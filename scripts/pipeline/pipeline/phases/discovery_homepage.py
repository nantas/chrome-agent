"""Phase 0 — Homepage-driven page discovery and assignment.

Orchestrates homepage parsing → type-specific page discovery → page assignment
→ manifest output. Consumed by Phase B for extraction.
"""

import json
import logging
from typing import Optional

from ..homepage_parser import parse_homepage
from ..page_assigner import assign_pages

log = logging.getLogger("pipeline")


def run_homepage_discovery(client, strategy: dict, origin: str,
                platform_variant: str = "standard",
                exclude_categories: Optional[list[str]] = None) -> dict:
    """Execute Phase 0: homepage-driven discovery + page assignment.

    Pipeline:
    1. Parse homepage HTML to extract category links
    2. For each category, discover member pages (list_page → prop=links,
       category_page → categorymembers)
    3. Assign discovered pages to output directories via priority chain
    4. Output manifest JSON compatible with Phase A format

    Args:
        client: ApiClient instance for MediaWiki API calls.
        strategy: Parsed strategy frontmatter dict.
        origin: Origin URL (e.g. ``https://bindingofisaacrebirth.wiki.gg``).
        platform_variant: Platform variant string (e.g. ``"standard"``, ``"wiki-gg"``).

    Returns:
        Manifest dict with ``pages`` list and metadata::

            {
                "pages": [
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
                ],
                "phase": "homepage",
                "source": "homepage-driven-discovery",
                "total_pages": int,
                "categories_discovered": int,
            }

    Raises:
        ValueError: If ``api.homepage`` config is missing from strategy.
        RuntimeError: If homepage fetch or page discovery fails.
    """
    # Validate strategy config
    homepage_cfg = strategy.get("api", {}).get("homepage")
    if not homepage_cfg:
        raise ValueError("Strategy has no 'api.homepage' configuration. "
                         "Phase 0 requires api.homepage to be defined.")

    # Step 1: Parse homepage to extract category links
    log.info("Homepage discovery: Parsing homepage...")
    categories = parse_homepage(client, strategy)
    log.info("Homepage discovery: Discovered %d category links", len(categories))

    if not categories:
        log.warning("Homepage discovery: No categories found on homepage — manifest will be empty")
        return {
            "pages": [],
            "phase": "homepage",
            "source": "homepage-driven-discovery",
            "total_pages": 0,
            "categories_discovered": 0,
        }

    # Exclude categories (strategy + CLI merged by orchestrator)
    exclude_set = set(exclude_categories or [])
    if exclude_set:
        cat_names = {c["name"] for c in categories}
        excluded_names = exclude_set & cat_names
        unmatched = exclude_set - cat_names
        if excluded_names:
            categories = [c for c in categories if c["name"] not in excluded_names]
            log.info("Homepage discovery: Excluded %d categories: %s", len(excluded_names),
                     ", ".join(sorted(excluded_names)))
        for name in sorted(unmatched):
            log.info("Homepage discovery: Exclude category '%s' not found in homepage categories — ignoring", name)

    if not categories:
        log.warning("Homepage discovery: No categories found on homepage — manifest will be empty")
        return {
            "pages": [],
            "phase": "homepage",
            "source": "homepage-driven-discovery",
            "total_pages": 0,
            "categories_discovered": 0,
        }

    # Step 2: Discover pages for each category
    log.info("Homepage discovery: Discovering pages for %d categories...", len(categories))
    all_pages = _discover_category_pages(client, categories, origin)

    # Step 3: Assign pages to output directories
    log.info("Homepage discovery: Assigning %d pages to directories...", len(all_pages))
    if all_pages:
        assigned_pages = assign_pages(all_pages, categories, strategy, client)
    else:
        assigned_pages = []

    # Step 4: Build manifest (includes category pages + list_page_content)
    manifest = _build_homepage_manifest(assigned_pages, categories, client, strategy)

    log.info("Homepage discovery complete: %d pages from %d categories",
             len(manifest["pages"]), len(categories))
    return manifest


