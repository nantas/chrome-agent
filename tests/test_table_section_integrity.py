"""Merged-cell assets and table section regression coverage."""
import unittest
from scripts.lib.extraction.converter import HtmlToMarkdownConverter
from scripts.explore.self_check import s1_image_retention, s5_text_integrity, s8_section_completeness, s6_table_integrity
from scripts.lib.test_assertions import assert_no_raw_html_tags

class TestTableSectionIntegrity(unittest.TestCase):
    def test_multirow_headers_form_one_valid_markdown_header(self):
        html = '<table><tr><th colspan="2">Combat</th></tr><tr><th>Accuracy<img src="https://example.org/accuracy.png"></th><th>Damage</th></tr><tr><td>95</td><td>8</td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertIn('Combat → Accuracy', md)
        self.assertEqual(md.count('accuracy.png'), 1)
        self.assertIn('| 95 | 8 |', md)
        self.assertIn('---', md.splitlines()[1])
        self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')

    def test_text_integrity_does_not_scan_url_hashes_as_versions(self):
        self.assertEqual(s5_text_integrity('[Sound](https://example.org/voice.wav?a1b2)')['status'], 'pass')
        self.assertEqual(s5_text_integrity('version v2alpha')['status'], 'fail')

    def test_heading_check_reads_linked_heading_as_rendered_text(self):
        html = '<h3><span class="mw-headline">The <a href="https://example.org/hero">Shieldbreaker</a></span></h3>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(s8_section_completeness(html, md)['status'], 'pass')
        self.assertEqual(s8_section_completeness(html, '### A different hero')['status'], 'fail')

    def test_heading_check_does_not_add_spaces_before_punctuation(self):
        html = '<h3><span class="mw-headline"><a href="https://example.org/a">Stress</a>, <a href="https://example.org/b">Virtues</a></span></h3>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(s8_section_completeness(html, md)['status'], 'pass')

    def test_row_check_ignores_empty_and_nested_container_rows(self):
        html = '<table><tr><td><table><tr><th>Rank</th></tr><tr><td>2</td></tr><tr><td>3</td></tr></table></td></tr><tr><td></td></tr><tr><td></td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')
        self.assertEqual(s6_table_integrity(html, '| Rank |\n| --- |')['status'], 'fail')

    def test_literal_angle_bracket_placeholder_is_not_html(self):
        md = HtmlToMarkdownConverter('').convert_body('<p>steam/userdata/&lt;a number&gt;/remote</p>')
        self.assertIn(r'steam/userdata/\<a number\>/remote', md)
        assert_no_raw_html_tags(md)
        with self.assertRaises(AssertionError):
            assert_no_raw_html_tags('<a number>')

    def test_rich_preformatted_warning_keeps_assets_and_links(self):
        html = '<pre><img src="https://example.org/warning.png"><b>WARNING</b> See <a href="https://example.org/boss">boss</a>.</pre>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(md.count('warning.png'), 1)
        self.assertIn('[boss](https://example.org/boss)', md)
        self.assertFalse(md.startswith('```'))
        self.assertIn('```\nprint(1)\n```', HtmlToMarkdownConverter('').convert_body('<pre>print(1)</pre>'))

    def test_promoted_heading_cell_keeps_its_nested_legend(self):
        html = '<table><tr><td><h3><span class="mw-headline">Legend</span></h3><table><tr><th>Symbol<img src="https://example.org/status.png"></th><th>Meaning</th></tr><tr><td>!</td><td>Danger</td></tr></table></td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(md.count('status.png'), 1)
        self.assertIn('| ! | Danger |', md)
        self.assertLess(md.index('Legend'), md.index('Symbol'))

    def test_table_caption_retains_image_and_link(self):
        html = '<table><caption><img src="https://example.org/quest.png">Gather <a href="https://example.org/quest">quest</a></caption><tr><th>Amount</th></tr><tr><td>3</td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(md.count('quest.png'), 1)
        self.assertIn('[quest](https://example.org/quest)', md)
        self.assertLess(md.index('Gather'), md.index('Amount'))

    def test_browser_table_row_groups_keep_headers_and_footer(self):
        html = '<table><thead><tr><th>Resistance<img src="https://example.org/icon.png"></th></tr></thead><tbody><tr><td>40%</td></tr></tbody><tfoot><tr><td>Note</td></tr></tfoot></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertIn('Resistance', md)
        self.assertEqual(md.count('icon.png'), 1)
        self.assertIn('40%', md)
        self.assertIn('Note', md)

    def test_merged_cell_image_occurs_once_but_labels_repeat(self):
        html = '<table><tr><th colspan="2">Group<img src="https://example.org/icon.png"></th></tr><tr><td rowspan="2">Label<img src="https://example.org/label.png"></td><td>1</td></tr><tr><td>2</td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(md.count('icon.png'), 1)
        self.assertEqual(md.count('label.png'), 1)
        self.assertEqual(md.count('Label'), 2)
        self.assertEqual(s1_image_retention(html, md)['status'], 'pass')

    def test_section_rows_become_headings_in_source_order(self):
        html = '<table><tr><th colspan="2"><h6><span class="mw-headline">Skill A</span></h6></th></tr><tr><th>Level</th><th>Damage</th></tr><tr><td>1</td><td>5</td></tr><tr><th colspan="2"><h6><span class="mw-headline">Skill B</span></h6></th></tr><tr><td>2</td><td>8</td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertIn('\n###### Skill B\n', md)
        self.assertTrue(md.startswith('###### Skill A'))
        self.assertLess(md.index('Skill A'), md.index('| 1 | 5 |'))
        self.assertLess(md.index('| 1 | 5 |'), md.index('Skill B'))
        self.assertEqual(s8_section_completeness(html, md)['status'], 'pass')

    def test_plain_english_is_not_repeated_text(self):
        for text in ['with the hero', 'This is fine', 'when entering', 'other heroes']:
            with self.subTest(text=text):
                self.assertEqual(s5_text_integrity(text)['status'], 'pass')

    def test_true_word_and_phrase_repetition_still_detected(self):
        for text in ['hero hero', 'combat skill combat skill']:
            with self.subTest(text=text):
                from scripts.explore.self_check import build_source_context
                context = build_source_context('<p>hero combat skill</p>', {}, input_scope='content_fragment')
                self.assertEqual(s5_text_integrity(text, context)['status'], 'fail')

    def test_nested_skill_levels_retained_as_separate_tables(self):
        html = '<table><tr><th><h6><span class="mw-headline">Skill</span></h6></th></tr><tr><td>Level 1<div><table><tr><th>Further levels</th><th>Value</th></tr><tr><td>Level 2</td><td>+3%</td></tr><tr><td>Level 5</td><td>+5%</td></tr></table></div></td></tr></table>'
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(md.count('Level 5'), 1)
        self.assertIn('| Level 5 | +5% |', md)
        self.assertNotIn('| Level 1|', md)
        self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')

    def test_nested_collapsible_data_loss_is_detected(self):
        html = '<table><tr><td>Skill<table class="mw-collapsible"><tr><th>Rank</th></tr><tr><td>2</td></tr><tr><td>3</td></tr><tr><td>4</td></tr></table></td></tr></table>'
        self.assertEqual(s6_table_integrity(html, '| |\n| --- |\n| Skill |')['status'], 'fail')
        md = HtmlToMarkdownConverter('').convert_body(html)
        self.assertEqual(s6_table_integrity(html, md)['status'], 'pass')
