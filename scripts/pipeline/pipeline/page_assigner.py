"""Page assignment — assigns discovered pages to output directories.

Uses a priority chain: manual overrides > source category match > MW category tags
(with aliases & page_categories fallback) > default (misc).
Queries MediaWiki category tags in batches for efficiency.
"""

import logging
import time
from typing import Optional

from ..strategies import title_to_filepath

log = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assign_pages(pages: list[dict], categories: list[dict],
                 strategy: dict, client) -> list[dict]:
    """Assign each discovered page to an output directory.

    Priority chain (highest to lowest):
    1. Manual overrides (``api.homepage.manual_assignments``)
    2. Source category match (``source_categories`` against ``assignment_priority``)
    3. MediaWiki category tag matching (with ``mw_category_aliases`` & ``page_categories`` fallback)
    4. Default (``"misc"`` directory)

    Args:
        pages: Discovered pages list from homepage discovery
            (each dict has at least ``title`` and ``source_categories``).
        categories: Category definitions from ``api.homepage.categories``
            (each dict has ``name`` and ``type``).
        strategy: Parsed strategy frontmatter dict.
        client: ApiClient instance for MW category queries.

    Returns:
        Enriched page list with assignment metadata::
            [
                {
                    "title": str,
                    "target_directory": str,
                    "target_filename": str,
                    "assigned_category": Optional[str],
                    "mw_categories": list[str],
                    "assignment_method": str,
                    "source_categories": list[str],
                },
                ...
            ]
    """
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    categories_cfg = homepage_cfg.get("categories", [])
    assignment_priority = homepage_cfg.get("assignment_priority", [])
    manual_assignments = homepage_cfg.get("manual_assignments", {})
    category_page_types = homepage_cfg.get("category_page_types", {})

    # Build lookup maps
    cat_name_to_dir = {c["name"]: c["dir"] for c in categories_cfg}

    # Step 1: Apply manual overrides
    result = _apply_manual_overrides(pages, manual_assignments)

    # Step 2: Apply source category assignments for remaining unassigned pages
    unassigned = [p for p in result if p.get("assignment_method") is None]
    result = _apply_source_category_assignments(
        result, unassigned, assignment_priority, cat_name_to_dir
    )

    # Step 3: Batch query MW categories and apply tag matching
    unassigned = [p for p in result if p.get("assignment_method") is None]
    result = _apply_mw_category_matching(
        result, unassigned, assignment_priority, cat_name_to_dir,
        client, strategy, categories_cfg
    )

    # Step 4: Default assignment for remaining
    for page in result:
        if page.get("assignment_method") is None:
            page["assigned_category"] = None
            page["target_directory"] = "misc"
            page["target_filename"] = title_to_filepath(page["title"], 0)[1]
            page["assignment_method"] = "default"
            log.info("Page '%s' assigned to 'misc' (no matching category)", page["title"])

    log.info("Page assignment complete: %d pages, methods: %s",
             len(result),
             {m: sum(1 for p in result if p["assignment_method"] == m)
              for m in set(p["assignment_method"] for p in result)})
    return result


# ===========================================================================
# Priority chain steps
# ===========================================================================


def _apply_manual_overrides(pages: list[dict],
                            manual_assignments: dict) -> list[dict]:
    """Apply manual override assignments.

    Args:
        pages: Discovered pages.
        manual_assignments: Dict mapping page title → output directory.

    Returns:
        Pages with manual overrides applied.
    """
    result = []
    for page in pages:
        title = page["title"]
        if title in manual_assignments:
            target_dir = manual_assignments[title]
            target_file = title_to_filepath(title, 0)[1]
            page["target_directory"] = target_dir
            page["target_filename"] = target_file
            page["assigned_category"] = None
            page["mw_categories"] = []
            page["assignment_method"] = "manual"
            log.info("Page '%s' manually assigned to '%s'", title, target_dir)
        else:
            page.setdefault("assignment_method", None)
            page.setdefault("mw_categories", [])
        result.append(page)
    return result


