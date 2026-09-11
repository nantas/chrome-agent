"""Page manifest validation shared by discovery and extraction boundaries."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import PurePosixPath


class ManifestError(ValueError):
    def __init__(self, field_path, reason):
        self.field_path = field_path
        self.reason = reason
        super().__init__(f'{field_path}: {reason}')


def strategy_fingerprint(strategy):
    semantic = {key: strategy.get(key) for key in ('domain', 'api', 'extraction', 'structure')}
    return hashlib.sha256(json.dumps(semantic, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _valid_path(value, field, filename=False):
    if not isinstance(value, str) or (filename and not value):
        raise ManifestError(field, 'expected target path string')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value or (filename and len(path.parts) != 1):
        raise ManifestError(field, 'unsafe target path')


def validate_manifest(manifest, strategy):
    """Validate and adapt a copy; never change membership or target paths."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get('pages'), list):
        raise ManifestError('pages', 'expected list')
    version = manifest.get('schema_version')
    if 'schema_version' in manifest and version != 2:
        raise ManifestError('schema_version', 'unsupported version; expected 2 or absent legacy version')
    if version == 2:
        if manifest.get('domain') != strategy.get('domain'):
            raise ManifestError('domain', 'does not match strategy')
        if manifest.get('strategy_fingerprint') != strategy_fingerprint(strategy):
            raise ManifestError('strategy_fingerprint', 'strategy changed; review scope before regenerating manifest')
        if not isinstance(manifest.get('list_page_decisions'), dict):
            raise ManifestError('list_page_decisions', 'expected map')
    elif manifest.get('domain') and manifest['domain'] != strategy.get('domain'):
        raise ManifestError('domain', 'does not match strategy')
    result = copy.deepcopy(manifest)
    lists = strategy.get('api', {}).get('taxonomy', {}).get('list_pages', {})
    decisions = result.setdefault('list_page_decisions', {})
    titles, paths = set(), set()
    for index, page in enumerate(result['pages']):
        field = f'pages[{index}]'
        if not isinstance(page, dict) or not isinstance(page.get('title'), str) or not page['title']:
            raise ManifestError(field + '.title', 'expected non-empty string')
        if not isinstance(page.get('ns'), int) or isinstance(page['ns'], bool):
            raise ManifestError(field + '.ns', 'expected namespace integer')
        for key in ('target_directory', 'target_filename'):
            _valid_path(page.get(key), field + '.' + key, key == 'target_filename')
        target = (page['target_directory'], page['target_filename'])
        if page['title'] in titles or target in paths:
            raise ManifestError(field, 'duplicate identity or target path')
        titles.add(page['title']); paths.add(target)
        if version == 2:
            if not isinstance(page.get('is_list_page'), bool):
                raise ManifestError(field + '.is_list_page', 'expected explicit boolean')
        elif 'is_list_page' not in page:
            title = page['title']
            aliases = [key for key in lists if key.replace('_', ' ') == title.replace('_', ' ')]
            if aliases and (title not in lists or lists[title] != page['target_directory']):
                raise ManifestError(field + '.is_list_page', 'ambiguous legacy list identity/directory')
            page['is_list_page'] = title in lists
        elif not isinstance(page['is_list_page'], bool):
            raise ManifestError(field + '.is_list_page', 'expected boolean')
    for title in set(lists) | set(result.get('list_page_content', {})):
        if title not in titles and not (decisions.get(title, {}).get('eligible') and decisions[title].get('canonical_title') in titles):
            decisions.setdefault(title, {'eligible': False, 'reason': 'absent_from_manifest'})
    if version is None:
        result['compatibility'] = {'mode': 'legacy_in_memory', 'source_unchanged': True}
    return result
