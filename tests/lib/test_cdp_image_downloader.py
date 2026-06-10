"""Unit tests for scripts/lib/cdp_image_downloader.py"""

from __future__ import annotations

import base64
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from scripts.lib.cdp_image_downloader import (
    collect_image_urls,
    download_images,
    fetch_image_as_base64,
    update_markdown_references,
)


def _make_valid_b64_png() -> str:
    """Return a minimal valid 1x1 PNG as base64 string."""
    # Minimal 1x1 transparent PNG
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return base64.b64encode(png_bytes).decode("ascii")


class TestCollectImageUrls(unittest.TestCase):
    """Test collect_image_urls with temp directories."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_md(self, filename: str, content: str) -> None:
        Path(self.tmpdir, filename).write_text(content, encoding="utf-8")

    def test_extracts_matching_urls(self) -> None:
        url = "https://cdn.example.com/contents/Attachments/Attach_1/img.png"
        self._write_md("page.md", f"![alt]({url})")
        result = collect_image_urls(self.tmpdir)
        self.assertEqual(len(result), 1)
        # Key should be the relative path
        keys = list(result.keys())
        self.assertTrue(any("img.png" in k for k in keys))

    def test_non_matching_url_skipped(self) -> None:
        url = "https://cdn.example.com/other/image.png"
        self._write_md("page.md", f"![alt]({url})")
        result = collect_image_urls(self.tmpdir)
        self.assertEqual(len(result), 0)

    def test_empty_directory(self) -> None:
        result = collect_image_urls(self.tmpdir)
        self.assertEqual(result, {})


class TestFetchImageAsBase64(unittest.TestCase):
    """Test fetch_image_as_base64 with mock CDP callback."""

    def test_success(self) -> None:
        b64 = _make_valid_b64_png()
        response = json.dumps({"mime": "image/png", "b64": b64, "size": len(b64)})

        def mock_eval(js: str) -> Optional[str]:
            return response

        result = fetch_image_as_base64("https://example.com/img.png", mock_eval)
        self.assertIsNotNone(result)
        self.assertEqual(result["mime"], "image/png")

    def test_error_response(self) -> None:
        response = json.dumps({"error": "404 Not Found"})

        def mock_eval(js: str) -> Optional[str]:
            return response

        result = fetch_image_as_base64("https://example.com/img.png", mock_eval)
        self.assertIsNotNone(result)
        self.assertIn("error", result)

    def test_none_response(self) -> None:
        def mock_eval(js: str) -> Optional[str]:
            return None

        result = fetch_image_as_base64("https://example.com/img.png", mock_eval)
        self.assertIsNone(result)


class TestDownloadImages(unittest.TestCase):
    """Test download_images with temp directories and mock CDP."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.tmpdir, "images")
        os.makedirs(self.images_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("time.sleep")
    def test_fresh_download(self, mock_sleep: object) -> None:
        b64 = _make_valid_b64_png()
        response = json.dumps({"mime": "image/png", "b64": b64, "size": len(b64)})

        def mock_eval(js: str) -> Optional[str]:
            return response

        url_map = {"https://example.com/img.png": "img.png"}
        stats = download_images(url_map, self.images_dir, mock_eval, delay_sec=0)
        self.assertEqual(stats["downloaded"], 1)
        self.assertEqual(stats["failed"], 0)
        self.assertTrue(Path(self.images_dir, "img.png").exists())

    @patch("time.sleep")
    def test_skip_existing(self, mock_sleep: object) -> None:
        # Create existing file > MIN_EXISTING_SIZE
        existing = Path(self.images_dir, "img.png")
        existing.write_bytes(b"x" * 200)

        def mock_eval(js: str) -> Optional[str]:
            self.fail("Should not call CDP for existing file")

        url_map = {"https://example.com/img.png": "img.png"}
        stats = download_images(url_map, self.images_dir, mock_eval, delay_sec=0)
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(stats["downloaded"], 0)

    @patch("time.sleep")
    def test_empty_url_map(self, mock_sleep: object) -> None:
        stats = download_images({}, self.images_dir, lambda js: None, delay_sec=0)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["downloaded"], 0)


class TestUpdateMarkdownReferences(unittest.TestCase):
    """Test update_markdown_references with temp directories."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_replaces_urls(self) -> None:
        url = "https://cdn.example.com/contents/Attachments/Attach_1/img.png"
        Path(self.tmpdir, "page.md").write_text(
            f"![img]({url})\n", encoding="utf-8"
        )
        url_map = {url: "Attachments/Attach_1/img.png"}
        count = update_markdown_references(self.tmpdir, url_map)
        self.assertEqual(count, 1)
        updated = Path(self.tmpdir, "page.md").read_text(encoding="utf-8")
        self.assertNotIn("https://cdn.example.com", updated)
        self.assertIn("Attachments/Attach_1/img.png", updated)

    def test_no_matching_urls(self) -> None:
        Path(self.tmpdir, "page.md").write_text("No images here.\n", encoding="utf-8")
        url_map = {"https://example.com/img.png": "img.png"}
        count = update_markdown_references(self.tmpdir, url_map)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
