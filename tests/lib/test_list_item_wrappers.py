"""unwrap_list_item_wrappers / strip_empty_inline_tags：列表解包与空 inline 清理回归。

现场 1（Shambler DD2）：<ul><big><li>+100 <span class="nowrap"><img/></span>…</li></big></ul>
  markdownify 丢弃非直接子节点的 li，导致 4 张奖励图标整块丢失。
现场 2（Fallen Templar）：块级内容前的空 <a>/<span> 打断换行，h2 与表格首行粘连。
"""
import unittest

from scripts.lib.extraction.preprocessor import _apply_cleanup_ops
from bs4 import BeautifulSoup


def preprocess(html: str, ops=None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _apply_cleanup_ops(soup, ops or ["unwrap_list_item_wrappers"])
    return str(soup)


class TestUnwrapListItemWrappers(unittest.TestCase):
    def test_big_wrapped_li_is_unwrapped(self):
        html = '<ul><big><li>+100 <span class="nowrap"><img src="/x.png"/></span> Flame</li></big></ul>'
        out = preprocess(html)
        soup = BeautifulSoup(out, "html.parser")
        self.assertEqual(len(soup.select("ul > li")), 1)
        self.assertIsNotNone(soup.select_one("ul > li img"))
        self.assertNotIn("<big>", out)

    def test_nested_wrappers_unwrapped(self):
        html = '<ul><div><span><li>a</li></span></div></ul>'
        out = preprocess(html)
        soup = BeautifulSoup(out, "html.parser")
        self.assertEqual(len(soup.select("ul > li")), 1)

    def test_plain_list_untouched(self):
        html = "<ul><li>a</li><li>b</li></ul>"
        self.assertEqual(preprocess(html), html)

    def test_wrapper_without_li_untouched(self):
        # 包裹元素不含 li 时不解包（普通 inline 内容保持原样）
        html = '<ul><li><span class="nowrap">x</span> y</li></ul>'
        self.assertEqual(preprocess(html), html)


class TestStripEmptyInlineTags(unittest.TestCase):
    OPS = ["strip_empty_inline_tags"]

    def test_empty_span_a_removed(self):
        html = '<div><a id="x"></a><img src="/i.png"/><span></span><p>intro</p></div>'
        out = preprocess(html, self.OPS)
        self.assertNotIn("<span>", out)
        self.assertIn("<a id=\"x\"></a>", out)
        self.assertIn("<img", out)

    def test_text_span_kept(self):
        html = '<p><span class="buff-dd2">+4</span> Speed</p>'
        self.assertEqual(preprocess(html, self.OPS), html)

    def test_img_span_kept(self):
        html = '<p><span class="nowrap"><img src="/i.png"/></span> x</p>'
        self.assertEqual(preprocess(html, self.OPS), html)

    def test_block_fallthrough_fixed(self):
        # 块级换行修复（Fallen Templar 粘连现场的结构验证）
        html = '<div><img src="/i.png"/><span></span><p>intro</p><h2>Skills</h2></div>'
        out = preprocess(html, self.OPS)
        self.assertNotIn("<span>", out)
        self.assertIn("<h2>Skills</h2>", out)


class TestStripEmptyParagraphs(unittest.TestCase):
    OPS = ["strip_empty_paragraphs"]

    def test_br_only_paragraph_removed(self):
        html = '<p>text</p><p><br/></p><h2>Skills</h2>'
        out = preprocess(html, self.OPS)
        self.assertNotIn('<p><br/></p>', out)

    def test_text_paragraph_kept(self):
        html = '<p>real text</p>'
        self.assertEqual(preprocess(html, self.OPS), html)

    def test_img_paragraph_kept(self):
        html = '<p><img src="/i.png"/></p>'
        self.assertEqual(preprocess(html, self.OPS), html)


class TestUnwrapNowrapSpans(unittest.TestCase):
    OPS = ["unwrap_nowrap_spans"]

    def test_nowrap_span_unwrapped(self):
        html = '<p><span class="nowrap"><img src="/d.png"/> <a href="/x">X</a></span></p>'
        out = preprocess(html, self.OPS)
        self.assertNotIn("nowrap", out)
        self.assertIn('<img src="/d.png"/>', out)

    def test_other_span_kept(self):
        html = '<p><span class="buff-dd2">+4</span> Speed</p>'
        self.assertEqual(preprocess(html, self.OPS), html)

    def test_block_fallthrough_released(self):
        # span.nowrap>img 后接块级元素：解包后换行状态不再丢失（结构层验证）
        html = '<div><span class="nowrap"><img src="/d.png"/></span><h2>Skills</h2></div>'
        out = preprocess(html, self.OPS)
        soup = BeautifulSoup(out, "html.parser")
        self.assertIsNone(soup.find("span"))
        self.assertIsNotNone(soup.find("h2"))


if __name__ == "__main__":
    unittest.main()