def _apply_source_category_assignments(
    pages: list[dict], unassigned: list[dict],
    assignment_priority: list[str],
    cat_name_to_dir: dict[str, str],
) -> list[dict]:
    """Assign pages by matching source_categories against assignment_priority.

    For each unassigned page, iterate assignment_priority in order and
    assign to the first category whose name appears in the page's
    source_categories. Works for both list_page and category_page types.

    Args:
        pages: All pages (with existing assignments preserved).
        unassigned: Subset of pages with no assignment yet.
        assignment_priority: Ordered list of category names (highest first).
        cat_name_to_dir: Map of category name → output directory.

    Returns:
        Updated pages list.
    """
    # Build a title → index map for O(1) updates
    page_index = {p["title"]: i for i, p in enumerate(pages)}

    for page in unassigned:
        source_cats = set(page.get("source_categories", []))
        # Find first matching category in priority order
        for cat_name in assignment_priority:
            if cat_name in source_cats:
                target_dir = cat_name_to_dir.get(cat_name)
                if target_dir:
                    idx = page_index[page["title"]]
                    target_file = title_to_filepath(page["title"], 0)[1]
                    pages[idx]["target_directory"] = target_dir
                    pages[idx]["target_filename"] = target_file
                    pages[idx]["assigned_category"] = cat_name
                    pages[idx]["assignment_method"] = "source_category_match"
                    log.info("Page '%s' assigned to '%s' (source category match: '%s')",
                             page["title"], target_dir, cat_name)
                break  # First matching priority wins
    return pages


def _apply_mw_category_matching(
    pages: list[dict], unassigned: list[dict],
    assignment_priority: list[str],
    cat_name_to_dir: dict[str, str],
    client, strategy: dict,
    categories_cfg: list[dict],
) -> list[dict]:
    """Query MW category tags and assign by priority chain.

    Batches category queries in groups of 50.

    Args:
        pages: All pages.
        unassigned: Pages needing MW category lookup.
        assignment_priority: Ordered list of category names (highest first).
        cat_name_to_dir: Map of category name → output directory.
        client: ApiClient instance.
        strategy: Strategy dict for rate limit config.

    Returns:
        Updated pages list.
    """
    if not unassigned:
        return pages

    # Build a title → page index for quick updates
    page_index = {p["title"]: i for i, p in enumerate(pages)}

    # Batch query MW categories
    titles = [p["title"] for p in unassigned]
    batch_size = 50
    rate_limit_cfg = strategy.get("api", {}).get("rate_limit", {})
    batch_delay_ms = rate_limit_cfg.get("batch_delay_ms", 1000)
    max_retries = rate_limit_cfg.get("retry", {}).get("max_retries", 3)

    for start_idx in range(0, len(titles), batch_size):
        batch = titles[start_idx:start_idx + batch_size]
        _query_batch_categories(batch, page_index, pages, client,
                                max_retries, strategy)

        # Rate limiting delay between batches
        if start_idx + batch_size < len(titles):
            log.debug("Waiting %dms before next category batch", batch_delay_ms)
            time.sleep(batch_delay_ms / 1000.0)

    # Build alias lookup table from mw_category_aliases
    alias_map: dict[str, tuple[str, str]] = {}  # mw_cat_name -> (homepage_cat_name, target_dir)
    cat_aliases: dict[str, list[str]] = {}      # homepage_cat_name -> [aliases]
    for c in categories_cfg:
        aliases = c.get("mw_category_aliases", [])
        if aliases:
            cat_aliases[c["name"]] = aliases
            for alias_name in aliases:
                alias_map[alias_name] = (c["name"], cat_name_to_dir.get(c["name"]))

    # Build page_categories fallback mapping from taxonomy
    page_cat_dir_map: dict[str, str] = {}  # mw_cat_name -> target_dir
    taxonomy = strategy.get("api", {}).get("taxonomy", {})
    page_categories = taxonomy.get("page_categories", {})
    for mw_cat_name, cat_path in page_categories.items():
        top_segment = cat_path.split("/")[0]
        if top_segment in cat_name_to_dir:
            page_cat_dir_map[mw_cat_name] = cat_name_to_dir[top_segment]

    # Now apply priority-based assignment for pages with MW categories
    for page_title, idx in page_index.items():
        page = pages[idx]
        if page.get("assignment_method") is not None:
            continue  # Already assigned

        mw_cats = page.get("mw_categories", [])

        # Find first match in priority order (name or alias)
        assigned = False
        for priority_name in assignment_priority:
            # Direct name match
            if priority_name in mw_cats:
                target_dir = cat_name_to_dir.get(priority_name)
                if target_dir:
                    target_file = title_to_filepath(page["title"], 0)[1]
                    pages[idx]["target_directory"] = target_dir
                    pages[idx]["target_filename"] = target_file
                    pages[idx]["assigned_category"] = priority_name
                    pages[idx]["assignment_method"] = "mw_category_match"
                    log.info("Page '%s' assigned to '%s' (MW category match: '%s')",
                             page["title"], target_dir, priority_name)
                    assigned = True
                    break
            # Alias match
            if not assigned:
                for alias_name in cat_aliases.get(priority_name, []):
                    if alias_name in mw_cats:
                        target_dir = cat_name_to_dir.get(priority_name)
                        if target_dir:
                            target_file = title_to_filepath(page["title"], 0)[1]
                            pages[idx]["target_directory"] = target_dir
                            pages[idx]["target_filename"] = target_file
                            pages[idx]["assigned_category"] = priority_name
                            pages[idx]["assignment_method"] = "mw_category_match"
                            log.info("Page '%s' assigned to '%s' (MW alias match: '%s' → '%s')",
                                     page["title"], target_dir, alias_name, priority_name)
                            assigned = True
                            break
                if assigned:
                    break

        # Fallback: page_categories mapping
        if not assigned and page.get("assignment_method") is None:
            for mw_cat in mw_cats:
                if mw_cat in page_cat_dir_map:
                    target_dir = page_cat_dir_map[mw_cat]
                    target_file = title_to_filepath(page["title"], 0)[1]
                    pages[idx]["target_directory"] = target_dir
                    pages[idx]["target_filename"] = target_file
                    pages[idx]["assigned_category"] = mw_cat
                    pages[idx]["assignment_method"] = "mw_category_match"
                    log.info("Page '%s' assigned to '%s' (MW page_categories fallback: '%s')",
                             page["title"], target_dir, mw_cat)
                    assigned = True
                    break

        if not assigned and page.get("assignment_method") is None:
            log.warning("Page '%s' has no matching MW category — will default to 'misc'",
                        page["title"])

    return pages