# ===========================================================================
# Page discovery helpers
# ===========================================================================


def _discover_category_pages(client, categories: list[dict],
                             origin: str) -> list[dict]:
    """Discover member pages for each category.

    For ``list_page`` type categories: use ``action=parse&prop=links``.
    For ``category_page`` type categories: use ``action=query&list=categorymembers``.

    Args:
        client: ApiClient instance.
        categories: List of category dicts with ``name``, ``page_title``, ``type``.
        origin: Origin URL (for building full URLs).

    Returns:
        Deduplicated list of discovered pages::

            [
                {
                    "title": str,
                    "source_categories": [str, ...],
                },
                ...
            ]
    """
    all_pages: dict[str, dict] = {}  # title → page info

    for cat in categories:
        cat_name = cat["name"]
        page_title = cat["page_title"]
        cat_type = cat.get("type", "list_page")

        if cat_type == "list_page":
            pages = _discover_list_page_pages(client, page_title, origin)
        elif cat_type == "category_page":
            pages = _discover_category_page_members(client, page_title, origin)
        else:
            log.warning("Unknown category type '%s' for '%s', treating as list_page",
                        cat_type, cat_name)
            pages = _discover_list_page_pages(client, page_title, origin)

        for page_title_str in pages:
            if page_title_str not in all_pages:
                all_pages[page_title_str] = {
                    "title": page_title_str,
                    "source_categories": [],
                }
            if cat_name not in all_pages[page_title_str]["source_categories"]:
                all_pages[page_title_str]["source_categories"].append(cat_name)

        log.info("Category '%s' (%s): discovered %d sub-pages",
                 cat_name, cat_type, len(pages))

    return list(all_pages.values())


def _discover_list_page_pages(client, page_title: str, origin: str) -> list[str]:
    """Discover pages linked from a list page using ``action=parse&prop=links``.

    Args:
        client: ApiClient instance.
        page_title: Wiki page title of the list page.
        origin: Origin URL.

    Returns:
        List of page titles (ns=0 only).
    """
    page_titles: list[str] = []

    try:
        data = client.parse(page=page_title, prop="links", redirects=True)
        links = data.get("parse", {}).get("links", [])

        for link in links:
            ns = link.get("ns", 0)
            if ns != 0:
                continue  # Non-content namespace
            title = link.get("*", "")
            if title:
                page_titles.append(title)

        log.debug("List page '%s': %d linked pages", page_title, len(page_titles))
    except Exception as e:
        log.warning("Failed to discover links from '%s': %s", page_title, e)

    return page_titles


# ===========================================================================
# Manifest builder (includes category pages + list_page_content)
# ===========================================================================


