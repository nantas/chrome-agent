"""Discovery summary builder — produces discovery_summary.json from manifest."""

import logging
import math as _math
import os
from typing import Optional

from ...lib.config_resolver import RateLimitConfig

log = logging.getLogger("pipeline")


def build_discovery_summary(manifest: dict, strategy: dict,
                            rate_limit_config: Optional[RateLimitConfig] = None,
                            output_dir: Optional[str] = None,
                            exclude_categories: Optional[list[str]] = None,
                            discovery_method: str = "homepage") -> dict:
    """Build a discovery_summary.json from manifest and strategy.

    Produces a structured summary suitable for SKILL-layer tree diagram
    generation and ask_user confirmation gates.

    Args:
        manifest: Manifest dict with ``pages`` list.
        strategy: Parsed strategy frontmatter dict.
        rate_limit_config: Resolved rate limit config (for time estimation).
        output_dir: Output directory path (for manifest_path field).
        exclude_categories: List of excluded category names.
        discovery_method: One of ``"homepage"``, ``"allpages"``, ``"first_level_links"``.

    Returns:
        Dict conforming to discovery-summary-schema spec.
    """
    pages = manifest.get("pages", [])
    total_pages = len(pages)
    domain = strategy.get("domain", "")

    # Derive exclude set
    exclude_set = set(exclude_categories or [])

    # --- Build categories ---
    if discovery_method == "homepage":
        categories = _build_homepage_categories(pages, strategy, exclude_set)
    else:  # allpages
        categories = _build_allpages_categories(pages, strategy, exclude_set)

    # --- Build excluded list ---
    excluded = _build_excluded_list(pages, strategy, exclude_set, discovery_method)

    # --- Build unclassified ---
    unclassified = _build_unclassified(pages, categories, exclude_set)

    # --- Time estimation ---
    estimated_time_minutes = _estimate_time(total_pages, rate_limit_config)

    # --- Manifest path ---
    manifest_path = None
    if output_dir:
        manifest_path = os.path.join(os.path.abspath(output_dir), "page_manifest.json")

    # --- Warnings & caveats ---
    warnings: list[str] = []
    caveats: list[str] = []
    failure_rate = 0.0

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
        "warnings": warnings,
        "caveats": caveats,
        "failure_rate": failure_rate,
    }


def _build_homepage_categories(pages: list, strategy: dict, exclude_set: set) -> list[dict]:
    """Build categories list from homepage-driven manifest."""
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    category_page_types = homepage_cfg.get("category_page_types", {})

    # Group pages by target_directory
    dir_pages: dict[str, list[dict]] = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    # Build category info from strategy categories
    categories: list[dict] = []
    for cat_cfg in strategy_categories:
        cat_name = cat_cfg.get("name", "")
        cat_dir = cat_cfg.get("dir", "")

        if cat_name in exclude_set:
            continue

        cat_type = category_page_types.get(cat_name, "list_page")
        cat_pages = dir_pages.get(cat_dir, [])

        # Determine if there's an index page (is_list_page)
        has_index = any(p.get("is_list_page", False) for p in cat_pages)

        # Sample pages: first 3-5 non-list-page titles
        sample_pages = [
            p["title"] for p in cat_pages
            if not p.get("is_list_page", False)
        ][:5]

        # Page type from strategy structure
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


def _build_allpages_categories(pages: list, strategy: dict, exclude_set: set) -> list[dict]:
    """Build categories list from allpages manifest by target_directory grouping."""
    # Group pages by target_directory
    dir_pages: dict[str, list[dict]] = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    # Try to map directories to category names from strategy
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    dir_to_name: dict[str, str] = {}
    for cat_cfg in strategy_categories:
        dir_to_name[cat_cfg.get("dir", "")] = cat_cfg.get("name", "")

    # Build taxonomy-based category mapping
    taxonomy = strategy.get("api", {}).get("taxonomy", {})
    page_categories = taxonomy.get("page_categories", {})

    categories: list[dict] = []
    for dir_name, cat_pages in sorted(dir_pages.items()):
        if dir_name == "misc":
            continue  # Handled by unclassified

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


def _build_excluded_list(pages: list, strategy: dict,
                          exclude_set: set, discovery_method: str) -> list[dict]:
    """Build list of excluded categories with page counts."""
    if not exclude_set:
        return []

    # Count pages per category
    cat_page_counts: dict[str, int] = {}
    for page in pages:
        for cat_name in page.get("source_categories", []):
            cat_page_counts[cat_name] = cat_page_counts.get(cat_name, 0) + 1

    # Also check assigned_category
    for page in pages:
        assigned = page.get("assigned_category", "")
        if assigned:
            cat_page_counts[assigned] = cat_page_counts.get(assigned, 0) + 1

    excluded: list[dict] = []
    for cat_name in sorted(exclude_set):
        count = cat_page_counts.get(cat_name, 0)
        excluded.append({
            "name": cat_name,
            "page_count": count,
            "reason": "api.exclude_categories",
        })

    return excluded


def _build_unclassified(pages: list, categories: list[dict],
                         exclude_set: set) -> dict:
    """Build unclassified pages info (pages in 'misc' directory)."""
    # Collect directories that are classified
    classified_dirs = {cat["directory"] for cat in categories}
    excluded_names = exclude_set

    misc_pages: list[dict] = []
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir == "misc" or tdir not in classified_dirs:
            # Check if the page belongs to an excluded category
            cats = set(page.get("source_categories", []))
            assigned = page.get("assigned_category", "")
            if assigned:
                cats.add(assigned)
            if cats & excluded_names:
                continue
            misc_pages.append(page)

    sample_pages = [p["title"] for p in misc_pages][:5]

    return {
        "count": len(misc_pages),
        "directory": "misc",
        "sample_pages": sample_pages,
    }


def _estimate_time(total_pages: int,
                    rate_limit_config: Optional[RateLimitConfig]) -> int:
    """Estimate extraction time in minutes."""
    if total_pages == 0:
        return 0

    if rate_limit_config:
        # Estimate based on rate limit config
        concurrency = max(rate_limit_config.concurrency, 1)
        batch_delay_sec = rate_limit_config.batch_delay_ms / 1000.0
        # Rough estimate: each page takes batch_delay / concurrency seconds
        avg_seconds = max(batch_delay_sec / concurrency, 0.5)
    else:
        avg_seconds = 1.0  # Conservative default

    minutes = _math.ceil(total_pages * avg_seconds / 60)
    return max(minutes, 1)  # Minimum 1 minute for non-empty manifest
