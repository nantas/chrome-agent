"""Unit tests for scripts/lib/extraction/html_to_markdown.py"""

from __future__ import annotations

import unittest

from scripts.lib.extraction.html_to_markdown import html_to_markdown


class TestHtmlToMarkdownBasic(unittest.TestCase):
    """Basic conversion scenarios."""

    def test_empty_string(self) -> None:
        self.assertEqual(html_to_markdown(""), "")

    def test_plain_text(self) -> None:
        result = html_to_markdown("Hello world")
        self.assertIn("Hello", result)

    def test_heading_h1(self) -> None:
        result = html_to_markdown("<h1>Title</h1>")
        self.assertIn("# Title", result)

    def test_heading_h2(self) -> None:
        result = html_to_markdown("<h2>Section</h2>")
        self.assertIn("## Section", result)

    def test_heading_h3(self) -> None:
        result = html_to_markdown("<h3>Sub</h3>")
        self.assertIn("### Sub", result)

    def test_paragraph(self) -> None:
        result = html_to_markdown("<p>Hello world</p>")
        self.assertIn("Hello world", result)

    def test_strong(self) -> None:
        result = html_to_markdown("<strong>bold</strong>")
        self.assertIn("**bold**", result)

    def test_emphasis(self) -> None:
        result = html_to_markdown("<em>italic</em>")
        self.assertIn("*italic*", result)

    def test_line_break(self) -> None:
        result = html_to_markdown("line1<br>line2")
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_anchor(self) -> None:
        result = html_to_markdown('<a href="https://example.com">link</a>')
        self.assertIn("link", result)

    def test_list_items(self) -> None:
        result = html_to_markdown("<ul><li>A</li><li>B</li></ul>")
        self.assertIn("A", result)
        self.assertIn("B", result)


class TestHtmlToMarkdownNoise(unittest.TestCase):
    """Noise removal: script, style, noscript."""

    def test_script_removed(self) -> None:
        result = html_to_markdown("<script>alert('hi')</script><p>Keep</p>")
        self.assertNotIn("alert", result)
        self.assertIn("Keep", result)

    def test_style_removed(self) -> None:
        result = html_to_markdown("<style>body{}</style><p>Keep</p>")
        self.assertNotIn("body{}", result)
        self.assertIn("Keep", result)

    def test_noscript_removed(self) -> None:
        result = html_to_markdown("<noscript>nope</noscript><p>Keep</p>")
        self.assertNotIn("nope", result)
        self.assertIn("Keep", result)


class TestHtmlToMarkdownTables(unittest.TestCase):
    """Table conversion integration."""

    def test_simple_table(self) -> None:
        html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
        result = html_to_markdown(html)
        self.assertIn("| A | B |", result)
        self.assertIn("| 1 | 2 |", result)

    def test_nav_table_removed(self) -> None:
        html = '<table class="page_nav"><tr><td>Nav</td></tr></table><p>Content</p>'
        result = html_to_markdown(html)
        self.assertNotIn("Nav", result)
        self.assertIn("Content", result)

    def test_breadcrumb_removed(self) -> None:
        html = '<div class="breadcrumb">Home > Page</div><p>Content</p>'
        result = html_to_markdown(html)
        self.assertNotIn("Home > Page", result)
        self.assertIn("Content", result)


class TestHtmlToMarkdownEntities(unittest.TestCase):
    """HTML entity decoding."""

    def test_amp(self) -> None:
        result = html_to_markdown("<p>A &amp; B</p>")
        self.assertIn("A & B", result)

    def test_lt_gt(self) -> None:
        result = html_to_markdown("<p>1 &lt; 2</p>")
        self.assertIn("1 < 2", result)


class TestHtmlToMarkdownSelect(unittest.TestCase):
    """Select/option stripping."""

    def test_select_removed(self) -> None:
        html = "<p>Before</p><select><option>A</option></select><p>After</p>"
        result = html_to_markdown(html)
        self.assertNotIn("<select", result)
        self.assertNotIn("<option", result)
        self.assertIn("Before", result)
        self.assertIn("After", result)


class TestHtmlToMarkdownWhitespace(unittest.TestCase):
    """Whitespace cleanup."""

    def test_excessive_newlines_collapsed(self) -> None:
        html = "<p>A</p><br><br><br><br><br><p>B</p>"
        result = html_to_markdown(html)
        # Should not have more than 3 consecutive newlines
        self.assertNotIn("\n\n\n\n", result)
        self.assertIn("A", result)
        self.assertIn("B", result)


if __name__ == "__main__":
    unittest.main()
