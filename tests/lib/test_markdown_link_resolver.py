"""Unit tests for scripts/lib/markdown_link_resolver.py"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from scripts.lib.markdown_link_resolver import (
    build_page_mapping,
    fix_all_links,
    resolve_link,
)


class TestBuildPageMapping(unittest.TestCase):
    """Test build_page_mapping with temp directories."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_md(self, filename: str, source_url: str) -> None:
        content = f"# Title\n\n> Source: {source_url}\n\nBody text.\n"
        Path(self.tmpdir, filename).write_text(content, encoding="utf-8")

    def test_basic_mapping(self) -> None:
        self._write_md("Page_42.md", "https://wiki.example.com/Pages/Page_42.html")
        mapping = build_page_mapping(self.tmpdir)
        self.assertIn("Pages/Page_42.html", mapping)
        self.assertEqual(mapping["Pages/Page_42.html"], "Page_42.md")

    def test_bare_title_mapping(self) -> None:
        self._write_md("Guide.md", "https://wiki.example.com/Guide.html")
        mapping = build_page_mapping(self.tmpdir)
        self.assertIn("Guide.html", mapping)

    def test_empty_directory(self) -> None:
        mapping = build_page_mapping(self.tmpdir)
        self.assertEqual(mapping, {})

    def test_no_source_line(self) -> None:
        Path(self.tmpdir, "NoSource.md").write_text("# No source\n\nJust text.\n", encoding="utf-8")
        mapping = build_page_mapping(self.tmpdir)
        self.assertEqual(mapping, {})

    def test_multiple_files(self) -> None:
        self._write_md("A.md", "https://example.com/Pages/A.html")
        self._write_md("B.md", "https://example.com/Pages/B.html")
        mapping = build_page_mapping(self.tmpdir)
        self.assertEqual(len(mapping), 2)


class TestResolveLink(unittest.TestCase):
    """Test resolve_link with various href patterns."""

    def setUp(self) -> None:
        self.mapping = {
            "Pages/Page_42.html": "Page_42.md",
            "Pages/Page_99.html": "Page_99.md",
            "Guide.html": "Guide.md",
        }
        self.base_web = "https://wiki.example.com"
        self.doc_base = "https://wiki.example.com/Packages/Docs/Guide"

    def test_absolute_url_passthrough(self) -> None:
        result = resolve_link(
            "https://other.site.com/page",
            self.mapping, self.base_web, self.doc_base,
        )
        self.assertEqual(result, "https://other.site.com/page")

    def test_anchor_passthrough(self) -> None:
        result = resolve_link("#section", self.mapping, self.base_web, self.doc_base)
        self.assertEqual(result, "#section")

    def test_javascript_passthrough(self) -> None:
        result = resolve_link(
            "javascript:void(0)",
            self.mapping, self.base_web, self.doc_base,
        )
        self.assertEqual(result, "javascript:void(0)")

    def test_relative_pages_in_mapping(self) -> None:
        result = resolve_link(
            "../Pages/Page_42.html",
            self.mapping, self.base_web, self.doc_base,
        )
        self.assertEqual(result, "Page_42.md")

    def test_relative_pages_not_in_mapping(self) -> None:
        result = resolve_link(
            "../Pages/Page_UNKNOWN.html",
            self.mapping, self.base_web, self.doc_base,
        )
        # Should return full URL
        self.assertIn("https://", result)

    def test_bare_pages_in_mapping(self) -> None:
        result = resolve_link(
            "Pages/Page_99.html",
            self.mapping, self.base_web, self.doc_base,
        )
        self.assertEqual(result, "Page_99.md")

    def test_uses_contents_false(self) -> None:
        result = resolve_link(
            "../Pages/Page_UNKNOWN.html",
            self.mapping, self.base_web, self.doc_base,
            uses_contents=False,
        )
        # URL without contents/ segment
        self.assertIn("https://", result)


class TestFixAllLinks(unittest.TestCase):
    """Test fix_all_links on full markdown text."""

    def setUp(self) -> None:
        self.mapping = {
            "Pages/Page_1.html": "Page_1.md",
            "Pages/Page_2.html": "Page_2.md",
        }
        self.base_web = "https://wiki.example.com"
        self.doc_base = "https://wiki.example.com/Packages/Docs/Guide"

    def test_resolve_multiple_links(self) -> None:
        text = "See [Page 1](../Pages/Page_1.html) and [Page 2](../Pages/Page_2.html)."
        result = fix_all_links(text, self.mapping, self.base_web, self.doc_base)
        self.assertIn("Page_1.md", result)
        self.assertIn("Page_2.md", result)

    def test_no_links(self) -> None:
        text = "Just some text without links."
        result = fix_all_links(text, self.mapping, self.base_web, self.doc_base)
        self.assertEqual(result, text)

    def test_mixed_links(self) -> None:
        text = "[External](https://other.com) and [Internal](../Pages/Page_1.html)."
        result = fix_all_links(text, self.mapping, self.base_web, self.doc_base)
        self.assertIn("https://other.com", result)
        self.assertIn("Page_1.md", result)


if __name__ == "__main__":
    unittest.main()
