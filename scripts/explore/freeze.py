"""freeze.py — finalize a strategy scaffold and write to registry."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml


def freeze(repo_root: str, scaffold_path: str) -> dict:
    """Validate before publishing; roll back both files on publication errors."""
    import tempfile
    from scripts.explore.strategy_lifecycle import validate_target
    from scripts.explore.capability_gate import check_requirements
    file = Path(scaffold_path)
    if not file.exists(): return {"ok": False, "error": "Scaffold not found"}
    original = file.read_bytes()
    content = original.decode()
    parts = content.split('---', 2)
    if len(parts) < 3: return {"ok": False, "error": "Missing YAML frontmatter"}
    strategy = yaml.safe_load(parts[1])
    registry_path = Path(repo_root) / 'sites/strategies/registry.json'
    previous = registry_path.read_bytes() if registry_path.exists() else None
    temp_paths = []
    try:
        capability_path = Path(repo_root) / 'configs/capability-registry.yaml'
        if capability_path.exists():
            gaps = check_requirements(strategy, yaml.safe_load(capability_path.read_text()))
            if gaps:
                gap_path = file.parent / "capability-gap.yaml"
                gap_path.write_text(yaml.safe_dump(gaps))
                return {"ok": False, "error": "Capability gaps", "gaps": gaps, "gap_path": str(gap_path)}
        draft = strategy.get('lifecycle', {}).get('status') == 'draft' or bool(re.search(r'Bootstrapped|Auto-generated scaffold|SCAPFOLD', content))
        validate_target(strategy, require_review=draft)
        strategy['lifecycle'] = {**strategy.get('lifecycle', {}), 'status': 'frozen'}
        strategy['lifecycle'].pop('pending_fields', None)
        body = re.sub(r'<!--[^>]*Bootstrapped.*?-->', '', parts[2], flags=re.S)
        final = '---\n' + yaml.safe_dump(strategy, sort_keys=False, allow_unicode=True) + '---' + body
        registry = json.loads(previous) if previous else {'entries': []}
        domain = strategy['domain']
        new_entry = {'domain': domain, 'description': strategy['description'],
            'protection_level': strategy.get('protection_level', 'low'),
            'page_types': sorted({p.get('type', 'article') for p in strategy['structure']['pages']}),
            'pagination': ['none'], 'entry_points': strategy['structure']['entry_points'],
            'anti_crawl_refs': strategy.get('anti_crawl_refs', []),
            'file': os.path.relpath(file, registry_path.parent),
            **({'backend': strategy['backend']} if strategy.get('backend') else {})}
        for index, entry in enumerate(registry['entries']):
            if entry.get('domain') == domain:
                ordered = {key: new_entry[key] for key in entry if key in new_entry}
                ordered.update(new_entry)
                registry['entries'][index] = ordered
                break
        else:
            registry['entries'].append(new_entry)
        previous_text = previous.decode('utf-8') if previous else ''
        indentation = re.search(r'\n([ \t]+)\"', previous_text)
        indent = indentation.group(1) if indentation else 4
        newline = '\n' if not previous or previous_text.endswith('\n') else ''
        registry_text = json.dumps(registry, ensure_ascii=False, indent=indent) + newline
        for target, data in [(file, final), (registry_path, registry_text)]:
            with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as temp:
                temp.write(data); temp_paths.append(temp.name)
        os.replace(temp_paths[0], file)
        os.replace(temp_paths[1], registry_path)
        return {'ok': True, 'status': 'frozen', 'domain': domain, 'strategy_path': str(file), 'registry_path': str(registry_path)}
    except Exception as error:
        file.write_bytes(original)
        if previous is not None: registry_path.write_bytes(previous)
        elif registry_path.exists(): registry_path.unlink()
        return {'ok': False, 'error': str(error)}
    finally:
        for temp in temp_paths:
            if os.path.exists(temp): os.unlink(temp)


def main():
    parser = argparse.ArgumentParser(description="Freeze a strategy scaffold")
    parser.add_argument("repo_root", help="Repository root path")
    parser.add_argument("scaffold_path", help="Path to strategy.md scaffold")
    args = parser.parse_args()

    result = freeze(args.repo_root, args.scaffold_path)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        # Exit 5 for capability gaps, 1 for other errors
        if result.get("gaps"):
            exit(5)
        exit(1)


if __name__ == "__main__":
    main()
