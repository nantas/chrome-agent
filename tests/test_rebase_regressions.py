import unittest

from scripts.explore.self_check import s6_table_integrity
from scripts.lib.extraction.infobox import extract_infobox


class RebaseRegressionTests(unittest.TestCase):
    def test_portable_infobox_lead_image(self):
        html = '<aside class="portable-infobox"><figure class="pi-item pi-image"><img src="/hero.png" alt="Hero"></figure></aside>'
        result = extract_infobox(html, {}, 'example.org')
        self.assertIn('| Image | ![Hero](https://example.org/hero.png) |', result)
        filtered = extract_infobox(html, {'image_filtering': {'skip_patterns': ['hero']}}, 'example.org')
        self.assertNotIn('hero.png', filtered)

    def test_synthetic_infobox_does_not_inflate_body_rows(self):
        html = '<table><tr><th>Name</th></tr><tr><td>A</td></tr><tr><td>B</td></tr></table>'
        md = '## Infobox\n\n| Field | Value |\n| --- | --- |\n| Image | Hero |\n\n## Body\n\n| Name |\n| --- |\n| A |\n| B |'
        self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')
