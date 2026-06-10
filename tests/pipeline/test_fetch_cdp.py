"""Unit tests for scripts/pipeline/pipeline/phases/fetch_cdp.py"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

from scripts.pipeline.pipeline.phases.fetch_cdp import (
    _url_to_safe_path,
    run_fetch_cdp,
)


class TestUrlToSafePath(unittest.TestCase):
    """Test _url_to_safe_path conversion."""

    def test_basic_path(self) -> None:
        result = _url_to_safe_path("https://example.com/Packages/Docs/Page_1.html")
        self.assertEqual(result, "Packages_Docs_Page_1.html")

    def test_deep_path(self) -> None:
        result = _url_to_safe_path(
            "https://example.com/A/B/C/D.html"
        )
        self.assertEqual(result, "A_B_C_D.html")

    def test_root_path(self) -> None:
        result = _url_to_safe_path("https://example.com/")
        self.assertEqual(result, "")

    def test_no_trailing_slash(self) -> None:
        result = _url_to_safe_path("https://example.com/Page.html")
        self.assertEqual(result, "Page.html")


class TestRunFetchCdp(unittest.TestCase):
    """Test run_fetch_cdp with mocked cache and CDP."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.repo_root = self.tmpdir

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_cache_hit_skips(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        mock_cache.is_cached.return_value = True

        pages = [{"url": "https://example.com/Page.html", "title": "Page"}]

        result = run_fetch_cdp(
            pages, "example.com", self.repo_root,
            cdp_extract=MagicMock(),
        )
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["fetched"], 0)

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_cache_miss_fetches(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        mock_cache.is_cached.return_value = False

        cdp_extract = MagicMock(
            return_value={"html": "<h1>Title</h1>"}
        )

        pages = [{"url": "https://example.com/Page.html", "title": "Page"}]

        result = run_fetch_cdp(
            pages, "example.com", self.repo_root,
            cdp_extract=cdp_extract,
        )
        self.assertEqual(result["fetched"], 1)
        self.assertEqual(result["skipped"], 0)
        cdp_extract.assert_called_once()
        mock_cache.save_page_cache.assert_called_once()

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_cdp_returns_none(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        mock_cache.is_cached.return_value = False

        cdp_extract = MagicMock(return_value=None)

        pages = [{"url": "https://example.com/Page.html", "title": "Page"}]

        result = run_fetch_cdp(
            pages, "example.com", self.repo_root,
            cdp_extract=cdp_extract,
        )
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["fetched"], 0)

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_refetch_ignores_cache(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        mock_cache.is_cached.return_value = True

        cdp_extract = MagicMock(
            return_value={"html": "<h1>Title</h1>"}
        )

        pages = [{"url": "https://example.com/Page.html", "title": "Page"}]

        result = run_fetch_cdp(
            pages, "example.com", self.repo_root,
            cdp_extract=cdp_extract,
            re_fetch=True,
        )
        self.assertEqual(result["fetched"], 1)
        cdp_extract.assert_called_once()

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_empty_pages(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        result = run_fetch_cdp(
            [], "example.com", self.repo_root,
            cdp_extract=MagicMock(),
        )
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["fetched"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["failed"], 0)

    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.cache_mod")
    @patch("scripts.pipeline.pipeline.phases.fetch_cdp.time.sleep")
    def test_stats_add_up(self, mock_sleep: object, mock_cache: MagicMock) -> None:
        # Mix: 1 cached, 1 fetched, 1 failed
        call_count = [0]

        def is_cached_side_effect(*args, **kwargs):
            call_count[0] += 1
            return call_count[0] == 1  # First is cached, others not

        mock_cache.is_cached.side_effect = is_cached_side_effect

        def cdp_side_effect(url):
            if "fail" in url:
                return None
            return {"html": "<p>ok</p>"}

        pages = [
            {"url": "https://example.com/cached.html", "title": "cached"},
            {"url": "https://example.com/ok.html", "title": "ok"},
            {"url": "https://example.com/fail.html", "title": "fail"},
        ]

        result = run_fetch_cdp(
            pages, "example.com", self.repo_root,
            cdp_extract=cdp_side_effect,
        )
        self.assertEqual(result["total"], 3)
        self.assertEqual(
            result["fetched"] + result["skipped"] + result["failed"],
            result["total"],
        )


if __name__ == "__main__":
    unittest.main()
