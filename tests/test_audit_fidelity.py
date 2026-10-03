import unittest
from scripts.lib.extraction.converter import convert_page_full
from scripts.explore.self_check import s6_table_integrity, s5_text_integrity, build_source_context


class AuditFidelityTests(unittest.TestCase):
    def test_hyphen_data_and_headerless_table(self):
        for header in ('', '<tr><th>Name</th></tr>'):
            html = '<table>' + header + '<tr><td>A</td></tr><tr><td>B</td></tr><tr><td>-</td></tr></table>'
            md = convert_page_full(html, {})
            self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')
            self.assertEqual(s6_table_integrity(html, md.replace('| B |\n', '').replace('| - |', ''))['status'], 'fail')

    def test_source_identifier_is_note_and_extra_occurrence_fails(self):
        context = build_source_context('<p>Battle Config2fc</p>', {}, input_scope='content_fragment')
        result = s5_text_integrity('Battle Config2fc', context)
        self.assertEqual(result['status'], 'pass')
        self.assertTrue(result['notes'])
        self.assertEqual(s5_text_integrity('Battle Config2fc\n\nBattle Config2fc', context)['status'], 'fail')
        context = build_source_context('<p>version v2 alpha</p>', {}, input_scope='content_fragment')
        self.assertEqual(s5_text_integrity('version v2alpha', context)['status'], 'fail')
        self.assertEqual(s5_text_integrity('`Config2fc` [ok](relative/Config2fc.md)', context)['status'], 'pass')
        self.assertEqual(s5_text_integrity('Config2fc')['status'], 'skip')

    def test_bracketed_and_linked_images_are_counted(self):
        from scripts.explore.self_check import run_checks
        html = '<p><img src="https://e.test/a.png"><img src="https://e.test/b.png"></p>'
        md = '[![A](https://e.test/a.png) x5] and [![B](https://e.test/b.png)](https://e.test/page)'
        context = build_source_context(html, {}, input_scope='content_fragment')
        check = next(c for c in run_checks(html, md, '', set(), source_context=context) if c['check'] == 'S1')
        self.assertEqual(check['status'], 'pass', check)

    def test_source_line_breaks_inside_one_table_cell(self):
        html = '<table><tr><td>Chance<br>Chance to help</td></tr></table>'
        context = build_source_context(html, {}, input_scope='content_fragment')
        self.assertEqual(s5_text_integrity(convert_page_full(html, {}), context)['status'], 'pass')
        # Separate source cells do not grant a repetition budget in a single output cell.
        other = build_source_context('<table><tr><td>Chance</td><td>Chance to help</td></tr></table>', {}, input_scope='content_fragment')
        self.assertEqual(s5_text_integrity('| Chance Chance to help |', other)['status'], 'fail')
