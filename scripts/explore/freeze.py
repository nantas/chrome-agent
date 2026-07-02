"""freeze.py — finalize a strategy scaffold and write to registry."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml


def freeze(repo_root: str, scaffold_path: str) -> dict:
    """Freeze a strategy scaffold.

    1. Remove scaffold marker
    2. Read frontmatter
    3. Append to registry.json
    4. Generate final report
    """
    if not os.path.exists(scaffold_path):
        return {"ok": False, "error": f"Scaffold not found: {scaffold_path}"}

    with open(scaffold_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Detect if this is a new scaffold (has scaffold marker) or a re-freeze
    is_new_scaffold = bool(
        re.search(r"^# (Auto-generated scaffold|SCAPFOLD)", content, re.M)
    )

    # Remove scaffold marker
    content = re.sub(r"^# Auto-generated scaffold — review recommended\n", "", content)
    content = re.sub(r"^# SCAPFOLD: auto-generated — review recommended\n", "", content)

    with open(scaffold_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Parse frontmatter
    match = re.search(r"^---\n(.*?)\n---", content, re.S)
    if not match:
        return {"ok": False, "error": "Missing YAML frontmatter"}

    frontmatter = yaml.safe_load(match.group(1))

    # Capability gate check: only for new scaffolds, not re-freezes
    if is_new_scaffold:
        from scripts.explore.capability_gate import check_requirements
        cap_registry_path = os.path.join(repo_root, "configs", "capability-registry.yaml")
        if os.path.exists(cap_registry_path):
            with open(cap_registry_path, "r", encoding="utf-8") as f:
                cap_registry = yaml.safe_load(f)
            gaps = check_requirements(frontmatter, cap_registry)
            if gaps:
                run_dir = os.path.dirname(scaffold_path)
                gap_path = os.path.join(run_dir, "capability-gap.yaml")
                with open(gap_path, "w", encoding="utf-8") as f:
                    yaml.dump(gaps, f, allow_unicode=True)
                return {
                    "ok": False,
                    "error": f"{len(gaps)} capability gap(s) found",
                    "gaps": gaps,
                    "gap_path": gap_path,
                }

    domain = frontmatter.get("domain", "")
    protection_level = frontmatter.get("protection_level", "low")
    page_types = []
    for page in frontmatter.get("structure", {}).get("pages", []):
        pt = page.get("type")
        if pt and pt not in page_types:
            page_types.append(pt)

    pagination = ["none"]
    entry_points = frontmatter.get("structure", {}).get("entry_points", [])
    anti_crawl_refs = frontmatter.get("anti_crawl_refs", [])

    # Append to registry
    registry_path = os.path.join(repo_root, "sites", "strategies", "registry.json")
    registry = {"entries": []}
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

    entries = registry.get("entries", [])
    # Remove existing entry for same domain
    entries = [e for e in entries if e.get("domain") != domain]

    rel_path = os.path.relpath(scaffold_path, os.path.join(repo_root, "sites", "strategies"))
    entries.append({
        "domain": domain,
        "description": frontmatter.get("description", ""),
        "protection_level": protection_level,
        "page_types": page_types,
        "pagination": pagination,
        "entry_points": entry_points,
        "anti_crawl_refs": anti_crawl_refs,
        "file": rel_path.replace("\\", "/"),
    })

    registry["entries"] = entries
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    # Generate final report
    report = {
        "domain": domain,
        "protection_level": protection_level,
        "page_types": page_types,
        "entry_points": entry_points,
        "anti_crawl_refs": anti_crawl_refs,
        "strategy_path": scaffold_path,
        "registry_path": registry_path,
        "status": "frozen",
    }

    report_path = os.path.join(os.path.dirname(scaffold_path), "freeze-report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return {
        "ok": True,
        "domain": domain,
        "strategy_path": scaffold_path,
        "registry_path": registry_path,
        "report_path": report_path,
    }


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
