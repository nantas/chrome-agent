"""Unified infobox extraction — supports BeautifulSoup and selectolax parsers.

Merges the former sample_converter._extract_infobox() (BS4) and
infox_renderer.render_infobox_table() (selectolax) into a single
config-driven function.

Spec: unified-infobox-extraction (all 7 requirements)
"""

from __future__ import annotations

import re
from typing import Callable, Optional

log_mod = __import__("logging").getLogger(__name__)


def extract_infobox(
    html_or_node,
    config: dict,
    wiki_domain: str = "",
    *,
    parser: str = "auto",
    field_selector: Optional[str] = None,
    label_selector: Optional[str] = None,
    value_selector: Optional[str] = None,
    nav_strip_selectors: Optional[list[str]] = None,
    infobox_handlers: Optional[dict] = None,
    render_inline_children_fn: Optional[Callable] = None,
    apply_handler_fn: Optional[Callable] = None,
) -> str:
    """Extract infobox from HTML and return a Markdown table string.

    Supports both BeautifulSoup (str/BS4 input) and selectolax (Node input)
    via parser auto-detection or explicit selection.

    Args:
        html_or_node: Raw HTML string (BS4 mode) or selectolax Node.
        config: Extraction config dict from strategy frontmatter.
        wiki_domain: Wiki domain for URL resolution (e.g. "wiki.gg").
        parser: "auto" | "bs4" | "selectolax".
        field_selector: CSS selector for infobox field rows.
            Default: read from config or "div.pi-data".
        label_selector: CSS selector for label elements.
        value_selector: CSS selector for value elements.
        nav_strip_selectors: Selectors for nav elements to strip from values.
        infobox_handlers: Map of {data_source: handler_config}.
        render_inline_children_fn: Callable(node) -> str for inline rendering.
        apply_handler_fn: Callable(handler_name, raw_html) -> str for handlers.

    Returns:
        Markdown table string starting with "## Infobox", or empty string.
    """
    infobox_cfg = config.get("infobox", config) if isinstance(config, dict) else {}
    selector = infobox_cfg.get("selector", "aside.portable-infobox")
    fsel = field_selector or infobox_cfg.get("field_selector", "div.pi-data")
    lsel = label_selector or infobox_cfg.get("label_selector", "h3.pi-data-label")
    vsel = value_selector or infobox_cfg.get("value_selector", "div.pi-data-value")
    nav_sels = nav_strip_selectors if nav_strip_selectors is not None else infobox_cfg.get("nav_strip_selectors", [])
    handlers = infobox_handlers if infobox_handlers is not None else config.get("infobox_field_handlers", {})

    # Resolve parser mode
    if parser == "auto":
        _type = type(html_or_node).__name__
        if _type in ("str", "Str"):
            parser = "bs4"
        else:
            parser = "selectolax"

    if parser == "bs4":
        return _extract_bs4(
            html_or_node, selector, fsel, lsel, vsel, nav_sels,
            handlers, wiki_domain, config,
        )
    else:
        return _extract_selectolax(
            html_or_node, selector, fsel, lsel, vsel, nav_sels,
            handlers, wiki_domain, config,
            render_inline_children_fn=render_inline_children_fn,
            apply_handler_fn=apply_handler_fn,
        )


# ---------------------------------------------------------------------------
# BS4 mode (explore path)
# ---------------------------------------------------------------------------

