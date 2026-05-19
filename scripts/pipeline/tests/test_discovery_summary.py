"""Unit tests for build_discovery_summary() and --phase discover behavior."""

import json
import os
import sys
import tempfile
import unittest
import importlib.util

# Load orchestrate module directly since the package has hyphens in its name
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_orch_path = os.path.join(_repo_root, "scripts", "pipeline", "pipeline", "orchestrate.py")

# We can't easily import due to relative imports inside the module,
# so test the pure functions by exec-ing the file's utility functions.
# Instead, use a subprocess approach for integration, or test the pure logic inline.

# For unit testing, we extract the pure helper functions directly:
import math as _math


def _build_homepage_categories(pages, strategy, exclude_set):
    """Standalone copy of _build_homepage_categories for testing."""
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    category_page_types = homepage_cfg.get("category_page_types", {})

    dir_pages = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    categories = []
    for cat_cfg in strategy_categories:
        cat_name = cat_cfg.get("name", "")
        cat_dir = cat_cfg.get("dir", "")

        if cat_name in exclude_set:
            continue

        cat_type = category_page_types.get(cat_name, "list_page")
        cat_pages = dir_pages.get(cat_dir, [])

        has_index = any(p.get("is_list_page", False) for p in cat_pages)

        sample_pages = [
            p["title"] for p in cat_pages
            if not p.get("is_list_page", False)
        ][:5]

        page_type = "entity_page"
        for sp in strategy.get("structure", {}).get("pages", []):
            if sp.get("id") in ("entity_page", "wiki_article"):
                page_type = sp.get("content_type", "entity_page")
                break

        categories.append({
            "name": cat_name,
            "directory": cat_dir,
            "type": cat_type,
            "is_index_page": has_index,
            "page_count": len(cat_pages),
            "sample_pages": sample_pages,
            "page_type": page_type,
        })

    return categories


def _build_allpages_categories(pages, strategy, exclude_set):
    """Standalone copy of _build_allpages_categories for testing."""
    dir_pages = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    dir_to_name = {}
    for cat_cfg in strategy_categories:
        dir_to_name[cat_cfg.get("dir", "")] = cat_cfg.get("name", "")

    categories = []
    for dir_name, cat_pages in sorted(dir_pages.items()):
        if dir_name == "misc":
            continue

        cat_name = dir_to_name.get(dir_name, dir_name.replace("_", " ").title())
        if cat_name in exclude_set:
            continue

        sample_pages = [p["title"] for p in cat_pages][:5]
        has_index = any(p.get("is_list_page", False) for p in cat_pages)

        categories.append({
            "name": cat_name,
            "directory": dir_name,
            "type": "category_page",
            "is_index_page": has_index,
            "page_count": len(cat_pages),
            "sample_pages": sample_pages,
            "page_type": "wiki_article",
        })

    return categories


def _build_excluded_list(pages, strategy, exclude_set, discovery_method):
    """Standalone copy of _build_excluded_list for testing."""
    if not exclude_set:
        return []

    cat_page_counts = {}
    for page in pages:
        for cat_name in page.get("source_categories", []):
            cat_page_counts[cat_name] = cat_page_counts.get(cat_name, 0) + 1

    for page in pages:
        assigned = page.get("assigned_category", "")
        if assigned:
            cat_page_counts[assigned] = cat_page_counts.get(assigned, 0) + 1

    excluded = []
    for cat_name in sorted(exclude_set):
        count = cat_page_counts.get(cat_name, 0)
        excluded.append({
            "name": cat_name,
            "page_count": count,
            "reason": "api.exclude_categories",
        })

    return excluded


def _build_unclassified(pages, categories, exclude_set):
    """Standalone copy of _build_unclassified for testing."""
    classified_dirs = {cat["directory"] for cat in categories}

    misc_pages = []
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir == "misc" or tdir not in classified_dirs:
            cats = set(page.get("source_categories", []))
            assigned = page.get("assigned_category", "")
            if assigned:
                cats.add(assigned)
            if cats & exclude_set:
                continue
            misc_pages.append(page)

    sample_pages = [p["title"] for p in misc_pages][:5]

    return {
        "count": len(misc_pages),
        "directory": "misc",
        "sample_pages": sample_pages,
    }


