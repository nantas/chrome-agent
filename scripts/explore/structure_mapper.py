"""StructureMapper — extract nav structure, page type, and content patterns from HTML."""

import re
from typing import Optional

from bs4 import BeautifulSoup


def _extract_nav(soup: BeautifulSoup, max_items: int = 10) -> list[str]:
    """Extract top-level nav section labels (≤10 items)."""
    labels = []

    # Try common nav selectors
    for selector in ["nav", ".mw-parser-output > h2", "#mw-panel", ".sidebar", ".wiki-nav"]:
        if selector.startswith(".") or selector.startswith("#"):
            els = soup.select(selector)
        else:
            els = soup.find_all(selector)
        for el in els:
            if el.name == "nav":
                # Extract individual link texts from nav
                for a in el.find_all("a"):
                    text = a.get_text(strip=True)
                    if text and text not in labels:
                        labels.append(text)
                    if len(labels) >= max_items:
                        break
            else:
                text = el.get_text(strip=True)
                if text and text not in labels:
                    labels.append(text)
            if len(labels) >= max_items:
                break
        if len(labels) >= max_items:
            break

    # Fallback: headings in content area
    if not labels:
        content = soup.select_one("#mw-content-text") or soup.select_one("main") or soup.select_one("article") or soup
        for h2 in content.find_all("h2"):
            text = h2.get_text(strip=True)
            if text and text not in labels:
                labels.append(text)
            if len(labels) >= max_items:
                break

    return labels[:max_items]


def _detect_page_type(soup: BeautifulSoup) -> str:
    """Detect page type based on DOM features."""
    # Check for home page indicators
    title = soup.find("title")
    title_text = title.get_text(strip=True).lower() if title else ""
    if any(word in title_text for word in ["home", "main page", "homepage", "welcome"]):
        return "home"

    # Check for list/category page
    tables = soup.find_all("table")
    data_rows = sum(len(t.find_all("tr")) for t in tables)
    list_items = len(soup.find_all("li"))
    if data_rows > 5 or list_items > 20:
        # But if there's a lot of prose, it might be an article
        paragraphs = len(soup.find_all("p"))
        if paragraphs > 10 and data_rows < 10:
            return "article"
        return "list"

    # Check for gallery
    images = soup.find_all("img")
    if len(images) > 10:
        return "gallery"

    # Default to article if substantial content
    paragraphs = len(soup.find_all("p"))
    if paragraphs > 3:
        return "article"

    return "home"


def _detect_content_structure(soup: BeautifulSoup) -> dict:
    """Detect content structure features."""
    tables = soup.find_all("table")
    data_tables = [t for t in tables if len(t.find_all("tr")) > 2]

    infobox = bool(soup.find(class_=re.compile(r"infobox|portable-infobox"))) or bool(
        soup.find("table", class_=re.compile(r"infobox|portable-infobox"))
    )

    list_items = soup.find_all("li")
    cards = bool(soup.find(class_=re.compile(r"card|tile|grid-item|list-item")))

    return {
        "has_tables": len(data_tables) > 0,
        "table_count": len(data_tables),
        "has_infobox": infobox,
        "has_lists": len(list_items) > 5,
        "list_item_count": len(list_items),
        "has_card_pattern": cards,
    }


def _query_category_counts(base_url: str, categories: list[str]) -> dict[str, int]:
    """Query MediaWiki API for category member counts."""
    import urllib.request
    from urllib.parse import quote

    counts = {}
    for cat in categories:
        cat_name = cat.replace(" ", "_")
        url = f"{base_url}?action=query&list=categorymembers&cmtitle=Category:{quote(cat_name)}&cmlimit=1&format=json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "chrome-agent-explore/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                cm = data.get("query", {}).get("categorymembers", [])
                counts[cat] = len(cm) if cm else 0
        except Exception:
            counts[cat] = 0
    return counts


def map_structure(html: str, api_config: Optional[dict] = None) -> dict:
    """Extract structure from HTML.

    Args:
        html: Raw HTML content
        api_config: Optional detected API config (for category queries)

    Returns:
        {
            "page_type": str,
            "nav_sections": [str],
            "content_structure": {has_tables, table_count, has_infobox, ...},
            "category_counts": {cat: count} (if API available),
        }
    """
    soup = BeautifulSoup(html, "html.parser")

    page_type = _detect_page_type(soup)
    nav_sections = _extract_nav(soup)
    content_structure = _detect_content_structure(soup)

    category_counts = {}
    if api_config and api_config.get("type") == "mediawiki":
        # Derive categories from nav sections
        category_counts = _query_category_counts(
            api_config["base_url"],
            nav_sections[:5],  # Limit to avoid too many API calls
        )

    return {
        "page_type": page_type,
        "nav_sections": nav_sections,
        "content_structure": content_structure,
        "category_counts": category_counts,
    }


import json  # noqa: E402, used inside _query_category_counts