def _extract_bs4(
    html: str,
    selector: str,
    field_sel: str,
    label_sel: str,
    value_sel: str,
    nav_strip_selectors: list[str],
    handlers: dict,
    base_url: str,
    config: dict,
) -> str:
    """BS4-based infobox extraction (explore path)."""
    from bs4 import BeautifulSoup, NavigableString

    soup = BeautifulSoup(html, "html.parser") if isinstance(html, str) else html
    container = soup.select_one(selector)
    if not container:
        return ""

    skip_patterns = config.get("image_filtering", {}).get("skip_patterns", [])

    lines = ["## Infobox", "", "| Field | Value |", "| --- | --- |"]

    for field in container.select(field_sel):
        label_el = field.select_one(label_sel)
        value_el = field.select_one(value_sel)
        if not label_el:
            continue
        key = label_el.get_text(strip=True)

        # Skip empty labels (spec: empty-label-skip)
        if not key:
            continue

        # data-source alias for handler lookup
        ds = field.get("data-source", "")
        ds_key = f"{ds}({key})" if ds else ""

        if not value_el:
            lines.append(f"| {key} | |")
            continue

        # Config-driven nav stripping
        for nav_sel in nav_strip_selectors:
            for nav_el in value_el.select(nav_sel):
                nav_el.decompose()

        # Walk descendants with deduplication
        processed: set[int] = set()
        val_parts: list[str] = []

        for child in value_el.descendants:
            if id(child) in processed:
                continue
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    val_parts.append(text)
            elif child.name == "img":
                src = child.get("src", "")
                alt = child.get("alt", "")
                if not src:
                    processed.update(id(c) for c in child.descendants)
                    continue
                if skip_patterns and any(re.search(p, src) for p in skip_patterns):
                    processed.update(id(c) for c in child.descendants)
                    continue
                if base_url and src.startswith("/"):
                    src = base_url + src
                val_parts.append(f"![{alt}]({src})")
                processed.update(id(c) for c in child.descendants)
            elif child.name == "a":
                # Skip nav links
                nav_classes: set[str] = set()
                for nav_sel in nav_strip_selectors:
                    for cls in re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', nav_sel):
                        nav_classes.add(cls)
                if child.get("class") and any(c in nav_classes for c in child.get("class", [])):
                    processed.update(id(c) for c in child.descendants)
                    continue
                imgs = child.find_all("img")
                if imgs and not child.get_text(strip=True):
                    for img in imgs:
                        s = img.get("src", "")
                        a = img.get("alt", "")
                        if not s:
                            continue
                        if skip_patterns and any(re.search(p, s) for p in skip_patterns):
                            continue
                        if base_url and s.startswith("/"):
                            s = base_url + s
                        val_parts.append(f"![{a}]({s})")
                    processed.update(id(c) for c in child.descendants)
                else:
                    text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if href.startswith("/") and base_url:
                        href = base_url + href
                    if text:
                        val_parts.append(f"[{text}]({href})")
                    processed.update(id(c) for c in child.descendants)

        # Handler lookup: label text → data-source alias
        handler_cfg = None
        if handlers:
            if key in handlers:
                handler_cfg = handlers[key]
            elif ds_key and ds_key in handlers:
                handler_cfg = handlers[ds_key]

        if handler_cfg:
            handler_name = handler_cfg.get("handler", "") if isinstance(handler_cfg, dict) else ""
            # BS4 mode: use inline handler application
            val = _apply_bs4_handler(handler_name, val_parts, value_el, skip_patterns, base_url)
        else:
            val = " ".join(val_parts).strip()

        if key and val:
            lines.append(f"| {key} | {val} |")

    if len(lines) <= 4:
        return ""
    return "\n".join(lines)


