"""Homepage HTML parser — extracts category links from MediaWiki homepages.

Parses the homepage HTML using CSS selectors defined in the strategy's
`api.homepage.category_sections` to discover category links and their types.
"""

import logging
import re
from typing import Optional

log = logging.getLogger("mediawiki-api-extract")


def parse_homepage(client, strategy: dict) -> list[dict]:
    """Parse homepage HTML and extract category links.

    Uses strategy ``api.homepage`` configuration to:
    1. Fetch the homepage via MediaWiki action=parse API
    2. Apply CSS selectors from ``category_sections`` to find category links
    3. Return structured category list with name, page_title, and type

    Args:
        client: ApiClient instance for MediaWiki API calls.
        strategy: Parsed strategy frontmatter dict with ``api.homepage``.

    Returns:
        List of dicts::
            [
                {
                    "name": str,          # Category display name
                    "page_title": str,    # Wiki page title
                    "type": str,          # "list_page" or "category_page"
                },
                ...
            ]

    Raises:
        ValueError: If ``api.homepage`` config is missing or incomplete.
        RuntimeError: If homepage fetch returns empty content.
    """
    homepage_cfg = strategy.get("api", {}).get("homepage")
    if not homepage_cfg:
        raise ValueError("Strategy has no 'api.homepage' configuration")

    page_title = homepage_cfg.get("page_title")
    if not page_title:
        raise ValueError("api.homepage.page_title is required")

    # Fetch homepage HTML
    log.info("Fetching homepage: %s", page_title)
    data = client.parse(page=page_title, prop="text", redirects=True)
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        raise RuntimeError(f"Empty HTML returned for homepage '{page_title}'")

    # Extract category links using configured selectors
    category_sections = homepage_cfg.get("category_sections", [])
    category_page_types = homepage_cfg.get("category_page_types", {})

    categories: list[dict] = []
    seen_titles: set[str] = set()
    domain = strategy.get("domain", "")

    for section in category_sections:
        selector = section.get("selector", "")
        if not selector:
            continue
        default_type = section.get("type", "list_page")

        extracted = _extract_links_by_selector(html, selector, domain)
        for link in extracted:
            page_title_str = link["page_title"]
            if page_title_str in seen_titles:
                continue
            seen_titles.add(page_title_str)

            # Determine type: section-level override > category_page_types > default
            cat_type = category_page_types.get(link["name"], default_type)
            _validate_category_type(cat_type)

            categories.append({
                "name": link["name"],
                "page_title": page_title_str,
                "type": cat_type,
            })

    log.info("Extracted %d category links from homepage", len(categories))
    return categories


# ===========================================================================
# Internal helpers
# ===========================================================================

def _extract_links_by_selector(html: str, selector: str,
                               domain: str = "") -> list[dict]:
    """Extract wiki page links matching a CSS selector from HTML.

    Uses a simple regex-based approach to find <a> tags inside elements
    matching the selector pattern. Filters out external and non-wiki links.

    Args:
        html: Raw HTML string.
        selector: CSS selector (supports class selectors like ``.gallerytext a``).
        domain: Wiki domain for filtering external links.

    Returns:
        List of dicts with ``name`` (display text) and ``page_title`` (wiki title).
    """
    results: list[dict] = []

    # Build regex pattern from CSS selector
    # Support simple patterns: .gallerytext a, .category-links a, etc.
    selector_parts = selector.strip().split()
    if not selector_parts:
        return results

    # For selectors like ".gallerytext a", find elements with the class
    class_patterns = []
    for part in selector_parts:
        if part.startswith("."):
            cls = part[1:]
            class_patterns.append(cls)

    if not class_patterns:
        return results

    # Strategy: locate parent elements matching the class(es),
    # then extract <a> tags within them
    for cls in class_patterns:
        # Find opening tags with this class
        tag_pattern = re.compile(
            rf'<[a-z]+[^>]*\bclass\s*=\s*["\'][^"\']*{re.escape(cls)}[^"\']*["\'][^>]*>',
            re.IGNORECASE,
        )
        for match in tag_pattern.finditer(html):
            # Track nested depth to find the matching close tag
            tag_name_match = re.match(r'<([a-z]+)', match.group(0))
            if not tag_name_match:
                continue
            tag_name = tag_name_match.group(1)
            start = match.start()
            pos = match.end()
            depth = 1

            open_re = re.compile(rf'<{re.escape(tag_name)}\b[^>]*(?<!/)>', re.IGNORECASE)
            close_re = re.compile(rf'</{re.escape(tag_name)}\s*>', re.IGNORECASE)

            while depth > 0 and pos < len(html):
                next_open = open_re.search(html, pos)
                next_close = close_re.search(html, pos)

                if next_close is None:
                    break
                if next_open is not None and next_open.start() < next_close.start():
                    depth += 1
                    pos = next_open.end()
                else:
                    depth -= 1
                    if depth == 0:
                        element_html = html[start:next_close.end()]
                        links = _extract_links_from_element(element_html, domain)
                        results.extend(links)
                        pos = next_close.end()
                    else:
                        pos = next_close.end()

    # Deduplicate by page_title within results
    seen: set[str] = set()
    deduped = []
    for link in results:
        if link["page_title"] not in seen:
            seen.add(link["page_title"])
            deduped.append(link)
    return deduped


def _extract_links_from_element(element_html: str, domain: str) -> list[dict]:
    """Extract wiki links from a single HTML element's content.

    Finds all <a href="/wiki/..."> patterns within the element HTML.
    Filters out external links and non-content namespace links.

    Returns:
        List of dicts with ``name`` and ``page_title``.
    """
    results: list[dict] = []
    link_pattern = re.compile(
        r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )

    for match in link_pattern.finditer(element_html):
        href = match.group(1).strip()
        inner_html = match.group(2)

        # Normalize href
        if href.startswith("/wiki/"):
            page_title = href[len("/wiki/"):]
        elif domain and href.startswith(f"https://{domain}/wiki/"):
            page_title = href[len(f"https://{domain}/wiki/"):]
        else:
            continue  # External or non-wiki link

        # Strip query params and fragments
        page_title = page_title.split("?")[0].split("#")[0]

        # Skip non-content namespaces
        if page_title.startswith(("File:", "Category:", "Template:",
                                   "Talk:", "Special:", "Help:", "User:")):
            continue

        # Extract display name from inner HTML (strip tags)
        name = re.sub(r'<[^>]+>', '', inner_html).strip()
        if not name:
            # Fall back to page title
            name = page_title.replace("_", " ")

        # Decode URL encoding in page_title
        try:
            from urllib.parse import unquote as _unquote
            page_title = _unquote(page_title)
        except Exception:
            pass

        # Normalize: replace underscores with spaces
        name = name.replace("_", " ")
        # Also decode name
        try:
            from urllib.parse import unquote as _unquote2
            name = _unquote2(name)
        except Exception:
            pass

        results.append({"name": name, "page_title": page_title.replace("_", " ")})

    return results


def _validate_category_type(cat_type: str) -> None:
    """Validate that a category type is recognized.

    Args:
        cat_type: Category type string.

    Raises:
        ValueError: If type is not ``list_page`` or ``category_page``.
    """
    if cat_type not in ("list_page", "category_page"):
        raise ValueError(
            f"Invalid category page type '{cat_type}'. "
            f"Expected 'list_page' or 'category_page'."
        )