def _query_batch_categories(titles: list[str], page_index: dict,
                            pages: list[dict], client,
                            max_retries: int, strategy: dict) -> None:
    """Query MediaWiki category tags for a batch of titles.

    Args:
        titles: List of page titles to query.
        page_index: Map of title → index in pages list.
        pages: All pages list (mutated in place).
        client: ApiClient instance.
        max_retries: Max retry attempts per batch.
        strategy: Strategy dict for config.
    """
    import urllib.parse

    # Build pipe-separated titles
    titles_pipe = "|".join(titles)

    for attempt in range(max_retries):
        try:
            data = client.query(
                prop="categories",
                titles=titles_pipe,
                cllimit="max",
                format="json",
            )
            query = data.get("query", {})
            pages_data = query.get("pages", {})

            for page_id, page_data in pages_data.items():
                if page_id == "-1":
                    continue  # Missing page
                title = page_data.get("title", "").replace(" ", "_").replace("_", " ")
                if title not in page_index:
                    continue

                categories_data = page_data.get("categories", [])
                cat_titles = []
                for cat in categories_data:
                    cat_title = cat.get("title", "")
                    # Extract category name from "Category:X" format
                    if cat_title.startswith("Category:"):
                        cat_name = cat_title[len("Category:"):]
                        cat_titles.append(cat_name)

                idx = page_index[title]
                pages[idx]["mw_categories"] = cat_titles

            return  # Success

        except Exception as e:
            log.warning("Category query failed (attempt %d/%d): %s",
                        attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                # Mark all pages in batch as empty categories (will go to misc)
                log.warning("Category query exhausted retries for %d pages, assigning to misc",
                            len(titles))
                for title in titles:
                    if title in page_index:
                        idx = page_index[title]
                        pages[idx]["mw_categories"] = []
