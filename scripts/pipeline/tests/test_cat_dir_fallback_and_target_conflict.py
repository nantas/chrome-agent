"""Unit tests for cat_dir auto-fallback and target_path conflict detection.

Spec:
  - specs/homepage-discovery-category-extraction/spec.md
  - specs/convert-target-conflict-detection/spec.md
  - specs/isaac-strategy-dir-completeness/spec.md
Change: openspec/changes/fix-homepage-category-dir-fallback
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is importable
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from scripts.explore.discovery_homepage import _build_homepage_manifest
from scripts.pipeline.pipeline.phases.convert import run_convert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_strategy(categories=None):
    """Build a minimal strategy dict with homepage categories."""
    cats = categories or []
    return {
        "api": {
            "platform": "mediawiki",
            "homepage": {
                "page_title": "Test_Wiki",
                "categories": cats,
                "category_page_types": {},
            },
            "output": {},
            "content_profile": {
                "link_resolver": "exact_title_match",
                "template_processor": "simple_substitution",
            },
        },
        "extraction": {},
    }


def _make_category(name, page_title=None, cat_type="list_page"):
    """Build a category dict."""
    return {
        "name": name,
        "page_title": page_title or name,
        "type": cat_type,
    }


def _mock_client():
    """Return a mock ApiClient that returns empty wikitext."""
    client = MagicMock()
    client.parse.return_value = {"parse": {"wikitext": {"*": ""}}}
    return client


# ===========================================================================
# 2.4.1 — Category without dir mapping auto-falls back to normalized name
# ===========================================================================

class TestCatDirAutoFallback(unittest.TestCase):
    """Scenario: category-without-strategy-dir-mapping from spec."""

    def test_no_dir_mapping_auto_fallback(self):
        """Category without dir mapping auto-falls back to normalized name."""
        categories = [_make_category("Completion Marks")]
        strategy = _make_strategy([])  # No dir mappings
        assigned_pages = []
        client = _mock_client()

        manifest = _build_homepage_manifest(assigned_pages, categories, client, strategy)

        # Find the Completion Marks entry
        pages = manifest["pages"]
        entry = next(p for p in pages if p["title"] == "Completion Marks")
        self.assertEqual(entry["target_directory"], "completion-marks")
        self.assertEqual(entry["target_filename"], "index.md")
        self.assertTrue(entry["is_list_page"])

    def test_no_dir_mapping_updates_existing_entry(self):
        """Existing entry with wrong target_directory gets corrected by auto-fallback."""
        categories = [_make_category("Completion Marks")]
        strategy = _make_strategy([])  # No dir mappings
        assigned_pages = [
            {
                "title": "Completion Marks",
                "target_directory": "items",
                "target_filename": "index.md",
                "source_categories": [],
            }
        ]
        client = _mock_client()

        manifest = _build_homepage_manifest(assigned_pages, categories, client, strategy)

        entry = next(p for p in manifest["pages"] if p["title"] == "Completion Marks")
        self.assertEqual(entry["target_directory"], "completion-marks")
        self.assertEqual(entry["is_list_page"], True)

    def test_auto_fallback_warning_emitted(self):
        """Auto-fallback emits a log.warning."""
        categories = [_make_category("Completion Marks")]
        strategy = _make_strategy([])
        assigned_pages = []
        client = _mock_client()

        with patch("scripts.explore.discovery_homepage.log") as mock_log:
            _build_homepage_manifest(assigned_pages, categories, client, strategy)
            mock_log.warning.assert_any_call(
                "Category '%s' has no dir mapping in strategy, auto-fallback to '%s'",
                "Completion Marks",
                "completion-marks",
            )


# ===========================================================================
# 2.4.2 — Existing dir mapping not affected by auto-fallback
# ===========================================================================

class TestCatDirExistingMapping(unittest.TestCase):
    """Scenario: category-with-strategy-dir-mapping from spec."""

    def test_existing_dir_mapping_not_overridden(self):
        """Category with strategy dir mapping uses strategy value, no fallback."""
        categories = [_make_category("Items")]
        strategy = _make_strategy([{"name": "Items", "dir": "items"}])
        assigned_pages = []
        client = _mock_client()

        with patch("scripts.explore.discovery_homepage.log") as mock_log:
            manifest = _build_homepage_manifest(assigned_pages, categories, client, strategy)

            # No auto-fallback warning should be emitted
            for c in mock_log.warning.call_args_list:
                self.assertNotIn("auto-fallback", c[0])

        entry = next(p for p in manifest["pages"] if p["title"] == "Items")
        self.assertEqual(entry["target_directory"], "items")


# ===========================================================================
# 2.4.3 — Target path conflict: later page skipped
# ===========================================================================

class TestTargetPathConflict(unittest.TestCase):
    """Scenario: detect-and-skip-conflicting-pages from spec."""

    def test_conflict_second_page_skipped(self):
        """When two pages share target_path, second is skipped as target_conflict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "pages": [
                    {
                        "title": "Page_A",
                        "target_directory": "items",
                        "target_filename": "index.md",
                    },
                    {
                        "title": "Page_B",
                        "target_directory": "items",
                        "target_filename": "index.md",
                    },
                ]
            }
            strategy = _make_strategy()
            # Mock cache to return minimal content for both pages
            cache_data = {"rendered_html": "<p>content</p>", "content_acquisition": "html_rendered"}
            with patch("scripts.pipeline.pipeline.phases.convert.cache_mod") as mock_cache, \
                 patch("scripts.pipeline.pipeline.phases.convert.convert_single_page") as mock_convert:
                mock_cache.load_page_cache.return_value = cache_data
                mock_convert.return_value = {
                    "title": "Page_A",
                    "status": "ok",
                    "content": "# Page A",
                }

                results, stats = run_convert(
                    tmpdir, manifest, strategy, "test.wiki.gg", _repo_root
                )

            self.assertEqual(results["Page_B"]["status"], "target_conflict")
            self.assertIn("target_conflict", results["Page_B"]["status"])

    def test_conflict_increments_failed_count(self):
        """Conflicting pages count as failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "pages": [
                    {"title": "A", "target_directory": "d", "target_filename": "f.md"},
                    {"title": "B", "target_directory": "d", "target_filename": "f.md"},
                ]
            }
            strategy = _make_strategy()
            cache_data = {"rendered_html": "<p>x</p>"}
            with patch("scripts.pipeline.pipeline.phases.convert.cache_mod") as mock_cache, \
                 patch("scripts.pipeline.pipeline.phases.convert.convert_single_page") as mock_convert:
                mock_cache.load_page_cache.return_value = cache_data
                mock_convert.return_value = {"title": "A", "status": "ok", "content": "# A"}

                _, stats = run_convert(tmpdir, manifest, strategy, "test.wiki.gg", _repo_root)

            self.assertEqual(stats["failed"], 1)

    def test_three_pages_same_path_first_wins(self):
        """Scenario: multiple-pages-same-path — 3 pages share one target_path.

        Spec: Page A wins, Page B and Page C both marked target_conflict.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "pages": [
                    {"title": "Page_A", "target_directory": "items", "target_filename": "index.md"},
                    {"title": "Page_B", "target_directory": "items", "target_filename": "index.md"},
                    {"title": "Page_C", "target_directory": "items", "target_filename": "index.md"},
                ]
            }
            strategy = _make_strategy()
            cache_data = {"rendered_html": "<p>x</p>"}
            with patch("scripts.pipeline.pipeline.phases.convert.cache_mod") as mock_cache, \
                 patch("scripts.pipeline.pipeline.phases.convert.convert_single_page") as mock_convert:
                mock_cache.load_page_cache.return_value = cache_data
                mock_convert.return_value = {"title": "Page_A", "status": "ok", "content": "# A"}

                results, stats = run_convert(tmpdir, manifest, strategy, "test.wiki.gg", _repo_root)

            self.assertEqual(results["Page_A"]["status"], "ok")
            self.assertEqual(results["Page_B"]["status"], "target_conflict")
            self.assertEqual(results["Page_C"]["status"], "target_conflict")
            self.assertEqual(stats["failed"], 2)


