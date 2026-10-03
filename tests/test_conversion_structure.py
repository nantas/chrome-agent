"""Full conversion regressions for structural normalization."""
import unittest
from scripts.lib.extraction.converter import convert_page_full


class ConversionStructureTests(unittest.TestCase):
    def test_span_does_not_capture_following_blocks(self):
        for cls in ('ordinary', 'nowrap', 'tooltip'):
            with self.subTest(cls=cls):
                html = '<div><span class="%s"><img src="https://e.test/i.png"></span><h2>Skills</h2><table><tr><td>Power</td></tr></table></div>' % cls
                md = convert_page_full(html, {})
                self.assertIn('\n\n## Skills\n\n', md)
                self.assertEqual(md.count('i.png'), 1)
                self.assertIn('| Power |', md)

    def test_tooltip_merge_retains_distinct_links_and_nested_text(self):
        html = '<div><span class="tooltip"><span style="--tb-icon-size:20px"><a href="https://e.test/a"><img src="https://e.test/i.png"></a></span><a href="https://e.test/a"><span>Power</span></a></span><h2>Next</h2><a href="https://e.test/b"><img src="https://e.test/j.png"></a><a href="https://e.test/c">Other</a></div>'
        md = convert_page_full(html, {})
        self.assertEqual(md.count('https://e.test/a)'), 1)
        self.assertIn('Power', md)
        self.assertIn('\n\n## Next\n\n', md)
        self.assertIn('https://e.test/b)', md)
        self.assertIn('https://e.test/c)', md)

    def test_deep_wrapped_list_preserves_nested_numbering(self):
        html = '<ul>' + '<big>' * 5 + '<li>A<img src="https://e.test/a.png"><ol><li>Inner one</li><li>Inner two</li></ol></li><li>B</li>' + '</big>' * 5 + '</ul>'
        md = convert_page_full(html, {'cleanup': ['unwrap_list_item_wrappers']})
        self.assertIn('a.png', md)
        self.assertIn('  1. Inner one\n  2. Inner two', md)
        self.assertTrue(md.endswith('- B'), md)
        self.assertEqual(convert_page_full('<ul><big><li>A</li></big></ul>', {}), '')

    def test_empty_cleanup_keeps_anchor_and_media_evidence(self):
        from scripts.lib.extraction.preprocessor import preprocess_html
        html = '<p><a id="jump"></a></p><a name="legacy"></a><span><img src="https://e.test/a.png"></span><h2>Next</h2>'
        rules = {'cleanup': ['strip_empty_inline_tags', 'strip_empty_paragraphs']}
        cleaned = preprocess_html(html, rules)
        self.assertIn('id="jump"', cleaned)
        self.assertIn('name="legacy"', cleaned)
        md = convert_page_full(html, rules)
        self.assertIn('\n\n## Next', md)
        self.assertEqual(md.count('a.png'), 1)

    def test_hidden_only_heading_does_not_emit_empty_heading(self):
        from scripts.lib.extraction.converter import convert_html_to_markdown
        self.assertEqual(convert_html_to_markdown('<h3><span style="display:none">Hidden</span></h3>', ''), '')

    def test_citation_brackets_do_not_gain_inner_spaces(self):
        md = convert_page_full('<p><a href="#note"><span>[</span><span>1</span><span>]</span></a></p>', {})
        self.assertEqual(md, '[[1]](#note)')
