import argparse
import copy
import unittest
from unittest.mock import patch

from scripts.lib.manifest_contract import validate_manifest, ManifestError, strategy_fingerprint


class ManifestContractTests(unittest.TestCase):
    def setUp(self):
        self.strategy = {'domain': 'example.org', 'api': {'taxonomy': {'list_pages': {'Tools': 'Tools'}}}}
        self.page = {'title': 'Tools', 'ns': 0, 'target_directory': 'Tools', 'target_filename': 'Tools.md'}

    def test_legacy_adaptation_does_not_mutate(self):
        original = {'pages': [self.page], 'list_page_content': {'Absent': 'body'}}
        before = copy.deepcopy(original)
        adapted = validate_manifest(original, self.strategy)
        self.assertEqual(original, before)
        self.assertTrue(adapted['pages'][0]['is_list_page'])
        self.assertEqual(adapted['list_page_decisions']['Absent']['reason'], 'absent_from_manifest')

    def test_invalid_versions_and_ambiguity(self):
        for manifest in [{'schema_version': 3, 'pages': [self.page]},
                         {'pages': [dict(self.page, target_directory='Other')]},
                         {'pages': [{'title': 'Missing'}]}]:
            with self.subTest(manifest=manifest), self.assertRaises(ManifestError):
                validate_manifest(manifest, self.strategy)

    def test_v2_checks_identity_and_required_fields(self):
        valid = {'schema_version': 2, 'domain': 'example.org',
                 'strategy_fingerprint': strategy_fingerprint(self.strategy),
                 'pages': [dict(self.page, is_list_page=True)], 'list_page_decisions': {}}
        self.assertTrue(validate_manifest(valid, self.strategy)['pages'][0]['is_list_page'])
        for key, value in [('domain', 'other.org'), ('strategy_fingerprint', 'bad')]:
            with self.assertRaises(ManifestError):
                validate_manifest(dict(valid, **{key: value}), self.strategy)
        self.assertEqual(strategy_fingerprint(self.strategy), strategy_fingerprint(dict(self.strategy, description='changed')))

    def test_preserve_legacy_root_and_reject_path_escape(self):
        page = dict(self.page, title='Other', target_directory='')
        self.assertEqual(validate_manifest({'pages': [page]}, self.strategy)['pages'][0]['target_directory'], '')
        with self.assertRaises(ManifestError):
            validate_manifest({'pages': [dict(page, target_directory='../escape')]}, self.strategy)

    def test_pipeline_rejects_discover_before_strategy_or_network(self):
        from scripts.pipeline.pipeline.orchestrator import run_pipeline
        with patch('scripts.pipeline.pipeline.orchestrator.parse_strategy') as parse:
            self.assertEqual(run_pipeline(argparse.Namespace(phase=['discover'])), 20)
            parse.assert_not_called()


if __name__ == '__main__':
    unittest.main()