# ===========================================================================
# 2.4.4 — No false positives for unique paths
# ===========================================================================

class TestNoConflictFalsePositive(unittest.TestCase):
    """Scenario: no-false-positives from spec."""

    def test_unique_paths_no_conflicts(self):
        """Pages with unique target paths produce no target_conflict results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "pages": [
                    {"title": "A", "target_directory": "items", "target_filename": "index.md"},
                    {"title": "B", "target_directory": "bosses", "target_filename": "index.md"},
                    {"title": "C", "target_directory": "trinkets", "target_filename": "index.md"},
                ]
            }
            strategy = _make_strategy()
            cache_data = {"rendered_html": "<p>x</p>"}
            with patch("scripts.pipeline.pipeline.phases.convert.cache_mod") as mock_cache, \
                 patch("scripts.pipeline.pipeline.phases.convert.convert_single_page") as mock_convert:
                mock_cache.load_page_cache.return_value = cache_data
                mock_convert.return_value = {"title": "X", "status": "ok", "content": "# X"}

                results, stats = run_convert(tmpdir, manifest, strategy, "test.wiki.gg", _repo_root)

            conflict_results = [r for r in results.values() if r.get("status") == "target_conflict"]
            self.assertEqual(len(conflict_results), 0)
            self.assertEqual(stats["failed"], 0)


# ===========================================================================
# 2.4.5 — Strategy dir mapping takes priority over auto-fallback
# ===========================================================================


# ===========================================================================
# 3.1.1–3.1.3 — Minimal verification set (5 pages from real Isaac data)
# ===========================================================================

class TestMinimalVerificationSet(unittest.TestCase):
    """Integration-style tests using realistic Isaac wiki data patterns.

    Uses 5 key pages to verify the fix end-to-end:
      Items, Completion Marks, Attributes, Bosses, Trinkets
    """

    def _make_isaac_assigned_pages(self):
        """Simulate assigned_pages state after assign_pages() for Isaac wiki."""
        return [
            {
                "title": "Items",
                "target_directory": "items",
                "target_filename": "index.md",
                "source_categories": [],
            },
            {
                "title": "Completion Marks",
                "target_directory": "items",  # Bug: wrong assignment
                "target_filename": "index.md",
                "source_categories": [],
            },
            {
                "title": "Attributes",
                "target_directory": "items",  # Bug: wrong assignment
                "target_filename": "index.md",
                "source_categories": [],
            },
            {
                "title": "Bosses",
                "target_directory": "bosses",
                "target_filename": "index.md",
                "source_categories": [],
            },
            {
                "title": "Trinkets",
                "target_directory": "trinkets",
                "target_filename": "index.md",
                "source_categories": [],
            },
        ]

    def _make_isaac_strategy(self, include_new_cats=True):
        """Build Isaac-like strategy with optional Completion Marks/Attributes."""
        cats = [
            {"name": "Items", "dir": "items"},
            {"name": "Trinkets", "dir": "trinkets"},
            {"name": "Bosses", "dir": "bosses"},
            {"name": "Monsters", "dir": "monsters"},
            {"name": "Characters", "dir": "characters"},
            {"name": "Cards", "dir": "cards"},
            {"name": "Challenges", "dir": "challenges"},
            {"name": "Transformations", "dir": "transformations"},
            {"name": "Chapters", "dir": "chapters"},
            {"name": "Rooms", "dir": "rooms"},
            {"name": "Mechanics", "dir": "mechanics"},
            {"name": "Achievements", "dir": "achievements"},
            {"name": "Pickups", "dir": "pickups"},
            {"name": "Effects", "dir": "effects"},
            {"name": "Curses", "dir": "curses"},
            {"name": "Seeds", "dir": "seeds"},
            {"name": "Endings", "dir": "endings"},
            {"name": "Music", "dir": "music"},
            {"name": "Modes", "dir": "modes"},
            {"name": "Objects", "dir": "objects"},
        ]
        if include_new_cats:
            cats.append({"name": "Completion Marks", "dir": "completion_marks"})
            cats.append({"name": "Attributes", "dir": "attributes"})
        return _make_strategy(cats)

    def test_3_1_2_five_pages_target_path_correct(self):
        """3.1.2: All 5 pages have correct target_path after _build_homepage_manifest."""
        assigned = self._make_isaac_assigned_pages()
        categories = [
            _make_category("Items"),
            _make_category("Completion Marks"),
            _make_category("Attributes"),
            _make_category("Bosses"),
            _make_category("Trinkets"),
        ]
        strategy = self._make_isaac_strategy(include_new_cats=True)
        client = _mock_client()

        manifest = _build_homepage_manifest(assigned, categories, client, strategy)

        pages = {p["title"]: p for p in manifest["pages"]}
        # Strategy-mapped categories: use explicit dir
        self.assertEqual(pages["Items"]["target_directory"], "items")
        self.assertEqual(pages["Bosses"]["target_directory"], "bosses")
        self.assertEqual(pages["Trinkets"]["target_directory"], "trinkets")
        # Newly added strategy mappings: use explicit dir (not auto-fallback)
        self.assertEqual(pages["Completion Marks"]["target_directory"], "completion_marks")
        self.assertEqual(pages["Attributes"]["target_directory"], "attributes")

    def test_3_1_2_without_strategy_mapping_auto_fallback(self):
        """3.1.2: Without strategy mapping, auto-fallback still gives correct paths."""
        assigned = self._make_isaac_assigned_pages()
        categories = [
            _make_category("Items"),
            _make_category("Completion Marks"),
            _make_category("Attributes"),
            _make_category("Bosses"),
            _make_category("Trinkets"),
        ]
        # Strategy WITHOUT Completion Marks / Attributes dir mappings
        strategy = self._make_isaac_strategy(include_new_cats=False)
        client = _mock_client()

        manifest = _build_homepage_manifest(assigned, categories, client, strategy)

        pages = {p["title"]: p for p in manifest["pages"]}
        # Auto-fallback produces hyphenated names
        self.assertEqual(pages["Completion Marks"]["target_directory"], "completion-marks")
        self.assertEqual(pages["Attributes"]["target_directory"], "attributes")
        # Existing mappings unaffected
        self.assertEqual(pages["Items"]["target_directory"], "items")
        self.assertEqual(pages["Bosses"]["target_directory"], "bosses")
        self.assertEqual(pages["Trinkets"]["target_directory"], "trinkets")

    def test_3_1_3_conflict_detection_in_convert(self):
        """3.1.3: Two pages same target_path → conflict detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = {
                "pages": [
                    {"title": "Items", "target_directory": "items", "target_filename": "index.md"},
                    {"title": "Completion Marks", "target_directory": "items", "target_filename": "index.md"},
                ]
            }
            strategy = self._make_isaac_strategy(include_new_cats=False)
            cache_data = {"rendered_html": "<p>x</p>"}
            with patch("scripts.pipeline.pipeline.phases.convert.cache_mod") as mock_cache, \
                 patch("scripts.pipeline.pipeline.phases.convert.convert_single_page") as mock_convert:
                mock_cache.load_page_cache.return_value = cache_data
                mock_convert.return_value = {"title": "Items", "status": "ok", "content": "# Items"}

                results, stats = run_convert(
                    tmpdir, manifest, strategy, "test.wiki.gg", _repo_root
                )

            self.assertEqual(results["Items"]["status"], "ok")
            self.assertEqual(results["Completion Marks"]["status"], "target_conflict")
            self.assertEqual(stats["failed"], 1)

class TestStrategyDirMappingPriority(unittest.TestCase):
    """Scenario: strategy dir mapping is used over auto-fallback."""

    def test_strategy_dir_wins_over_auto_fallback(self):
        """Strategy mapping produces 'completion_marks' not 'completion-marks'."""
        categories = [_make_category("Completion Marks")]
        strategy = _make_strategy([
            {"name": "Completion Marks", "dir": "completion_marks"}
        ])
        assigned_pages = []
        client = _mock_client()

        with patch("scripts.explore.discovery_homepage.log") as mock_log:
            manifest = _build_homepage_manifest(assigned_pages, categories, client, strategy)

            # No auto-fallback warning
            for c in mock_log.warning.call_args_list:
                self.assertNotIn("auto-fallback", c[0])

        entry = next(p for p in manifest["pages"] if p["title"] == "Completion Marks")
        self.assertEqual(entry["target_directory"], "completion_marks")


if __name__ == "__main__":
    unittest.main()
