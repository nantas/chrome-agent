"""Feedback admission happens before file mutation or conversion."""
import os
import subprocess
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml
from scripts.lib.strategy_loader import parse_strategy
from scripts.lib.extraction.preprocessor import preprocess_html

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/explore'))
iterate_module = importlib.import_module('iterate')

class IterateTests(unittest.TestCase):
    def test_external_entry_without_pythonpath(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env.pop('PYTHONPATH', None)
            result = subprocess.run([sys.executable, iterate_module.__file__, '--help'], cwd=directory,
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def run_feedback(self, rules, feedback, mediawiki=True):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'strategy.md'
            frontmatter = {'domain': 'example.org', 'api': {'platform': 'mediawiki' if mediawiki else 'static-site'}, 'identity': 'preserve', 'extraction': rules}
            path.write_text('---\n' + yaml.safe_dump(frontmatter) + '---\nBODY\\1\n')
            original = path.read_bytes()
            with patch.object(iterate_module, 'convert', return_value=[]) as convert:
                result = iterate_module.iterate(directory, str(path), feedback, [], 'offline', directory)
            return result, path.read_bytes(), original, convert.call_count, parse_strategy(str(path))

    def test_edit_toc_real_consumer_roundtrip(self):
        result, actual, original, count, strategy = self.run_feedback({}, 'edit toc image space')
        self.assertTrue(result['ok'])
        self.assertEqual(count, 1)
        self.assertEqual(strategy['identity'], 'preserve')
        self.assertIn(b'BODY\\1', actual)
        cleaned = preprocess_html('<p>KEEP</p><span class="mw-editsection">EDIT</span><div id="toc">TOC</div>', strategy['extraction'])
        self.assertIn('KEEP', cleaned)
        self.assertNotIn('EDIT', cleaned)
        self.assertNotIn('TOC', cleaned)
        from scripts.lib.extraction.converter import apply_post_conversion_ops
        self.assertEqual(apply_post_conversion_ops('word2word', strategy['extraction']), 'word 2 word')
        cleaned = preprocess_html('<a href="file"><img src="https://example.org/a.png"></a>', strategy['extraction'])
        self.assertNotIn('<a ', cleaned)
        self.assertIn('<img', cleaned)

    def test_invalid_existing_config_preserves_bytes(self):
        result, actual, original, count, _ = self.run_feedback({'cleanup': ['strip_toc']}, 'image')
        self.assertFalse(result['ok'])
        self.assertEqual(actual, original)
        self.assertEqual(count, 0)
        self.assertEqual(result['errors'][0]['field_path'], 'extraction.cleanup[0]')

    def test_invalid_candidate_preserves_bytes(self):
        candidate = {'extraction': {'cleanup': ['invented']}, 'changed': True, 'applied': [], 'unresolved': []}
        with patch.object(iterate_module, 'plan_remediation', return_value=candidate, create=True):
            result, actual, original, count, _ = self.run_feedback({}, 'image')
        self.assertFalse(result['ok'])
        self.assertEqual(actual, original)
        self.assertEqual(count, 0)

    def test_image_partial_and_static_boundary(self):
        result, _, _, _, strategy = self.run_feedback({}, 'image')
        self.assertEqual(strategy['extraction']['cleanup'], ['unwrap_image_wrappers'])
        self.assertEqual(result['remediation']['unresolved'][0]['reason_code'], 'missing_evidence')
        result, _, _, _, strategy = self.run_feedback({'cleanup': ['descriptive_rule']}, 'toc', False)
        self.assertTrue(result['ok'])
        self.assertIn('descriptive_rule', strategy['extraction']['cleanup'])
