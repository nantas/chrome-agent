"""Extraction schema and authoritative cleanup registry validation."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
import yaml


@lru_cache(maxsize=1)
def cleanup_operations():
    root = Path(__file__).resolve().parents[3]
    registry = yaml.safe_load((root / 'configs/capability-registry.yaml').read_text())
    return {op['name']: op['implemented_in'] for op in registry['convert']['cleanup_ops']}


def operation_registry_errors():
    root = Path(__file__).resolve().parents[3]
    errors = []
    for name, module in cleanup_operations().items():
        source = (root / module).read_text()
        if not re.search(r'[\"\']' + re.escape(name) + r'[\"\']\s+in\s+cleanup', source):
            errors.append({'field_path': 'cleanup.' + name, 'expected': 'implemented operation', 'value': module})
    return errors


def validate_extraction(config):
    errors = []
    def fail(path, value, expected):
        errors.append({'field_path': 'extraction.' + path, 'observed_type': type(value).__name__, 'value': value, 'expected': expected})
    if not isinstance(config, dict):
        fail('', config, 'map'); return errors
    # Additional platform-specific keys remain owned by their consumers/Gate;
    # only governed fields are shape checked here.
    fields = {'heading_normalization','cleanup','cleanup_selectors','image_filtering','image_handling','infobox','infobox_field_handlers','lazyload','selectors','table_options','text_normalization','url_conversion','youtube_cleanup','engine'}
    for key in config:
        if key not in fields and key != 'pipeline': fail(key, config[key], 'supported extraction field')
    if 'pipeline' in config:
        fail('pipeline', config['pipeline'], 'remove obsolete descriptive pipeline field')
    for key, names in [('cleanup', cleanup_operations()), ('text_normalization', {'fix_spaces','normalize_blank_lines','deduplicate_words'})]:
        value = config.get(key, [])
        if not isinstance(value, list):
            fail(key, value, 'list[str]'); continue
        for index, name in enumerate(value):
            if not isinstance(name, str) or name not in names:
                fail(f'{key}[{index}]', name, 'supported operation name')
    heading_rules = config.get('heading_normalization', [])
    if not isinstance(heading_rules, list):
        fail('heading_normalization', heading_rules, 'list[map]')
    else:
        import soupsieve
        for index, rule in enumerate(heading_rules):
            path = f'heading_normalization[{index}]'
            if not isinstance(rule, dict):
                fail(path, rule, 'map'); continue
            keys = {'heading_selector', 'label_selector'}
            for key in rule.keys() - keys - {'label_aliases'}:
                fail(path + '.' + key, rule[key], 'supported field')
            aliases = rule.get('label_aliases', {})
            if not isinstance(aliases, dict) or not all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip() for k, v in aliases.items()):
                fail(path + '.label_aliases', aliases, 'map of nonempty exact source-to-visible labels')
            for key in keys:
                value = rule.get(key)
                if not isinstance(value, str) or not value.strip():
                    fail(path + '.' + key, value, 'nonempty CSS selector'); continue
                try:
                    soupsieve.compile(value)
                except soupsieve.SelectorSyntaxError:
                    fail(path + '.' + key, value, 'valid CSS selector')
    maps = {'lazyload': {'enabled','placeholder_pattern','real_src_attr'},
            'url_conversion': {'enabled'}, 'youtube_cleanup': {'enabled'},
            'image_filtering': {'skip_patterns'}, 'table_options': {'transpose_wider_than'}}
    for key, names in maps.items():
        if key not in config: continue
        value = config[key]
        if not isinstance(value, dict):
            fail(key, value, 'map'); continue
        for name, item in value.items():
            if name not in names: fail(key + '.' + name, item, 'supported field')
        if key == 'lazyload' and value.get('enabled'):
            for name in ('placeholder_pattern','real_src_attr'):
                if not isinstance(value.get(name), str) or not value[name]:
                    fail(key + '.' + name, value.get(name), 'nonempty string when enabled')
    for key in ('selectors','image_handling','infobox','infobox_field_handlers'):
        if key in config and not isinstance(config[key], dict): fail(key, config[key], 'map')
    for key in ('cleanup_selectors',):
        if key in config and (not isinstance(config[key],list) or not all(isinstance(v,str) for v in config[key])):
            fail(key, config[key], 'list[str]')
    return errors


def require_valid_extraction(config):
    errors = validate_extraction(config)
    if errors:
        raise ValueError('extraction_schema: ' + str(errors))
