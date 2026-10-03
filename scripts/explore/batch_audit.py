"""Offline source-aware audit of explicit local HTML/Markdown pairs."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.explore.self_check import build_source_context, run_checks, summarize, _markdown_links
from scripts.lib.extraction.schema import require_valid_extraction


def _resolve_links(markdown: str, page: dict, base: Path, mapping: dict) -> tuple:
    """Restore only declared local destinations; never infer page identities."""
    missing = []
    source = page.get('source_url', '')
    directory = (base / page['markdown_path']).resolve().parent
    for link in reversed(_markdown_links(markdown)):
        if link['image']:
            continue
        url = link['url']
        parsed = urlsplit(url)
        if parsed.scheme or url.startswith('//'):
            continue
        if url.startswith('#'):
            target = source
        else:
            target = mapping.get(str((directory / unquote(parsed.path)).resolve()))
        if target:
            replacement = target + ('#' + parsed.fragment if parsed.fragment else '')
            old = markdown[link['start']:link['end']]
            # URL is a suffix of the parsed link; labels may themselves contain links.
            ending = old.rfind('](')
            if ending >= 0:
                new = old[:ending + 2] + replacement.replace('(', '%28').replace(')', '%29') + ')'
                markdown = markdown[:link['start']] + new + markdown[link['end']:]
        else:
            missing.append(url)
    return markdown, sorted(set(missing))


def audit_manifest(manifest_path) -> dict:
    path = Path(manifest_path).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8'))
    rules = manifest.get('extraction', {})
    require_valid_extraction(rules)
    base = path.parent
    mapping = {str((base / key).resolve()): value for key, value in manifest.get('link_mapping', {}).items()}
    for page in manifest['pages']:
        if page.get('markdown_path') and page.get('source_url'):
            key = str((base / page['markdown_path']).resolve())
            if key in mapping and mapping[key] != page['source_url']:
                raise ValueError('conflicting page mapping: ' + key)
            mapping[key] = page['source_url']
    pages, seen = [], set()
    coverage = defaultdict(Counter)
    for page in manifest['pages']:
        identity = page.get('id') or page.get('source_url')
        result = {'id': identity, 'source_url': page.get('source_url'), 'html_path': page.get('html_path'),
                  'markdown_path': page.get('markdown_path'), 'input_scope': page.get('input_scope')}
        try:
            if not identity or identity in seen:
                raise ValueError('missing or duplicate page identity')
            seen.add(identity)
            if urlsplit(page.get('source_url', '')).scheme not in {'http', 'https'}:
                raise ValueError('source_url must be an absolute HTTP(S) URL')
            html = (base / page['html_path']).read_text(encoding='utf-8')
            markdown = (base / page['markdown_path']).read_text(encoding='utf-8')
            context = build_source_context(html, rules, input_scope=page.get('input_scope', ''), source_url=page.get('source_url', ''))
            comparable, unresolved = _resolve_links(markdown, page, base, mapping)
            checks = run_checks(html, comparable, '', set(), source_context=context)
            if unresolved:
                for check in checks:
                    if check['check'] in {'S2', 'S9', 'S11'} and check['status'] != 'fail':
                        check.update(status='skip', detail='Local link attribution unavailable', unresolved_links=unresolved)
            result.update(checks=checks, summary=summarize(checks), unresolved_links=unresolved)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result.update(error=f'{type(exc).__name__}: {exc}', checks=[], summary={'overall_pass': False})
        for check in result['checks']:
            coverage[check['check']][check['status']] += 1
        pages.append(result)
    errors = sum(bool(p.get('error')) for p in pages)
    failures = sum(not p['summary']['overall_pass'] for p in pages)
    return {'manifest': str(path), 'pages': pages, 'coverage': dict(coverage), 'input_errors': errors,
            'failed_pages': failures, 'overall_pass': bool(pages) and failures == 0,
            'complete_validation': bool(pages) and not errors and failures == 0 and not any(v['skip'] for v in coverage.values())}


def write_report(manifest_path, output_path, report: dict) -> None:
    path, output = Path(manifest_path).resolve(), Path(output_path).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8'))
    inputs = {path}
    for page in manifest['pages']:
        inputs.update((path.parent / page[key]).resolve() for key in ('html_path', 'markdown_path') if key in page)
    if output in inputs:
        raise ValueError('report output must not overwrite an input')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        report = audit_manifest(args.manifest)
        write_report(args.manifest, args.output, report)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'{exc}\n')
    print(json.dumps({key: report[key] for key in ('coverage', 'input_errors', 'failed_pages', 'overall_pass', 'complete_validation')}))
    return 0 if report['overall_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