def _build_homepage_manifest(assigned_pages: list[dict],
                              categories: list[dict],
                              client,
                              strategy: dict = None) -> dict:
    """Build the final manifest, including category pages and list_page_content.

    Steps:
    1. Add category pages themselves to assigned_pages (with is_list_page=true)
    2. Fetch list_page_content for all list_page type categories
    3. Build the final manifest dict

    Args:
        assigned_pages: Pages already assigned by assign_pages().
        categories: List of category dicts from homepage parsing.
        client: ApiClient instance for API calls.

    Returns:
        Manifest dict compatible with Phase B/Phase C consumption.
    """
    # Build lookup of existing pages by title
    existing_titles: dict[str, int] = {}
    for i, p in enumerate(assigned_pages):
        existing_titles[p["title"]] = i

    # Build strategy-backed category→dir map (parse_homepage doesn't include dir)
    strategy_cat_dir: dict[str, str] = {}
    if strategy:
        for sc in strategy.get("api", {}).get("homepage", {}).get("categories", []):
            strategy_cat_dir[sc["name"]] = sc.get("dir", "")

    cat_dir_map: dict[str, dict] = {}
    for c in categories:
        cat_dir_map[c["name"]] = c

    # Step 1: Add category pages (with is_list_page=true) if not already present
    for cat in categories:
        page_title = cat.get("page_title", cat["name"])
        # Use strategy-backed dir mapping, fall back to category dict (empty for parse_homepage)
        cat_dir = strategy_cat_dir.get(cat["name"], cat.get("dir", ""))
        cat_name = cat["name"]

        # Auto-fallback: if no strategy dir mapping, normalize category name as directory
        if not cat_dir:
            cat_dir = cat_name.lower().replace(" ", "-")
            log.warning("Category '%s' has no dir mapping in strategy, auto-fallback to '%s'",
                        cat_name, cat_dir)

        if page_title in existing_titles:
            # Update existing entry: add is_list_page and ensure assignment
            idx = existing_titles[page_title]
            assigned_pages[idx]["is_list_page"] = True
            assigned_pages[idx]["assignment_method"] = "homepage_category"
            assigned_pages[idx]["target_directory"] = cat_dir
            assigned_pages[idx]["target_filename"] = "index.md"
            if cat_name not in assigned_pages[idx].get("source_categories", []):
                assigned_pages[idx].setdefault("source_categories", []).append(cat_name)
        else:
            # Add new entry for the category page itself
            entry = {
                "title": page_title,
                "target_directory": cat_dir,
                "target_filename": "index.md",
                "assigned_category": cat_name,
                "mw_categories": [],
                "assignment_method": "homepage_category",
                "source_categories": [cat_name],
                "is_list_page": True,
            }
            assigned_pages.append(entry)
            existing_titles[page_title] = len(assigned_pages) - 1

    # Step 2: Fetch list_page_content for all list_page categories
    list_page_content: dict[str, str] = {}
    list_pages_to_fetch = [
        c for c in categories
        if c.get("type", "list_page") == "list_page"
    ]

    if list_pages_to_fetch:
        log.info("Homepage discovery: Fetching list page content for %d categories...",
                 len(list_pages_to_fetch))
        for cat in list_pages_to_fetch:
            page_title = cat.get("page_title", cat["name"])
            try:
                data = client.parse(page=page_title, prop="wikitext")
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                if wikitext:
                    list_page_content[page_title] = wikitext
                    log.debug("Fetched wikitext for list page '%s' (%d chars)",
                              page_title, len(wikitext))
                else:
                    log.warning("List page '%s' returned empty wikitext", page_title)
            except Exception as e:
                log.warning("Failed to fetch list page content for '%s': %s — continuing",
                            page_title, e)

    # Step 3: Build manifest
    manifest = {
        "pages": assigned_pages,
        "list_page_content": list_page_content,
        "phase": "homepage",
        "source": "homepage-driven-discovery",
        "total_pages": len(assigned_pages),
        "categories_discovered": len(categories),
    }

    list_count = len(list_page_content)
    log.info("Homepage discovery manifest built: %d pages, %d list page contents",
             len(assigned_pages), list_count)
    return manifest


def _discover_category_page_members(client, page_title: str,
                                    origin: str) -> list[str]:
    """Discover category members using ``action=query&list=categorymembers``.

    Args:
        client: ApiClient instance.
        page_title: Category page title (with or without ``Category:`` prefix).
        origin: Origin URL.

    Returns:
        List of member page titles.
    """
    member_titles: list[str] = []
    cmtitle = f"Category:{page_title}" if not page_title.startswith("Category:") else page_title

    try:
        cmcontinue = None
        while True:
            params = {
                "list": "categorymembers",
                "cmtitle": cmtitle,
                "cmtype": "page",
                "cmlimit": "max",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            data = client.query(**params)
            query = data.get("query", {})

            for member in query.get("categorymembers", []):
                ns = member.get("ns", 0)
                if ns != 0:
                    continue  # Keep only ns=0 pages
                title = member.get("title", "")
                if title:
                    member_titles.append(title)

            # Continue pagination
            cont = data.get("continue", {})
            cmcontinue = cont.get("cmcontinue")
            if not cmcontinue:
                break

        log.debug("Category '%s': %d member pages", cmtitle, len(member_titles))
    except Exception as e:
        log.warning("Failed to discover members of '%s': %s", cmtitle, e)

    return member_titles
