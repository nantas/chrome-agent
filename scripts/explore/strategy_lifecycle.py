"""Draft generation and production strategy validation."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from urllib.parse import urlparse
import yaml

from scripts.lib.extraction.schema import require_valid_extraction
from scripts.lib.strategy_loader import parse_strategy


def bootstrap_draft(source, url, profile=None):
    require_valid_extraction(source.get('extraction', {}))
    domain = urlparse(url).hostname
    if not domain: raise ValueError('Target hostname is required')
    draft = {key: copy.deepcopy(source[key]) for key in ('protection_level','engine_preference','anti_crawl_refs') if key in source}
    draft.update(domain=domain, description=f'Draft strategy for {domain}',
                 structure={'pages': [], 'entry_points': []},
                 lifecycle={'status':'draft','source_domain':source.get('domain'),
                            'pending_fields':['description','structure.pages','structure.entry_points','api.taxonomy'], 'review_evidence':None})
    api = source.get('api', {})
    draft['api'] = {key: copy.deepcopy(api[key]) for key in ('platform','platform_variant','content_profile','rate_limit') if key in api}
    draft['api']['base_url'] = f'https://{domain}/api.php'
    # Selectors/handlers are site-specific; use the schema-valid platform template.
    template = Path(__file__).resolve().parents[2] / 'sites/templates/mediawiki-fandom.yaml'
    extraction = parse_strategy(str(template)).get('extraction', {}) if api.get('platform_variant') == 'fandom' else {}
    draft['extraction'] = copy.deepcopy(extraction)
    draft['extraction'].setdefault('image_handling', {})['base_url'] = f'https://{domain}'
    if profile: draft['extraction']['cleanup'] = [profile]
    require_valid_extraction(draft['extraction'])
    return draft


def validate_target(strategy, require_review=False):
    if strategy.get('api', {}).get('platform') == 'mediawiki':
        require_valid_extraction(strategy.get('extraction', {}))
    domain = strategy.get('domain')
    if not domain or not strategy.get('description'): raise ValueError('Target domain and description are required')
    structure = strategy.get('structure', {})
    pages = structure.get('pages', [])
    entries = structure.get('entry_points', [])
    ids = {p.get('id') for p in pages}
    if not pages or not entries or any(e not in ids for e in entries):
        raise ValueError('Valid target structure.pages and entry_points are required')
    for page in pages:
        if page.get('url_example') and urlparse(page['url_example']).hostname != domain:
            raise ValueError('structure.pages.url_example must match target domain')
    for value in (strategy.get('api', {}).get('base_url'), strategy.get('extraction', {}).get('image_handling', {}).get('base_url')):
        if value and urlparse(value).hostname != domain:
            raise ValueError('API/image base_url must match target domain')
    if require_review and not strategy.get('lifecycle', {}).get('review_evidence'):
        raise ValueError('lifecycle.review_evidence is required before freezing a draft')
    if strategy.get('api', {}).get('platform') == 'mediawiki':
        from scripts.pipeline.pipeline.registry import build_pipeline
        build_pipeline(strategy, domain)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action', choices=['bootstrap','validate'])
    parser.add_argument('--source',required=True)
    parser.add_argument('--url')
    parser.add_argument('--profile')
    parser.add_argument('--output')
    args=parser.parse_args()
    try:
        strategy=parse_strategy(args.source)
        if args.action == 'validate':
            validate_target(strategy)
            result={'ok':True}
        else:
            draft=bootstrap_draft(strategy,args.url,args.profile)
            file=Path(args.output)
            if file.exists():raise ValueError('Target strategy file already exists')
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text('---\n'+yaml.safe_dump(draft,sort_keys=False,allow_unicode=True)+'---\n\n<!-- Bootstrapped draft; validate target fields before freeze -->\n\n## Overview\n\nGenerated platform defaults; target identity requires review.\n\n## Page Structure\n\nSee lifecycle.pending_fields.\n\n## Extraction Flow\n\nPlatform template defaults.\n\n## Known Issues\n\nNot production eligible.\n\n## Evidence\n\nReview evidence must be recorded before freeze.\n')
            result={'ok':True,'status':'draft','pending_fields':draft['lifecycle']['pending_fields']}
        print(json.dumps(result));return 0
    except Exception as error:
        print(json.dumps({'ok':False,'error':str(error)}));return 14


if __name__=='__main__':raise SystemExit(main())
