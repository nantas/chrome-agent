"""Enumerate pages using an already frozen strategy; no site analysis."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scripts.lib.strategy_loader import parse_strategy
from scripts.lib.extraction.schema import require_valid_extraction
from scripts.lib.manifest_contract import validate_manifest, strategy_fingerprint
from scripts.lib.config_resolver import resolve_rate_limit_config, resolve_exclude_categories
from scripts.pipeline.client import ApiClient
from scripts.pipeline.pipeline.registry import build_pipeline
from scripts.explore.discovery_allpages import run_allpages_discovery
from scripts.explore.discovery_homepage import run_homepage_discovery


class ObservedClient:
    def __init__(self, client):
        self.client = client
        self.requests = 0
        self.failed = 0

    def __getattr__(self, name):
        value = getattr(self.client, name)
        if name not in {'query', 'parse'} or not callable(value):
            return value
        def call(*args, **kwargs):
            self.requests += 1
            try:
                result = value(*args, **kwargs)
                if isinstance(result, dict) and result.get('error'):
                    raise RuntimeError(str(result['error']))
                return result
            except Exception:
                self.failed += 1
                raise
        return call


def build_summary(manifest, elapsed):
    categories = {}
    for page in manifest['pages']:
        bucket = categories.setdefault(page['target_directory'], {'count': 0, 'index_kind': 'generated', 'index_page': None})
        bucket['count'] += 1
        if page.get('is_list_page'):
            bucket.update(index_kind='real', index_page=page['title'])
    outcomes = manifest.get('request_outcomes', {})
    count = outcomes.get('total', 0)
    return {'total_pages': len(manifest['pages']), 'categories': categories,
            'excluded': {'total': manifest.get('discovery_counts', {}).get('excluded'),
                         'unknown_reason': None if 'discovery_counts' in manifest else 'upstream did not report exclusions'},
            'failure_rate': outcomes.get('failed', 0) / count if count else None,
            'failure_rate_basis': 'observed API requests' if count else 'unknown: no observed API requests',
            'estimated_time': None, 'estimate_basis': 'unknown: no extraction timing measurement',
            'discovery_elapsed_seconds': elapsed, 'manifest_path': 'page_manifest.json',
            'list_page_decisions': manifest.get('list_page_decisions', {})}


def discover_pages(strategy, output, args, client=None):
    started = time.monotonic()
    require_valid_extraction(strategy.get('extraction', {}))
    strategies = build_pipeline(strategy, strategy['domain'])
    api = strategy['api']
    client = client or ApiClient(api['base_url'], rate_limit_config=resolve_rate_limit_config(strategy, args))
    client = ObservedClient(client)
    excludes = resolve_exclude_categories(strategy, args.exclude_category or [])
    origin = 'https://' + strategy['domain']
    if api.get('homepage'):
        manifest = run_homepage_discovery(client, strategy, origin, platform_variant=api.get('platform_variant', 'standard'), exclude_categories=excludes)
    else:
        manifest = run_allpages_discovery(client, strategy, origin, strategies.discovery, platform_variant=api.get('platform_variant', 'standard'), exclude_categories=excludes)
    lists = api.get('taxonomy', {}).get('list_pages', {})
    for page in manifest['pages']:
        page.setdefault('ns', 14 if page['title'].startswith('Category:') else 0)
        if page['ns'] == 0 and not page.get('target_directory'):
            page['target_directory'] = 'Misc'
        page['is_list_page'] = page.get('is_list_page', page['title'] in lists)
    if args.max_pages and args.max_pages > 0:
        manifest['pages'] = manifest['pages'][:args.max_pages]
    manifest.update(schema_version=2, domain=strategy['domain'], strategy_fingerprint=strategy_fingerprint(strategy))
    manifest['list_page_decisions'] = {}
    by_title = {p['title']: p for p in manifest['pages']}
    for title in set(lists) | set(manifest.get('list_page_content', {})):
        canonical = title if title in by_title else None
        candidates = [name for name in by_title if name.replace('_', ' ') == title.replace('_', ' ')]
        if canonical is None and len(candidates) == 1:
            canonical = candidates[0]
        reason = 'absent_from_manifest'
        if canonical is None and title in lists and hasattr(client.client, 'parse'):
            try:
                info = client.parse(page=title, prop='properties', redirects=True)
                resolved = info.get('parse', {}).get('title')
                canonical = resolved if resolved in by_title else None
                reason = 'outside_retained_scope' if resolved else 'identity_unresolved'
            except Exception:
                reason = 'identity_lookup_failed'
        eligible = canonical is not None and title in lists
        if eligible:
            by_title[canonical]['is_list_page'] = True
        manifest['list_page_decisions'][title] = {'eligible': eligible,
            'canonical_title': canonical, 'reason': 'included' if eligible else reason}
    manifest = validate_manifest(manifest, strategy)
    directory = Path(output); directory.mkdir(parents=True, exist_ok=True)
    manifest['request_outcomes'] = {'total': client.requests, 'failed': client.failed}
    summary = build_summary(manifest, time.monotonic() - started)
    state = 'failure' if not manifest['pages'] else ('partial_success' if client.failed else 'success')
    summary['result'] = state
    (directory / 'discovery_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    manifest_path = directory / 'page_manifest.json'
    if state != 'failure':
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    elif manifest_path.exists():
        manifest_path.unlink()
    return {'result': state, 'manifest_path': str(manifest_path) if state != 'failure' else None,
            'discovery_summary_path': str(directory / 'discovery_summary.json')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--exclude-category', action='append', default=[])
    parser.add_argument('--max-pages', type=int)
    parser.add_argument('--concurrency', type=int)
    args = parser.parse_args()
    try:
        result = discover_pages(parse_strategy(args.strategy), args.output, args)
        print(json.dumps(result))
        return {'success': 0, 'partial_success': 1, 'failure': 10}[result['result']]
    except Exception as error:
        print(json.dumps({'result': 'failure', 'error': str(error)}))
        return 14 if isinstance(error, ValueError) else 10


if __name__ == '__main__':
    raise SystemExit(main())
