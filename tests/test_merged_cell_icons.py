"""Merged-cell projections preserve semantic labels without duplicating assets."""
import unittest

from scripts.lib.extraction.schema import require_valid_extraction
from scripts.lib.extraction.converter import convert_page_full
from scripts.explore.self_check import build_source_context, s5_text_integrity

LABELS = {'Dd2 token vulnerable.png': 'Vulnerable', 'Dd2 token daze.png': 'Daze'}
RULES = {'table_options': {'merged_cell_icon_labels': LABELS}}
CRYPT = '''<table><tr><th>Condition</th><th>Continuation</th></tr><tr><td colspan="2">
When Moving: Add <img src="/blind.png" alt="Blind"> (15%) or
<img src="/weak.png" alt="Weak"> (15%) or
<img src="/vulnerable.png" alt="Dd2 token vulnerable.png"> or
<img src="/daze.png" alt="Dd2 token daze.png"> (15%)
</td></tr></table>'''


class MergedCellIconTests(unittest.TestCase):
    def test_mapping_schema(self):
        for options in ({}, {'merged_cell_icon_labels': {}}, {'transpose_wider_than': 10, 'merged_cell_icon_labels': LABELS}):
            require_valid_extraction({'table_options': options})
        for bad in ([], None, {'': 'A'}, {'A': ''}, {'A': 1}, {' A': 'B'}, {'A': 'B '}, {'A': 'B\nC'}):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'table_options.merged_cell_icon_labels'):
                convert_page_full(CRYPT, {'table_options': {'merged_cell_icon_labels': bad}})
        with self.assertRaisesRegex(ValueError, 'table_options.unknown'):
            require_valid_extraction({'table_options': {'unknown': {}}})

    def test_crypt_keeper_colspan(self):
        context = build_source_context(CRYPT, {}, input_scope='content_fragment')
        md = convert_page_full(CRYPT, RULES)
        self.assertEqual(md.count('!['), 4)
        self.assertIn('| When Moving: Add Blind (15%) or Weak (15%) or Vulnerable or Daze (15%) |', md)
        self.assertEqual(s5_text_integrity(md, context)['status'], 'pass')

    def test_name_resolution(self):
        for attrs, expected in [
            ('alt=" Dd2 token vulnerable.png "', 'Vulnerable'),
            ('alt="Blind" title="Other"', 'Blind'),
            ('alt="x.PNG" title="Useful"', 'Useful'),
            ('alt="icon" title="Useful"', 'Useful'),
            ('alt="https://x.test/a" title="Useful"', 'Useful'),
            ('alt="dd2 token vulnerable.png"', '（未命名图标）'),
            ('alt="image"', '（未命名图标）'), ('', '（未命名图标）'),
        ]:
            html = '<table><tr><th>A</th><th>B</th></tr><tr><td colspan="2"><img src="/a.png" '+attrs+'></td></tr></table>'
            with self.subTest(attrs=attrs):
                md = convert_page_full(html, RULES)
                self.assertIn('| '+expected+' |', md)
                self.assertEqual(md.count('!['), 1)

    def test_link_labels_and_safe_text(self):
        html = '''<table><tr><th>A</th><th>B</th></tr><tr><td colspan="2">
        <a href="https://e.test/Blind"><img src="/b.png" alt="Blind"><b>Blind</b></a>
        <a href="https://e.test/Special"><img src="/s.png" alt="Special"></a>
        </td></tr></table>'''
        md = convert_page_full(html, {'table_options': {'merged_cell_icon_labels': {'Special': '[A]|*B*<C>&'}}})
        self.assertNotIn('Blind **Blind**', md)
        self.assertIn('[**Blind**](https://e.test/Blind)', md)
        self.assertIn('[&#91;A&#93;&#124;&#42;B&#42;&#60;C&#62;&#38;](https://e.test/Special)', md)
        self.assertEqual(md.count('!['), 2)

    def test_spans_filters_and_source_occurrences(self):
        html = '''<table><tr><th>A</th><th>B</th><th>C</th></tr>
        <tr><td colspan="2" rowspan="2">Gain <img src="/b.png" alt="Blind"></td><td>11</td></tr>
        <tr><td>22</td></tr><tr><td><img src="/b.png" alt="Blind"></td><td>33</td><td>44</td></tr>
        <tr><td colspan="2">Keep <img src="/skip.png" alt="Forbidden"></td><td>55</td></tr></table>'''
        rules = {'image_filtering': {'skip_patterns': ['skip.png']}}
        md = convert_page_full(html, rules)
        self.assertEqual(md.count('![Blind]'), 2)
        self.assertIn('| Gain Blind | Gain Blind | 22 |', md)
        self.assertIn('| Keep | Keep | 55 |', md)
        self.assertNotIn('Forbidden', md)
        self.assertIn('| 33 | 44 |', md)
        context = build_source_context('<p>Gain strength</p>', {}, input_scope='content_fragment')
        self.assertEqual(s5_text_integrity('Gain Gain strength', context)['status'], 'fail')

    def test_nested_header_transpose_and_plain_cells(self):
        html = '''<table><thead><tr><th rowspan="2"><img src="/b.png" alt="Blind"></th><th>X</th></tr>
        <tr><th>Y</th></tr></thead><tbody><tr><td colspan="2">Plain</td></tr>
        <tr><td colspan="2">Outer<img src="/w.png" alt="Weak"><table><tr><td>Inner</td><td>99</td></tr></table></td></tr></tbody></table>'''
        for options in ({}, {'transpose_wider_than': 1}):
            with self.subTest(options=options):
                md = convert_page_full(html, {'table_options': options})
                self.assertEqual(md.count('!['), 2)
                self.assertIn('Outer Weak', md)
                self.assertEqual(md.count('99'), 1)
                self.assertIn('Plain', md)

    def test_adjacent_exact_labels_preserve_links_and_boundaries(self):
        cases = [
            ('<img src="/a.png" alt="HP"> <a href="https://e.test/a">HP</a>', '[HP](https://e.test/a)'),
            ('<a href="https://e.test/a"><img src="/a.png" alt="Upgraded"></a> Upgraded', '[Upgraded](https://e.test/a)'),
            ('<a href="https://e.test/a"><img src="/a.png" alt="HP"></a> <a href="https://e.test/a">HP</a>', '[HP](https://e.test/a)'),
            ('<b>HP</b> <a href="https://e.test/a"><img src="/a.png" alt="HP"></a>', '[**HP**](https://e.test/a)'),
        ]
        for body, expected in cases:
            html = '<table><tr><th>A</th><th>B</th></tr><tr><td colspan="2">'+body+'</td></tr></table>'
            with self.subTest(body=body):
                md = convert_page_full(html, {})
                self.assertTrue(md.endswith('| '+expected+' |'), md)
        for body in [
            '<a href="https://e.test/a"><img src="/a.png" alt="HP"></a> or HP',
            '<a href="https://e.test/a"><img src="/a.png" alt="HP"></a><br>HP',
            '<a href="https://e.test/a"><img src="/a.png" alt="HP"></a><a href="https://e.test/b">HP</a>',
            '<a href="https://e.test/a"><img src="/a.png" alt="HP"><img src="/b.png" alt="HP"></a>',
        ]:
            html = '<table><tr><th>A</th><th>B</th></tr><tr><td colspan="2">'+body+'</td></tr></table>'
            with self.subTest(boundary=body):
                md = convert_page_full(html, {})
                self.assertIn('HP', md)
                self.assertIn('https://e.test/a', md)
                # Independent source labels/images must not be globally deduplicated.
                self.assertGreaterEqual(md.split(' | ')[-1].count('HP'), 2, md)
