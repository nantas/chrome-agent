"""Shared infobox renderer — portable infobox → Markdown table conversion.

This module provides the single source of truth for rendering
<aside class="portable-infobox"> elements into Markdown tables.

Used by both:
  - HtmlToMarkdownConverter (pipeline path)
  - sample_converter.py (explore path)

The renderer accepts selectolax Node objects and produces identical output
regardless of which caller invoked it.
"""

import re
import logging
from typing import Optional

log = logging.getLogger("mediawiki-api-extract.converters.infox_renderer")


def render_infobox_table(
    infobox_node,
    extraction_config: dict,
    wiki_domain: str,
    *,
    field_selector: str = "div.pi-data",
    label_selector: str = "h3.pi-data-label",
    value_selector: str = "div.pi-data-value",
    infobox_handlers: Optional[dict] = None,
    # Callable hooks for inline/value rendering — caller provides these
    render_inline_children_fn=None,
    apply_handler_fn=None,
) -> str:
    """Render an infobox container as a complete Markdown table.

    Args:
        infobox_node: A parsed HTML element node (selectolax Node) representing
            the infobox container (e.g. <aside class="portable-infobox">).
        extraction_config: Extraction config dict (from strategy frontmatter).
        wiki_domain: Wiki domain for URL resolution.
        field_selector: CSS selector for infobox field rows.
        label_selector: CSS selector for label elements within a field.
        value_selector: CSS selector for value elements within a field.
        infobox_handlers: Optional map of {data_source: handler_config}.
        render_inline_children_fn: Callable(node) -> str for rendering inline
            content of a node. If None, a simple text-based fallback is used.
        apply_handler_fn: Callable(handler_name, raw_html) -> str for applying
            named field handlers. If None, plain text extraction is used.

    Returns:
        Markdown table string starting with "## Infobox", or empty string if
        no fields found.
    """
    rows: list[tuple[str, str]] = []

    for field_node in infobox_node.css(field_selector):
        # Extract label
        label_node = field_node.css_first(label_selector)
        if label_node:
            label_text = (
                render_inline_children_fn(label_node)
                if render_inline_children_fn
                else _fallback_text(label_node)
            )
        else:
            label_text = ""

        # Skip fields with empty labels (fixes Basement "****" bug)
        # When label node contains only images or no text content, skip the row
        if not label_text.strip():
            continue

        # Extract data-source attribute for handler lookup
        ds = field_node.attributes.get("data-source")

        # Extract value with optional handler
        if ds and infobox_handlers and ds in infobox_handlers:
            raw_html_node = field_node.css_first(value_selector)
            if raw_html_node is not None:
                raw_html = raw_html_node.html if hasattr(raw_html_node, 'html') else ""
            else:
                raw_html = ""
            handler_cfg = infobox_handlers[ds]
            if isinstance(handler_cfg, dict):
                handler_name = handler_cfg.get("handler", "text")
            elif isinstance(handler_cfg, str):
                handler_name = handler_cfg
            else:
                handler_name = "text"

            if apply_handler_fn:
                value = apply_handler_fn(handler_name, raw_html)
            else:
                value = _fallback_text_from_html(raw_html)
        else:
            value_node = field_node.css_first(value_selector)
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
# Fallback helpers (used when caller doesn't provide rendering functions)
# ---------------------------------------------------------------------------

def _fallback_text(node) -> str:
    """Extract plain text from a selectolax node as fallback."""
    text = node.text(deep=True, separator=" ", strip=True) if hasattr(node, 'text') else ""
    return text.strip()


def _fallback_text_from_html(html: str) -> str:
    """Strip HTML tags and return plain text as fallback."""
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
