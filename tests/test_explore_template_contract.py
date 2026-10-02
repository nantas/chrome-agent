"""Registered MediaWiki templates must produce executable draft configuration."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.explore.strategy_scaffold_generator import generate
from scripts.lib.strategy_loader import parse_strategy
from scripts.lib.extraction.schema import validate_extraction
from scripts.lib.extraction.preprocessor import preprocess_html

ROOT = Path(__file__).resolve().parents[1]
HTML = '<div id="mw-content-text"><p>KEEP</p><span class="mw-editsection">EDIT</span><div class="toc">TOC_CLASS</div><div id="toc">TOC_ID</div></div>'


class TemplateContractTests(unittest.TestCase):
    def assert_template(self, platform):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'sites/templates', root / 'sites/templates')
            (root / 'scripts').symlink_to(ROOT / 'scripts', target_is_directory=True)
            result = generate(directory, 'example.org', 'Fixture', platform, {}, {}, None)
            strategy = parse_strategy(result['path'])
            self.assertEqual(strategy['lifecycle']['status'], 'draft')
            self.assertIsNone(strategy['lifecycle']['review_evidence'])
            self.assertFalse((root / 'sites/strategies/registry.json').exists())
            rules = strategy['extraction']
            self.assertEqual(validate_extraction(rules), [])
            cleaned = preprocess_html(HTML, rules)
            self.assertIn('KEEP', cleaned)
            for unwanted in ['EDIT', 'TOC_CLASS', 'TOC_ID']:
                self.assertNotIn(unwanted, cleaned)
            if platform == 'mediawiki-wiki-gg':
                self.assertIn('.nav-box', rules['cleanup_selectors'])
                self.assertIn('.nav-header', rules['cleanup_selectors'])
                self.assertEqual(rules['image_filtering']['skip_patterns'], ['Font_TeamMeat', 'Dlc_.*indicator'])

    def test_wiki_gg_template(self):
        self.assert_template('mediawiki-wiki-gg')

    def test_registered_mediawiki_templates(self):
        registry = json.loads((ROOT / 'sites/templates/registry.json').read_text())
        for entry in registry['entries']:
            if entry['platform'].startswith('mediawiki'):
                with self.subTest(platform=entry['platform']):
                    self.assert_template(entry['platform'])

    def test_generic_template(self):
        self.assert_template('mediawiki')


if __name__ == '__main__':
    unittest.main()
