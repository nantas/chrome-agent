"""Phase 0 — Homepage-driven page discovery and assignment.

Orchestrates homepage parsing → type-specific page discovery → page assignment
→ manifest output. Consumed by Phase B for extraction.
"""

import json
import logging
from typing import Optional

from .homepage_parser import parse_homepage
from .page_assigner import assign_pages

log = logging.getLogger("mediawiki-api-extract")


def run_phase_0(client, strategy: dict, origin: str,
                platform_variant: str = "standard") -> dict:
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
    log.info("Phase 0: Parsing homepage...")
    categories = parse_homepage(client, strategy)
    log.info("Phase 0: Discovered %d category links", len(categories))

    if not categories:
        log.warning("Phase 0: No categories found on homepage — manifest will be empty")
        return {
            "pages": [],
            "phase": "homepage",
            "source": "homepage-driven-discovery",
            "total_pages": 0,
            "categories_discovered": 0,
        }

    # Step 2: Discover pages for each category
    log.info("Phase 0: Discovering pages for %d categories...", len(categories))
    all_pages = _discover_category_pages(client, categories, origin)

    # Step 3: Assign pages to output directories
    log.info("Phase 0: Assigning %d pages to directories...", len(all_pages))
    if all_pages:
        assigned_pages = assign_pages(all_pages, categories, strategy, client)
    else:
        assigned_pages = []

    # Step 4: Build manifest
    manifest = {
        "pages": assigned_pages,
        "phase": "homepage",
        "source": "homepage-driven-discovery",
        "total_pages": len(assigned_pages),
        "categories_discovered": len(categories),
    }

    log.info("Phase 0 complete: %d pages from %d categories",
             len(assigned_pages), len(categories))
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
