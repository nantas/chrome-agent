"""TDD for HtmlToMarkdownConverter generic-HTML path (empty wiki_domain).

Covers unify-html-converter spec requirement `cdp-path-uses-shared-kernel`:
the shared kernel SHALL accept wiki_domain="" as a generic-HTML signal and
skip wiki-specific link handling (absolutization, /wiki/ resolution).
"""

from __future__ import annotations

import unittest

from scripts.lib.extraction.converter import (
    HtmlToMarkdownConverter,
    convert_html_to_markdown,
)


class TestEmptyWikiDomainInit(unittest.TestCase):
    def test_empty_string_accepted(self) -> None:
        c = HtmlToMarkdownConverter(wiki_domain="")
        self.assertEqual(c.wiki_domain, "")

    def test_none_still_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            HtmlToMarkdownConverter(wiki_domain=None)


class TestGenericHtmlConversion(unittest.TestCase):
    def test_basic_paragraph(self) -> None:
        md = convert_html_to_markdown("<p>Hello generic</p>", wiki_domain="")
        self.assertIn("Hello generic", md)

    def test_absolute_path_link_not_absolutized(self) -> None:
        """Empty domain MUST leave /foo as-is (no malformed https:///foo)."""
        md = convert_html_to_markdown(
            '<a href="/foo">x</a>', wiki_domain=""
        )
        self.assertIn("/foo", md)
        self.assertNotIn("https:///", md)

    def test_already_absolute_url_preserved(self) -> None:
        md = convert_html_to_markdown(
            '<a href="https://example.com/bar">y</a>', wiki_domain=""
        )
        self.assertIn("https://example.com/bar", md)


if __name__ == "__main__":
    unittest.main()