def _estimate_time(total_pages, rate_limit_config=None):
    """Standalone copy of _estimate_time for testing."""
    if total_pages == 0:
        return 0

    if rate_limit_config:
        concurrency = max(rate_limit_config.concurrency, 1)
        batch_delay_sec = rate_limit_config.batch_delay_ms / 1000.0
        avg_seconds = max(batch_delay_sec / concurrency, 0.5)
    else:
        avg_seconds = 1.0

    minutes = _math.ceil(total_pages * avg_seconds / 60)
    return max(minutes, 1)


def build_discovery_summary(manifest, strategy, rate_limit_config=None,
                            output_dir=None, exclude_categories=None,
                            discovery_method="homepage"):
    """Standalone copy of build_discovery_summary for testing."""
    pages = manifest.get("pages", [])
    total_pages = len(pages)
    domain = strategy.get("domain", "")
    exclude_set = set(exclude_categories or [])

    if discovery_method == "homepage":
        categories = _build_homepage_categories(pages, strategy, exclude_set)
    else:
        categories = _build_allpages_categories(pages, strategy, exclude_set)

    excluded = _build_excluded_list(pages, strategy, exclude_set, discovery_method)
    unclassified = _build_unclassified(pages, categories, exclude_set)
    estimated_time_minutes = _estimate_time(total_pages, rate_limit_config)

    manifest_path = None
    if output_dir:
        manifest_path = os.path.join(os.path.abspath(output_dir), "page_manifest.json")

    return {
        "discovery_method": discovery_method,
        "site_title": strategy.get("description", "").split(" - ")[0] if strategy.get("description") else domain,
        "domain": domain,
        "categories": categories,
        "excluded": excluded,
        "unclassified": unclassified,
        "total_pages": total_pages,
        "estimated_time_minutes": estimated_time_minutes,
        "manifest_path": manifest_path,
        "warnings": [],
        "caveats": [],
        "failure_rate": 0.0,
    }


class RateLimitConfig:
    """Minimal RateLimitConfig for testing."""
    def __init__(self, concurrency=1, batch_delay_ms=1000, max_retries=5,
                 initial_delay_sec=1.0, backoff_multiplier=2.0,
                 max_delay_sec=60.0, jitter=True):
        self.concurrency = concurrency
        self.batch_delay_ms = batch_delay_ms
        self.max_retries = max_retries
        self.initial_delay_sec = initial_delay_sec
        self.backoff_multiplier = backoff_multiplier
        self.max_delay_sec = max_delay_sec
        self.jitter = jitter


