"""Unified HTML preprocessor — config-driven cleanup for explore path.

Replaces sample_converter._apply_extraction() Phase 1-4 with a
single function that executes all preprocessing steps in order.

Spec: unified-html-preprocessing (all 7 requirements)
"""

from __future__ import annotations

import re
from typing import Optional


def preprocess_html(
    html: str,
    config: dict,
    context: str = "explore",
) -> str:
    """Preprocess HTML with config-driven cleanup operations.

    Args:
        html: Raw HTML string.
        config: Extraction config dict from strategy frontmatter.
        context: "explore" (full 6-step preprocessing) or
            "pipeline" (placeholder — returns HTML unchanged; pipeline path
            uses HtmlToMarkdownConverter (selectolax kernel) and does not call
            this function).

    Returns:
        Cleaned HTML string.
    """
    if context == "explore":
        return _preprocess_explore(html, config)
    else:
        # Pipeline context: placeholder — Change 2 does not modify clean_html()
        return html


def _preprocess_explore(html: str, config: dict) -> str:
    """Full 6-step preprocessing for explore path."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Step 1: Remove infobox container
    infobox_cfg = config.get("infobox", {})
    if infobox_cfg.get("enabled") and infobox_cfg.get("selector"):
        for el in soup.select(infobox_cfg["selector"]):
            el.decompose()

    # Step 2: Strip elements matching cleanup_selectors
    for sel in config.get("cleanup_selectors", []):
        for el in soup.select(sel):
            el.decompose()

    # Step 3: Fix lazyload images
    lazyload_cfg = config.get("lazyload", {})
    if lazyload_cfg.get("enabled"):
        placeholder = lazyload_cfg.get("placeholder_pattern", "")
        src_attr = lazyload_cfg.get("real_src_attr", "")
        if placeholder and src_attr:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                data_src = img.get(src_attr, "")
                if placeholder in src and data_src:
                    img["src"] = data_src

    # Step 4: Execute cleanup operations
    cleanup = config.get("cleanup", [])
    _apply_cleanup_ops(soup, cleanup)

    # Step 5: Remove decorative images (config-driven skip patterns)
    skip_patterns = config.get("image_filtering", {}).get("skip_patterns", [])
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if any(re.search(p, src) for p in skip_patterns):
            img.decompose()

    # Step 6: Select main content
    selector = config.get("selectors", {}).get("content", "body")
    content = soup.select_one(selector) or soup.select_one("body") or soup

    return str(content)


def _apply_cleanup_ops(soup, cleanup: list[str]) -> None:
    """Apply config-driven cleanup operations to soup in-place."""
    if "strip_fandom_infobox_tables" in cleanup:
        for cls in [
            "item-table-header", "item-table-body", "item-table-description",
            "item-table-appearance", "infobox-table", "portable-infobox",
        ]:
            for el in soup.find_all("table", class_=lambda x: x and cls in x):
                el.decompose()

    if "convert_ambox_to_text" in cleanup:
        for el in soup.find_all("table", class_=lambda x: x and "ambox" in x):
            text = el.get_text(strip=True)
            new_p = soup.new_tag("p")
            new_p.string = f"\u26a0\ufe0f {text}" if text else ""
            el.replace_with(new_p)

    if "unwrap_image_wrappers" in cleanup:
        for a in soup.find_all("a"):
            children = list(a.children)
            non_empty = [c for c in children if not (isinstance(c, str) and c.strip() == "")]
            if len(non_empty) == 1 and getattr(non_empty[0], "name", None) == "img":
                a.unwrap()
            elif a.get("class") and "image" in a.get("class", []):
                imgs = a.find_all("img")
                if imgs and not a.get_text(strip=True):
                    a.unwrap()

    if "strip_footer" in cleanup:
        for sel in ("#catlinks", "#mw-hidden-catlinks", ".printfooter", ".mw-footer", "#footer"):
            for el in soup.select(sel):
                el.decompose()

    if "strip_edit_links" in cleanup:
        for el in soup.select(".mw-editsection"):
            el.decompose()

    if "strip_skip_links" in cleanup:
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("#mw-") and not a.get_text(strip=True):
                continue
            if a["href"].startswith("#mw-"):
                a.decompose()
        for el in soup.select(".skip-link, [class*=skip-to], #jump-to-nav"):
            el.decompose()

    if "strip_category_links" in cleanup:
        for sel in ("#catlinks", ".mw-normal-catlinks", "#mw-hidden-catlinks",
                    ".catlinks", "[class*=category]", "[id*=catlinks]"):
            for el in soup.select(sel):
                el.decompose()

    if "convert_nested_images" in cleanup:
        for fig in soup.find_all("figure"):
            img = fig.find("img")
            if img:
                fig.replace_with(img)
            else:
                fig.decompose()
        for pic in soup.find_all("picture"):
            img = pic.find("img")
            if img:
                pic.replace_with(img)
            else:
                pic.decompose()
