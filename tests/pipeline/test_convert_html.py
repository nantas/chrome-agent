"""Unit tests for scripts/pipeline/pipeline/phases/convert_html.py"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.pipeline.pipeline.phases.convert_html import (
    _safe_path_to_title,
    _url_to_safe_path,
    run_convert_html,
)


class TestSafePathToTitle(unittest.TestCase):
    """Identity function."""

    def test_passthrough(self) -> None:
        self.assertEqual(_safe_path_to_title("A_B_C.html"), "A_B_C.html")

    def test_empty(self) -> None:
        self.assertEqual(_safe_path_to_title(""), "")


class TestUrlToSafePath(unittest.TestCase):
    """URL path → safe filename conversion."""

    def test_basic(self) -> None:
        result = _url_to_safe_path("https://example.com/Packages/Docs/Page_1.html")
        self.assertEqual(result, "Packages_Docs_Page_1.html")

    def test_deep(self) -> None:
        result = _url_to_safe_path("https://example.com/A/B/C.html")
        self.assertEqual(result, "A_B_C.html")


class TestRunConvertHtml(unittest.TestCase):
    """Test run_convert_html with mocked cache."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.repo_root = self.tmpdir
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_successful_conversion(self, mock_cache: MagicMock) -> None:
        mock_cache.load_page_cache.return_value = {
            "html": "<h1>Title</h1><p>Body text</p>",
        }

        pages = [
            {"url": "https://example.com/Page.html", "title": "Page"},
        ]

        result = run_convert_html(
            pages, "example.com", self.repo_root, self.output_dir,
        )
        self.assertEqual(result["converted"], 1)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 0)

        # Check output file was created
        md_files = list(Path(self.output_dir).glob("*.md"))
        self.assertGreater(len(md_files), 0)

        # Check content format
        content = md_files[0].read_text(encoding="utf-8")
        self.assertIn("Page", content)
        self.assertIn("> Source:", content)

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_no_cache_entry(self, mock_cache: MagicMock) -> None:
        mock_cache.load_page_cache.return_value = None

        pages = [
            {"url": "https://example.com/Page.html", "title": "Page"},
        ]

        result = run_convert_html(
            pages, "example.com", self.repo_root, self.output_dir,
        )
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["converted"], 0)

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_empty_html(self, mock_cache: MagicMock) -> None:
        mock_cache.load_page_cache.return_value = {"html": ""}

        pages = [
            {"url": "https://example.com/Page.html", "title": "Page"},
        ]

        result = run_convert_html(
            pages, "example.com", self.repo_root, self.output_dir,
        )
        self.assertEqual(result["skipped"], 1)

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_empty_pages(self, mock_cache: MagicMock) -> None:
        result = run_convert_html(
            [], "example.com", self.repo_root, self.output_dir,
        )
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["converted"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 0)

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_stats_add_up(self, mock_cache: MagicMock) -> None:
        call_count = [0]

        def load_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"html": "<p>ok</p>"}
            elif call_count[0] == 2:
                return None  # skip
            else:
                return {"html": ""}  # skip (empty)

        mock_cache.load_page_cache.side_effect = load_side_effect

        pages = [
            {"url": "https://example.com/ok.html", "title": "ok"},
            {"url": "https://example.com/missing.html", "title": "missing"},
            {"url": "https://example.com/empty.html", "title": "empty"},
        ]

        result = run_convert_html(
            pages, "example.com", self.repo_root, self.output_dir,
        )
        self.assertEqual(result["total"], 3)
        self.assertEqual(
            result["converted"] + result["skipped"] + result["failed"],
            result["total"],
        )

    @patch("scripts.pipeline.pipeline.phases.convert_html.cache_mod")
    def test_output_file_has_source_header(self, mock_cache: MagicMock) -> None:
        mock_cache.load_page_cache.return_value = {
            "html": "<p>Content</p>",
        }

        url = "https://example.com/Packages/Docs/Page_123.html"
        pages = [{"url": url, "title": "Page_123"}]

        run_convert_html(
            pages, "example.com", self.repo_root, self.output_dir,
        )

        md_files = list(Path(self.output_dir).glob("*.md"))
        self.assertGreater(len(md_files), 0)
        content = md_files[0].read_text(encoding="utf-8")
        self.assertIn(f"> Source: {url}", content)


if __name__ == "__main__":
    unittest.main()