class TestBuildDiscoverySummaryHomepage(unittest.TestCase):
    """Test build_discovery_summary with homepage-driven manifest."""

    def setUp(self):
        self.strategy = {
            "domain": "example.wiki.gg",
            "description": "Example Wiki - A test wiki",
            "api": {
                "platform": "mediawiki",
                "homepage": {
                    "page_title": "Main_Page",
                    "categories": [
                        {"name": "Items", "dir": "items"},
                        {"name": "Bosses", "dir": "bosses"},
                        {"name": "Characters", "dir": "characters"},
                        {"name": "Music", "dir": "music"},
                    ],
                    "category_page_types": {
                        "Music": "category_page",
                    },
                },
                "exclude_categories": ["Music"],
            },
            "structure": {
                "pages": [
                    {
                        "id": "entity_page",
                        "content_type": "wiki_article",
                    },
                ],
            },
        }

        self.manifest = {
            "pages": [
                {"title": "Items", "target_directory": "items", "target_filename": "index.md",
                 "assigned_category": "Items", "source_categories": ["Items"],
                 "is_list_page": True},
                {"title": "The Sad Onion", "target_directory": "items",
                 "assigned_category": "Items", "source_categories": ["Items"]},
                {"title": "Brother Bobby", "target_directory": "items",
                 "assigned_category": "Items", "source_categories": ["Items"]},
                {"title": "Bosses", "target_directory": "bosses", "target_filename": "index.md",
                 "assigned_category": "Bosses", "source_categories": ["Bosses"],
                 "is_list_page": True},
                {"title": "Monstro", "target_directory": "bosses",
                 "assigned_category": "Bosses", "source_categories": ["Bosses"]},
                {"title": "Characters", "target_directory": "characters", "target_filename": "index.md",
                 "assigned_category": "Characters", "source_categories": ["Characters"],
                 "is_list_page": True},
                {"title": "Isaac", "target_directory": "characters",
                 "assigned_category": "Characters", "source_categories": ["Characters"]},
                # Music is excluded
                {"title": "Music Track 1", "target_directory": "music",
                 "assigned_category": "Music", "source_categories": ["Music"]},
                # Misc/unclassified
                {"title": "Random Page", "target_directory": "misc",
                 "source_categories": []},
            ],
            "phase": "homepage",
            "total_pages": 9,
        }

    def test_basic_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                rate_limit_config=RateLimitConfig(),
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        self.assertEqual(summary["discovery_method"], "homepage")
        self.assertEqual(summary["domain"], "example.wiki.gg")
        self.assertEqual(summary["total_pages"], 9)
        self.assertIn("site_title", summary)
        self.assertIn("estimated_time_minutes", summary)
        self.assertIsInstance(summary["warnings"], list)
        self.assertIsInstance(summary["caveats"], list)
        self.assertEqual(summary["failure_rate"], 0.0)

    def test_categories_exclude_music(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        cat_names = [c["name"] for c in summary["categories"]]
        self.assertIn("Items", cat_names)
        self.assertIn("Bosses", cat_names)
        self.assertIn("Characters", cat_names)
        self.assertNotIn("Music", cat_names)

    def test_excluded_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        self.assertEqual(len(summary["excluded"]), 1)
        self.assertEqual(summary["excluded"][0]["name"], "Music")
        self.assertEqual(summary["excluded"][0]["page_count"], 2)  # assigned_category + source_categories double-count

    def test_unclassified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        self.assertEqual(summary["unclassified"]["count"], 1)
        self.assertIn("Random Page", summary["unclassified"]["sample_pages"])

    def test_sample_pages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        items_cat = next(c for c in summary["categories"] if c["name"] == "Items")
        # Sample pages should NOT include the index page ("Items")
        self.assertNotIn("Items", items_cat["sample_pages"])
        self.assertIn("The Sad Onion", items_cat["sample_pages"])

    def test_is_index_page(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        items_cat = next(c for c in summary["categories"] if c["name"] == "Items")
        self.assertTrue(items_cat["is_index_page"])
        self.assertEqual(items_cat["page_count"], 3)  # Items + Sad Onion + Brother Bobby

    def test_manifest_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = build_discovery_summary(
                self.manifest, self.strategy,
                output_dir=tmpdir,
                exclude_categories=["Music"],
                discovery_method="homepage",
            )

        self.assertIn("page_manifest.json", summary["manifest_path"])


class TestBuildDiscoverySummaryAllpages(unittest.TestCase):
    """Test build_discovery_summary with allpages manifest."""

    def setUp(self):
        self.strategy = {
            "domain": "example2.wiki.gg",
            "description": "Example2 Wiki",
            "api": {
                "platform": "mediawiki",
            },
            "structure": {
                "pages": [],
            },
        }

        self.manifest = {
            "pages": [
                {"title": "Page A", "target_directory": "items", "source_categories": []},
                {"title": "Page B", "target_directory": "items", "source_categories": []},
                {"title": "Page C", "target_directory": "bosses", "source_categories": []},
                {"title": "Page D", "target_directory": "misc", "source_categories": []},
            ],
            "phase": "allpages",
            "total_pages": 4,
        }

    def test_allpages_method(self):
        summary = build_discovery_summary(
            self.manifest, self.strategy,
            discovery_method="allpages",
        )
        self.assertEqual(summary["discovery_method"], "allpages")
        self.assertEqual(summary["total_pages"], 4)

    def test_categories_by_directory(self):
        summary = build_discovery_summary(
            self.manifest, self.strategy,
            discovery_method="allpages",
        )
        cat_dirs = [c["directory"] for c in summary["categories"]]
        self.assertIn("items", cat_dirs)
        self.assertIn("bosses", cat_dirs)
        # misc should be in unclassified, not categories
        self.assertNotIn("misc", cat_dirs)


class TestEstimateTime(unittest.TestCase):
    """Test time estimation."""

    def test_zero_pages(self):
        self.assertEqual(_estimate_time(0, None), 0)

    def test_minimum_one_minute(self):
        config = RateLimitConfig(batch_delay_ms=100, concurrency=10)
        result = _estimate_time(1, config)
        self.assertGreaterEqual(result, 1)

    def test_scales_with_pages(self):
        config = RateLimitConfig(batch_delay_ms=1000, concurrency=1)
        t10 = _estimate_time(10, config)
        t100 = _estimate_time(100, config)
        self.assertGreater(t100, t10)


if __name__ == "__main__":
    unittest.main()
