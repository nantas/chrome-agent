"""Unified HTML preprocessor — config-driven cleanup for all paths.

Always executes the full 6-step preprocessing pipeline regardless of
calling context. Replaces sample_converter._apply_extraction() Phase 1-4.

Spec: unified-html-preprocessing (all 7 requirements)
"""

from __future__ import annotations

import re
from typing import Optional


def preprocess_html(
    html: str,
    config: dict,
) -> str:
    """Preprocess HTML with config-driven cleanup operations.

    Always executes the full 6-step preprocessing pipeline regardless of
    calling context (explore / pipeline).

    Args:
        html: Raw HTML string.
        config: Extraction config dict from strategy frontmatter.

    Returns:
        Cleaned HTML string.
    """
    from .schema import require_valid_extraction
    require_valid_extraction(config)
    return _preprocess_explore(html, config)


def heading_pairs(soup, rules: list) -> tuple:
    """Find declared source pairs without mutating evidence; return diagnostics."""
    import soupsieve
    pairs, diagnostics, used = [], [], set()
    for rule in rules:
        for heading in soup.select(rule['heading_selector']):
            if id(heading) in used:
                continue
            label = heading.find_next_sibling()
            text = ' '.join(heading.get_text(' ', strip=True).split())
            if (not re.fullmatch(r'h[1-6]', heading.name or '')
                    or not heading.select('[style*="display:none"], [style*="display: none"]')
                    or label is None or not soupsieve.match(rule['label_selector'], label)
                    or not text or rule.get('label_aliases', {}).get(text, text) != ' '.join(label.get_text(' ', strip=True).split())):
                diagnostics.append({'heading': text, 'reason': 'heading_pair_unmatched'})
                continue
            if id(label) in used:
                diagnostics.append({'heading': text, 'reason': 'heading_pair_ambiguous'})
                continue
            used.update((id(heading), id(label)))
            pairs.append((heading, label))
    return pairs, diagnostics


def normalize_heading_pairs(soup, rules: list) -> None:
    pairs, _ = heading_pairs(soup, rules)
    for heading, label in pairs:
        identifiers = [dict((key, node[key]) for key in ('id', 'name') if node.has_attr(key))
                       for node in heading.find_all(True) if node.has_attr('id') or node.has_attr('name')]
        if not heading.get('id'):
            for attrs in identifiers:
                if attrs.get('id'):
                    heading['id'] = attrs['id']
                    break
        heading.clear()
        for attrs in identifiers:
            if attrs.get('id') == heading.get('id'):
                attrs = {key: value for key, value in attrs.items() if key != 'id'}
            if not attrs:
                continue
            anchor = soup.new_tag('span', attrs=attrs)
            heading.append(anchor)
        for child in list(label.contents):
            heading.append(child.extract())
        label.decompose()


def _preprocess_explore(html: str, config: dict) -> str:
    """Full 6-step preprocessing for explore path."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Normalize declared semantic headings before any hidden-content cleanup.
    normalize_heading_pairs(soup, config.get('heading_normalization', []))

    # Step 1: Remove infobox container
    infobox_cfg = config.get("infobox", {})
    if infobox_cfg.get("enabled"):
        for el in soup.select(infobox_cfg.get("selector", "aside.portable-infobox")):
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

    if "strip_empty_paragraphs" in cleanup:
        # Optional empty-content cleanup; never discard named anchors.
        for el in soup.find_all("p"):
            if el.attrs is None:
                continue
            if el.has_attr("id") or el.has_attr("name") or el.select("[id], [name]") or el.find(["img", "table", "ul", "ol", "figure", "video", "audio", "iframe"]):
                continue
            if not el.get_text(strip=True):
                el.decompose()

    if "unwrap_nowrap_spans" in cleanup:
        # Legacy presentation cleanup, not required for block-boundary integrity.
        for el in list(soup.find_all("span", class_="nowrap")):
            el.unwrap()

    if "strip_empty_inline_tags" in cleanup:
        # Preserve media and identifiers even when visible text is empty.
        for el in soup.find_all(["span", "a", "b", "i", "em", "strong", "small", "big", "font", "u", "sup", "sub", "abbr"]):
            if el.attrs is None:
                continue
            if el.has_attr("id") or el.has_attr("name") or el.select("[id], [name]") or el.find(["img", "table", "ul", "ol", "figure", "video", "audio", "iframe"]):
                continue
            if not el.get_text(strip=True):
                el.decompose()

    if "unwrap_list_item_wrappers" in cleanup:
        # MediaWiki 容错渲染：li 被 big/span/div 等表现性元素包裹时不再是
        # ul/ol 直接子节点，共享列表渲染器只接受直接 li。
        # 解包这些包裹元素，使 li 回到直接子节点位置。
        _WRAPPER_TAGS = ("big", "span", "div", "font", "b", "i", "small", "center", "p")
        while True:  # Each successful pass removes a wrapper; finite DOM guarantees termination.
            changed = False
            for lst in soup.find_all(["ul", "ol"]):
                for child in list(lst.children):
                    if getattr(child, "name", None) not in _WRAPPER_TAGS:
                        continue
                    # Only li whose nearest list is this one belongs here.
                    if any(li.find_parent(["ul", "ol"]) is lst for li in child.find_all("li")):
                        child.unwrap()
                        changed = True
            if not changed:
                break

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
