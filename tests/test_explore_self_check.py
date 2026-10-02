"""Compatibility coverage for the extraction-only remediation API."""
import unittest
from scripts.explore.self_check import auto_remediate
from scripts.lib.extraction.schema import validate_extraction

class TestAutoRemediate(unittest.TestCase):
    def test_supported_rules_preserved_and_admitted(self):
        result = auto_remediate({'cleanup': ['strip_edit_links']}, [
            {'fixable_type': 'image_wrapper'}, {'fixable_type': 'space_normalization'}])
        self.assertEqual(validate_extraction(result), [])
        self.assertEqual(result['cleanup'], ['strip_edit_links', 'unwrap_image_wrappers'])
        self.assertEqual(result['text_normalization'], ['fix_spaces'])

    def test_unsupported_does_not_invent_operations(self):
        for kind in ['base64_residue', 'relative_link', 'totally_unknown']:
            with self.subTest(kind=kind):
                self.assertEqual(auto_remediate({}, [{'fixable_type': kind}]), {})