def _apply_bs4_handler(
    handler_name: str,
    val_parts: list[str],
    value_el,
    skip_patterns: list[str],
    base_url: str,
) -> str:
    """Apply a named handler to BS4 value content."""
    if handler_name == "extract_cur_id":
        cur_el = value_el.select_one(".infobox-nav-cur")
        if cur_el:
            return cur_el.get_text(strip=True)
        return value_el.get_text(strip=True)

    elif handler_name == "count_images":
        imgs = value_el.find_all("img")
        count = 0
        for img in imgs:
            src = img.get("src", "")
            if skip_patterns and any(re.search(p, src) for p in skip_patterns):
                continue
            count += 1
        return str(count) if count else " ".join(val_parts).strip()

    elif handler_name == "dedup_pools":
        seen: set[str] = set()
        parts: list[str] = []
        for a in value_el.find_all("a"):
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if not text or text in seen:
                continue
            seen.add(text)
            if href.startswith("/") and base_url:
                href = base_url + href
            parts.append(f"[{text}]({href})")
        return " ".join(parts) if parts else " ".join(val_parts).strip()

    elif handler_name == "simplify_collection":
        first_a = value_el.find("a")
        if first_a:
            text = first_a.get_text(strip=True)
            href = first_a.get("href", "")
            if href.startswith("/") and base_url:
                href = base_url + href
            return f"[{text}]({href})"
        return " ".join(val_parts).strip()

    return " ".join(val_parts).strip()


# ---------------------------------------------------------------------------
# Selectolax mode (pipeline path)
# ---------------------------------------------------------------------------

def _extract_selectolax(
    infobox_node,
    selector: str,
    field_sel: str,
    label_sel: str,
    value_sel: str,
    nav_strip_selectors: list[str],
    handlers: dict,
    wiki_domain: str,
    config: dict,
    *,
    render_inline_children_fn: Optional[Callable] = None,
    apply_handler_fn: Optional[Callable] = None,
) -> str:
    """Selectolax-based infobox extraction (pipeline path)."""
    rows: list[tuple[str, str]] = []

    for field_node in infobox_node.css(field_sel):
        # Extract label
        label_node = field_node.css_first(label_sel)
        if label_node:
            label_text = (
                render_inline_children_fn(label_node)
                if render_inline_children_fn
                else _fallback_text(label_node)
            )
        else:
            label_text = ""

        # Skip empty labels (spec: empty-label-skip)
        if not label_text.strip():
            continue

        # Extract data-source attribute
        ds = field_node.attributes.get("data-source")

        # Handler lookup: label text → ds_key alias → pure data-source (spec: dual-handler-lookup)
        ds_key = f"{ds}({label_text})" if ds else ""
        handler_cfg = None
        if handlers:
            if label_text in handlers:
                handler_cfg = handlers[label_text]
            elif ds_key and ds_key in handlers:
                handler_cfg = handlers[ds_key]
            elif ds and ds in handlers:
                handler_cfg = handlers[ds]

        # Extract value with optional handler
        if handler_cfg:
            if isinstance(handler_cfg, dict):
                handler_name = handler_cfg.get("handler", "text")
            elif isinstance(handler_cfg, str):
                handler_name = handler_cfg
            else:
                handler_name = "text"

            raw_html_node = field_node.css_first(value_sel)
            raw_html = raw_html_node.html if raw_html_node is not None and hasattr(raw_html_node, 'html') else ""

            if apply_handler_fn:
                value = apply_handler_fn(handler_name, raw_html)
            else:
                value = _fallback_text_from_html(raw_html)
        else:
            value_node = field_node.css_first(value_sel)
            if value_node:
                value = (
                    render_inline_children_fn(value_node)
                    if render_inline_children_fn
                    else _fallback_text(value_node)
                )
            else:
                value = ""

        rows.append((label_text, value))

    if not rows:
        return ""

    table = "## Infobox\n\n"
    table += "| Field | Value |\n"
    table += "| --- | --- |\n"
    for label, value in rows:
        escaped_label = label.replace("|", "\\|")
        escaped_value = value.replace("|", "\\|")
        table += f"| **{escaped_label}** | {escaped_value} |\n"

    return table.strip()


# ---------------------------------------------------------------------------
# Fallback helpers (selectolax path without callbacks)
# ---------------------------------------------------------------------------

def _fallback_text(node) -> str:
    """Extract plain text from a selectolax node."""
    text = node.text(deep=True, separator=" ", strip=True) if hasattr(node, 'text') else ""
    return text.strip()


def _fallback_text_from_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
