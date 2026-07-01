from __future__ import annotations

"""HTML to Markdown converter — independent of pipeline internals.

Can be imported and used standalone:
    from scripts.lib.extraction.converter import HtmlToMarkdownConverter
"""

import json
import logging
import os
import re
import urllib.request
from typing import Optional
from urllib.parse import unquote

from selectolax.parser import HTMLParser

log = logging.getLogger("pipeline.converters")


class HtmlToMarkdownConverter:
    """Convert MediaWiki server-rendered HTML to standard Markdown.

    Based on wiki.gg project experience (cross-repo reference:
    /Users/nantasmac/projects/personal/wiki.gg/src/wiki_gg/convert/markdown.py
    and clean/html.py).
    """

    _REMOVAL_SELECTORS = (
        ".mw-editsection",
        ".toc",
        "#toc",
        ".hatnote",
    )

    _BLOCK_TAGS = {
        "article", "blockquote", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "ol", "p", "pre", "section", "table", "ul",
    }

    def __init__(self, wiki_domain: str, extraction_config: dict | None = None):
        if wiki_domain is None:
            raise TypeError("wiki_domain must be a string (use empty string for generic HTML)")
        self.wiki_domain = wiki_domain
        self.config = extraction_config or {}
        # Read cleanup selectors from config, fall back to class defaults
        config_cleanup = self.config.get("cleanup_selectors", [])
        self._REMOVAL_SELECTORS = tuple(config_cleanup) if config_cleanup else self._REMOVAL_SELECTORS
        self.title_to_path: dict[str, tuple[str, str]] = {}
        self._redirect_map: dict[str, str] = {}
        # Image skip patterns from config
        self._skip_patterns: list[str] = self.config.get("image_filtering", {}).get("skip_patterns", [])
        # Infobox config: read extraction.infox settings
        infobox_cfg = self.config.get("infobox", {})
        self._infobox_enabled = infobox_cfg.get("enabled", False)
        self._infobox_selector = infobox_cfg.get("selector", "aside.portable-infobox")
        self._infobox_field_selector = infobox_cfg.get("field_selector", "div.pi-data")
        self._infobox_label_selector = infobox_cfg.get("label_selector", "h3.pi-data-label")
        self._infobox_value_selector = infobox_cfg.get("value_selector", "div.pi-data-value")
        # Parse infobox selector for tag + class matching
        sel_parts = self._infobox_selector.lstrip(".").split(".")
        self._infobox_tag = sel_parts[0]
        self._infobox_class_list = sel_parts[1:] if len(sel_parts) > 1 else []
        # Infobox field handlers from config
        self._infobox_handlers: dict = self.config.get("infobox_field_handlers", {})

    def build_link_index(self, manifest_pages: list[dict],
                          redirect_map: dict[str, str] | None = None):
        """Build title -> (target_directory, target_filename) index."""
        self.title_to_path = {
            p["title"]: (p["target_directory"], p["target_filename"])
            for p in manifest_pages
        }
        self._redirect_map = redirect_map or {}

    # ------------------------------------------------------------------
    # Tooltip link merge
    # ------------------------------------------------------------------

    @staticmethod
    def merge_tooltip_links(html: str) -> str:
        """Merge MediaWiki tooltip icon+text link patterns.

        Processes HTML to combine tooltip spans where an icon link and text
        link point to the same URL into a single combined link element.
        """
        # Remove opening tooltip spans (keep inner content)
        html = re.sub(r'<span\s+class="tooltip"[^>]*>', '', html)
        # Remove icon-size spans (keep inner content)
        html = re.sub(r'<span\s+style="--tb-icon-size:[^"]*"[^>]*>', '', html)
        # Remove all closing span tags
        html = re.sub(r'</span>', '', html)

        # Merge consecutive <a> pairs with same href where first has <img>
        def _merge_pair(m):
            url1 = m.group(1)
            img_tag = m.group(2)
            url2 = m.group(3)
            text = m.group(4)
            if url1 == url2:
                return f'<a href="{url1}">{img_tag} {text}</a>'
            return m.group(0)

        html = re.sub(
            r'<a\s+href="([^"]*)"[^>]*>(<img[^>]*>)\s*</a>\s*'
            r'<a\s+href="([^"]*)"[^>]*>([^<]+)</a>',
            _merge_pair,
            html,
        )
        return html

    # ------------------------------------------------------------------
    # YouTube oEmbed extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_video_links(html: str) -> list[str]:
        """Extract YouTube video links with oEmbed titles.

        Parses data-mw-iframeconfig attributes to find YouTube embeds,
        then retrieves video titles via the YouTube oEmbed API.
        Falls back to generic "YouTube Video (ID)" on failure.
        """
        results: list[str] = []
        pattern = re.compile(r'data-mw-iframeconfig="([^"]+)"')
        for match in pattern.finditer(html):
            try:
                config_str = match.group(1).replace('&quot;', '"')
                config = json.loads(config_str)
                src = config.get('src', '')
                vid_match = re.search(r'embed/([a-zA-Z0-9_-]+)', src)
                if not vid_match:
                    continue
                video_id = vid_match.group(1)
                watch_url = f'https://www.youtube.com/watch?v={video_id}'

                # Try oEmbed API with 5s timeout
                try:
                    oembed_url = (
                        f'https://www.youtube.com/oembed'
                        f'?url={watch_url}&format=json'
                    )
                    req = urllib.request.Request(
                        oembed_url,
                        headers={'User-Agent': 'chrome-agent/1.0'},
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        title = data.get('title', '')
                        if title:
                            results.append(f'- [{title}]({watch_url})')
                            continue
                except Exception:
                    pass
                # Fallback on failure
                results.append(
                    f'- [YouTube Video ({video_id})]({watch_url})'
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    # ------------------------------------------------------------------
    # HTML cleaning
    # ------------------------------------------------------------------

    def clean_html(self, html: str) -> str:
        """Remove wiki UI noise and hidden elements."""
        parser = HTMLParser(html)

        for selector in self._REMOVAL_SELECTORS:
            for node in parser.css(selector):
                node.decompose()

        for node in parser.css('img[src*="ModuleEditIcon"]'):
            parent = node.parent
            if parent:
                parent.decompose()

        # Config-driven image filtering
        for pattern in self._skip_patterns:
            for node in parser.css(f'img[src*="{pattern}"]'):
                node.decompose()

        # Remove YouTube oEmbed fallback UI containers
        # wiki.gg YouTube embeds use fixed CSS classes in a nested structure:
        # figure.embedvideo > div.embedvideo-wrapper > div.embedvideo-consent
        #   > div.embedvideo-overlay > div.embedvideo-loader
        # Only decompose the known leaf-level containers, never ancestor divs.
        VIDEO_EMBED_SELECTORS = [
            "div.embedvideo-wrapper",
            "div.embedvideo-consent",
            "div.embedvideo-overlay",
            "div.embedvideo-loader",
        ]
        for selector in VIDEO_EMBED_SELECTORS:
            for node in parser.css(selector):
                node.decompose()

        for node in parser.css("[style]"):
            style = node.attributes.get("style", "") or ""
            if "display:none" in style.replace(" ", ""):
                node.decompose()

        body = parser.body
        if body is not None:
            return body.html or ""
        root = parser.css_first(".mw-parser-output")
        if root is not None:
            return root.html or ""
        return parser.html or ""

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def convert(self, html: str, source_dir: str = "") -> str:
        """Convert cleaned HTML to Markdown."""
        parser = HTMLParser(f'<div data-wrapper="root">{html}</div>')
        root = parser.css_first('[data-wrapper="root"]')
        if root is None:
            return ""

        rendered = self._render_blocks(self._child_nodes(root), source_dir=source_dir)
        return rendered.strip()

    def convert_body(self, html: str, source_dir: str = "") -> str:
        """Full conversion pipeline: merge tooltips → clean → convert → insert videos."""
        # Step 1: Merge tooltip links (raw HTML preprocessing)
        html = self.merge_tooltip_links(html)

        # Step 2: Extract video links from raw HTML before cleanup
        video_links = self.extract_video_links(html)

        # Step 3: Clean HTML
        cleaned = self.clean_html(html)

        # Step 4: Convert to Markdown
        markdown = self.convert(cleaned, source_dir=source_dir)

        # Step 5: Insert video links into body
        if video_links:
            video_section = "\n".join(video_links)
            if "## In-game Footage" in markdown:
                markdown = markdown.replace(
                    "## In-game Footage",
                    f"## In-game Footage\n{video_section}",
                )
            else:
                markdown += f"\n\n## In-game Footage\n{video_section}"

        return markdown

    # ------------------------------------------------------------------
    # Block rendering
    # ------------------------------------------------------------------

    def _render_blocks(self, nodes, source_dir: str = "") -> str:
        blocks = []
        for node in nodes:
            block = self._render_block(node, source_dir=source_dir)
            if block:
                blocks.append(block.strip("\n"))
        return "\n\n".join(block for block in blocks if block).strip()

    def _render_block(self, node, source_dir: str = "", list_level: int = 0) -> str:
        tag = node.tag

        if tag == "-text":
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))

        if tag in {"div", "section", "article", "span"}:
            # Check for portable infobox data-source field
            if tag == "div" and self._infobox_handlers:
                ds = node.attributes.get("data-source")
                if ds:
                    handler_cfg = self._infobox_handlers.get(ds)
                    if handler_cfg and isinstance(handler_cfg, dict):
                        handler_name = handler_cfg.get("handler", "text")
                    elif isinstance(handler_cfg, str):
                        handler_name = handler_cfg
                    else:
                        handler_name = "text"
                    label_node = None
                    for child in self._child_nodes(node):
                        cls = child.attributes.get("class", "") or ""
                        if "pi-data-label" in cls:
                            label_node = child
                            break
                    label_text = self._render_inline_children(label_node, source_dir=source_dir) if label_node else ds
                    raw_value = node.html if hasattr(node, 'html') else ""
                    value = self._apply_infobox_handler(handler_name, raw_value)
                    return f"| **{label_text}** | {value} |"
            if self._has_block_children(node):
                return self._render_blocks(self._child_nodes(node), source_dir=source_dir)
            return self._render_inline_children(node, source_dir=source_dir)

        if tag in {"p", "dd", "dt"}:
            return self._render_inline_children(node, source_dir=source_dir)

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            if level == 1:
                level = 2
            text = self._render_inline_children(node, source_dir=source_dir)
            return f'{"#" * level} {text}'.strip()

        if tag in {"ul", "ol"}:
            return self._render_list(node, source_dir=source_dir, level=list_level)

        if tag == "blockquote":
            body = self._render_blocks(self._child_nodes(node), source_dir=source_dir) or self._render_inline_children(node, source_dir=source_dir)
            lines = body.splitlines() or [""]
            return "\n".join(
                ">" if not line.strip() else f"> {line}" for line in lines
            ).strip()

        if tag == "pre":
            code = node.text(deep=True, separator="", strip=False)
            if code is None:
                code = ""
            code = code.strip("\n")
            if not code:
                return ""
            return f"```\n{code}\n```"

        if tag == "hr":
            return "---"

        if tag == "table":
            return self._render_table(node, source_dir=source_dir)

        if tag == "img":
            return self._render_image(node)

        if tag == "br":
            return ""

        if tag in {"strong", "b", "em", "i", "code", "a"}:
            return self._render_inline(node, source_dir=source_dir)

        # Infobox container detection — render as complete Markdown table
        if self._infobox_enabled and tag == self._infobox_tag:
            cls = node.attributes.get("class", "") or ""
            if all(c in cls for c in self._infobox_class_list):
                result = self._render_infobox_table(node, source_dir=source_dir)
                if result:
                    return result

        if self._has_block_children(node):
            return self._render_blocks(self._child_nodes(node), source_dir=source_dir)

        return self._render_inline_children(node, source_dir=source_dir)

    # ------------------------------------------------------------------
    # List rendering
    # ------------------------------------------------------------------

    def _render_list(self, node, source_dir: str = "", level: int = 0) -> str:
        lines = []
        index = 1
        for child in self._child_nodes(node):
            if child.tag != "li":
                continue
            item_prefix = f"{index}." if node.tag == "ol" else "-"
            item_lines = self._render_list_item(child, source_dir=source_dir, level=level, prefix=item_prefix)
            if item_lines:
                lines.extend(item_lines)
                if node.tag == "ol":
                    index += 1
        return "\n".join(lines).rstrip()

    def _render_list_item(self, node, source_dir: str = "", level: int = 0, prefix: str = "") -> list[str]:
        indent = "  " * level
        inline_parts = []
        nested_lines = []
        for child in self._child_nodes(node):
            if child.tag in {"ul", "ol"}:
                nested = self._render_list(child, source_dir=source_dir, level=level + 1)
                if nested:
                    nested_lines.extend(nested.splitlines())
                continue
            rendered = self._render_inline(child, source_dir=source_dir)
            if rendered:
                inline_parts.append(rendered)
        header = f"{indent}{prefix} {self._render_inline_part_list(inline_parts)}" if inline_parts else f"{indent}{prefix}"
        return [header, *nested_lines]

    # ------------------------------------------------------------------
    # Infobox table rendering
    # ------------------------------------------------------------------

    def _render_infobox_table(self, node, source_dir: str = "") -> str:
        """Render an infobox container as a complete Markdown table.

        Delegates to the shared lib.extraction.infobox module.
        """
        from scripts.lib.extraction.infobox import extract_infobox

        return extract_infobox(
            node,
            self.config,
            self.wiki_domain,
            source_dir=source_dir,
            field_selector=self._infobox_field_selector,
            label_selector=self._infobox_label_selector,
            value_selector=self._infobox_value_selector,
            infobox_handlers=self._infobox_handlers,
            render_inline_children_fn=self._render_inline_children,
            apply_handler_fn=self._apply_infobox_handler,
        )

    # ------------------------------------------------------------------
    # Infobox field handlers
    # ------------------------------------------------------------------

    def _apply_infobox_handler(self, handler_name: str, raw_html: str) -> str:
        """Apply a named infobox field handler to raw HTML value."""
        if handler_name == "text" or not handler_name:
            return self._strip_html(raw_html)
        if handler_name == "image":
            return self._extract_image_value(raw_html)
        if handler_name == "count_images":
            return self._count_images(raw_html)
        if handler_name == "extract_cur_id":
            return self._extract_cur_id(raw_html)
        if handler_name == "dedup_pools":
            return self._dedup_pools(raw_html)
        if handler_name == "simplify_collection":
            return self._simplify_collection(raw_html)
        if handler_name == "extract_tags":
            return self._extract_tags(raw_html)
        # Unknown handler — fall back to text
        log.warning("Unknown infobox handler: %s, falling back to text", handler_name)
        return self._strip_html(raw_html)

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip all HTML tags, return plain text."""
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_image_value(self, html: str) -> str:
        """Extract primary image as Markdown."""
        m = re.search(r'<img[^>]+src="([^"]+)"[^>]*(?:alt="([^"]*)")?', html)
        if not m:
            return self._strip_html(html)
        src, alt = m.group(1), (m.group(2) or "image")
        if src.startswith("/"):
            src = f"https://{self.wiki_domain}{src}"
        return f"![{alt}]({src})"

    @staticmethod
    def _count_images(html: str) -> str:
        """Count images grouped by alt text pattern."""
        imgs = re.findall(r'<img[^>]+alt="([^"]*)"', html)
        if not imgs:
            return "0"
        from collections import Counter
        counts = Counter(imgs)
        parts = [f"{n}× {alt}" for alt, n in counts.items()]
        return ", ".join(parts)

    @staticmethod
    def _extract_cur_id(html: str) -> str:
        """Extract current ID from infobox-nav-cur span."""
        m = re.search(r'<span[^>]*class="[^"]*infobox-nav-cur[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
        if m:
            return re.sub(r'<[^>]+>', '', m.group(1)).strip()
        # Fallback: first code/text content
        text = re.sub(r'<[^>]+>', '', html).strip()
        return text

    def _dedup_pools(self, html: str) -> str:
        """Deduplicate item pool links, keep text-based, skip icon-only."""
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
        seen_urls = set()
        result = []
        for href, inner in links:
            if href in seen_urls:
                continue
            inner_text = re.sub(r'<[^>]+>', '', inner).strip()
            if not inner_text:
                # Icon-only — skip
                continue
            seen_urls.add(href)
            if href.startswith("/"):
                href = f"https://{self.wiki_domain}{href}"
            result.append(f"[{inner_text}]({href})")
        return ", ".join(result) if result else self._strip_html(html)

    def _simplify_collection(self, html: str) -> str:
        """Simplify collection grid to a single page link."""
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
        for href, inner in links:
            inner_text = re.sub(r'<[^>]+>', '', inner).strip()
            if inner_text:
                if href.startswith("/"):
                    href = f"https://{self.wiki_domain}{href}"
                return f"See [{inner_text}]({href})"
        return self._strip_html(html)

    def _extract_tags(self, html: str) -> str:
        """Extract tag tooltips from icon links."""
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]*)"[^>]*>', html)
        if not links:
            links = re.findall(r'<a[^>]+title="([^"]*)"[^>]+href="([^"]+)"[^>]*>', html)
            links = [(h, t) for t, h in links]
        result = []
        for href, title in links:
            if not title:
                continue
            if href.startswith("/"):
                href = f"https://{self.wiki_domain}{href}"
            result.append(f"[{title}]({href})")
        return ", ".join(result) if result else self._strip_html(html)

    # ------------------------------------------------------------------
    # Table rendering
    # ------------------------------------------------------------------

    def _render_cell_content(self, cell, source_dir: str = "") -> str:
        """Render a <th> or <td> cell's inline content, skipping nested <table> elements.

        Returns the rendered Markdown for non-table children, or empty string if
        the cell contains only nested table(s).  A warning is logged when a nested
        table is detected and skipped.
        """
        has_nested_table = any(
            child.tag == "table" for child in self._child_nodes(cell)
        )
        if not has_nested_table:
            return self._render_inline_children(cell, source_dir=source_dir) or ""

        # Found nested table(s) — log warning and render non-table children only
        log.warning(
            "Nested <table> found inside cell — skipping recursive rendering "
            "to prevent grid corruption. Cell text content will be preserved."
        )
        parts = []
        for child in self._child_nodes(cell):
            if child.tag == "table":
                continue
            rendered = self._render_inline(child, source_dir=source_dir)
            if rendered:
                parts.append(rendered)
        return self._join_inline_parts(parts) or ""

    def _build_table_grid(self, node, source_dir: str = "") -> list[list[str]]:
        """Parse a <table> node into a normalized 2D grid, expanding colspan/rowspan."""
        MAX_COLS = 200
        grid: list[list[str]] = []
        col_spans: dict[int, tuple[int, str]] = {}  # col_idx -> (remaining_rows, content)

        # Only collect direct child <tr> elements (via <tbody> if present)
        # to avoid mixing rows from nested tables into the parent grid
        tr_nodes: list = []
        for child in self._child_nodes(node):
            if child.tag == "tr":
                tr_nodes.append(child)
            elif child.tag == "tbody":
                tr_nodes.extend(c for c in self._child_nodes(child) if c.tag == "tr")
        if not tr_nodes:
            return []

        for tr in tr_nodes:
            row: list[str] = []
            cells = [child for child in self._child_nodes(tr) if child.tag in {"th", "td"}]
            cell_iter = iter(cells)
            col_idx = 0

            # First: consume rowspan entries from previous rows
            while col_spans:
                # Find the lowest col_idx in col_spans
                min_col = min(col_spans.keys())
                if min_col != col_idx:
                    # No rowspan at this col, proceed to consume a real cell
                    break
                remaining, content = col_spans[col_idx]
                if len(row) < MAX_COLS:
                    row.append(content)
                del col_spans[col_idx]
                if remaining > 1:
                    col_spans[col_idx] = (remaining - 1, content)
                col_idx += 1
                if col_idx >= MAX_COLS:
                    break

            # Consume actual cells
            for cell in cell_iter:
                if col_idx >= MAX_COLS:
                    break
                # Skip over col_spans that occupy columns before this cell
                while col_idx in col_spans:
                    remaining, content = col_spans[col_idx]
                    if len(row) < MAX_COLS:
                        row.append(content)
                    del col_spans[col_idx]
                    if remaining > 1:
                        col_spans[col_idx] = (remaining - 1, content)
                    col_idx += 1
                    if col_idx >= MAX_COLS:
                        break

                if col_idx >= MAX_COLS:
                    break

                content = self._render_cell_content(cell, source_dir=source_dir) or ""
                colspan = int(cell.attributes.get("colspan", 1) or 1)
                rowspan = int(cell.attributes.get("rowspan", 1) or 1)

                # Cap colspan to not exceed MAX_COLS
                colspan = min(colspan, MAX_COLS - col_idx)

                # Expand colspan into current row
                for _ in range(colspan):
                    if len(row) < MAX_COLS:
                        row.append(content)

                # Register rowspan for future rows
                if rowspan > 1:
                    for c in range(colspan):
                        span_col = col_idx + c
                        if span_col < MAX_COLS:
                            col_spans[span_col] = (rowspan - 1, content)

                col_idx += colspan

            # After consuming all cells, drain remaining col_spans for this row
            while True:
                # Find next occupied col
                occupied = [c for c in col_spans if c >= col_idx]
                if not occupied or col_idx >= MAX_COLS:
                    break
                next_col = min(occupied)
                # Fill gaps with empty strings
                while col_idx < next_col and len(row) < MAX_COLS:
                    row.append("")
                    col_idx += 1
                if col_idx >= MAX_COLS:
                    break
                remaining, content = col_spans[col_idx]
                if len(row) < MAX_COLS:
                    row.append(content)
                del col_spans[col_idx]
                if remaining > 1:
                    col_spans[col_idx] = (remaining - 1, content)
                col_idx += 1

                # Skip completely empty rows
            if row:
                grid.append(row)

        if not grid:
            return []

        # Determine max_cols and pad rows
        max_cols = max(len(r) for r in grid)
        if max_cols > MAX_COLS:
            log.warning("Table grid exceeds %d columns (%d), truncating", MAX_COLS, max_cols)
            max_cols = MAX_COLS

        for r in grid:
            while len(r) < max_cols:
                r.append("")
            if len(r) > max_cols:
                del r[max_cols:]

        return grid

    @staticmethod
    def _transpose_grid(grid: list[list[str]], header_row_count: int = 1) -> list[list[str]]:
        """Transpose a 2D grid, merging multi-row headers with ' \u2192 ' separator."""
        if not grid:
            return []

        num_cols = len(grid[0])
        num_rows = len(grid)

        if header_row_count <= 0:
            # Simple transpose: result[j][i] = grid[i][j]
            return [
                [grid[i][j] for i in range(num_rows)]
                for j in range(num_cols)
            ]

        # Merge multi-row headers per column
        merged_headers: list[str] = []
        for col in range(num_cols):
            parts = []
            for row_idx in range(header_row_count):
                val = grid[row_idx][col].strip()
                if val:
                    parts.append(val)
            merged_headers.append(" \u2192 ".join(parts))

        # Data rows start after header_row_count
        data_rows = grid[header_row_count:]

        # Build transposed grid:
        # Row 0: merged header (label) | data values from each original data row
        # Column headers are original column-0 values of data rows
        result: list[list[str]] = []
        for col in range(num_cols):
            transposed_row = [merged_headers[col]]
            for data_row in data_rows:
                transposed_row.append(data_row[col] if col < len(data_row) else "")
            result.append(transposed_row)

        return result

    def _render_grid_as_table(self, grid: list[list[str]], header_row_count: int = 1) -> str:
        """Render a normalized 2D grid as a Markdown table."""
        if not grid:
            return ""

        max_cols = len(grid[0])

        def normalize_cell(cell: str) -> str:
            # Replace newlines (from <br>) with space to keep table rows atomic
            return cell.replace("\n", " ").replace("|", "\\|")

        lines: list[str] = []

        if header_row_count > 0:
            # Render header rows
            for i in range(header_row_count):
                row = grid[i]
                escaped = [normalize_cell(c) for c in row]
                while len(escaped) < max_cols:
                    escaped.append("")
                lines.append("| " + " | ".join(escaped) + " |")
            # Separator
            lines.append("| " + " | ".join(["---"] * max_cols) + " |")
            # Body rows
            for row in grid[header_row_count:]:
                escaped = [normalize_cell(c) for c in row]
                while len(escaped) < max_cols:
                    escaped.append("")
                lines.append("| " + " | ".join(escaped) + " |")
        else:
            # No header — treat all rows as body, add empty header
            lines.append("| " + " | ".join([""] * max_cols) + " |")
            lines.append("| " + " | ".join(["---"] * max_cols) + " |")
            for row in grid:
                escaped = [normalize_cell(c) for c in row]
                while len(escaped) < max_cols:
                    escaped.append("")
                lines.append("| " + " | ".join(escaped) + " |")

        return "\n".join(lines)

    def _render_table(self, node, source_dir: str = "") -> str:
        """Render an HTML table as a Markdown table using grid-based parsing."""
        # Build normalized grid
        grid = self._build_table_grid(node, source_dir=source_dir)
        if not grid:
            return ""

        # Detect header_row_count: count consecutive all-<th> rows
        header_row_count = 0
        for row_node in node.css("tr"):
            children = list(self._child_nodes(row_node))
            th_cells = [c for c in children if c.tag == "th"]
            td_cells = [c for c in children if c.tag == "td"]
            if th_cells and not td_cells:
                header_row_count += 1
            else:
                break

        # Check transpose threshold
        table_options = self.config.get("table_options", {})
        transpose_threshold = table_options.get("transpose_wider_than")
        if transpose_threshold is not None and len(grid[0]) > transpose_threshold:
            grid = self._transpose_grid(grid, header_row_count)
            # After transpose, first row becomes the new header
            header_row_count = 1

        return self._render_grid_as_table(grid, header_row_count)

    # ------------------------------------------------------------------
    # Inline rendering
    # ------------------------------------------------------------------

    def _render_inline_children(self, node, source_dir: str = "") -> str:
        return self._render_inline_part_list(
            self._render_inline(child, source_dir=source_dir) for child in self._child_nodes(node)
        )

    def _render_inline_part_list(self, parts) -> str:
        return self._join_inline_parts(parts)

    def _render_inline(self, node, source_dir: str = "") -> str:
        tag = node.tag
        if tag == "-text":
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))
        if tag in {"strong", "b"}:
            text = self._render_inline_children(node, source_dir=source_dir)
            return f"**{text}**" if text else ""
        if tag in {"em", "i"}:
            text = self._render_inline_children(node, source_dir=source_dir)
            return f"*{text}*" if text else ""
        if tag == "code":
            text = node.text(deep=True, separator="", strip=False)
            if text is None:
                text = ""
            text = text.strip()
            return f"`{text}`" if text else ""
        if tag == "br":
            return "\n"
        if tag == "a":
            text = self._render_inline_children(node, source_dir=source_dir) or self._normalize_text(
                node.text(deep=True, separator=" ", strip=False)
            )
            href = self._normalize_href(node.attributes.get("href"))
            if not text:
                return ""
            if not href:
                return text
            wiki_link = self._to_markdown_link(href, text, source_dir)
            if wiki_link is not None:
                return wiki_link
            return f"[{text}]({href})"
        if tag == "img":
            return self._render_image(node)
        if tag in self._BLOCK_TAGS:
            return self._render_block(node, source_dir=source_dir)
        if not any(True for _ in self._child_nodes(node)):
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))
        return self._render_inline_children(node, source_dir=source_dir)

    def _render_image(self, node) -> str:
        src = self._normalize_href(node.attributes.get("src"))
        if not src:
            return ""
        # Skip patterns check (safety net — primary filtering in clean_html)
        for pattern in self._skip_patterns:
            if re.search(pattern, src):
                return ""
        alt = self._normalize_text(node.attributes.get("alt") or node.attributes.get("title") or "image")
        return f"![{alt}]({src})"

    # ------------------------------------------------------------------
    # Link resolution helpers
    # ------------------------------------------------------------------

    def _normalize_href(self, href: str | None) -> str | None:
        if href is None:
            return None
        normalized = href.strip()
        if not normalized:
            return None
        # Strip javascript: links → text-only rendering
        if normalized.startswith("javascript:"):
            return None
        # Wiki-specific absolutization — skip for generic HTML (empty wiki_domain)
        if self.wiki_domain:
            if normalized.startswith("about:/wiki/"):
                normalized = normalized.replace("about:/wiki/", f"https://{self.wiki_domain}/wiki/", 1)
            elif normalized.startswith("/wiki/") or normalized.startswith("/images/"):
                normalized = f"https://{self.wiki_domain}{normalized}"
            elif normalized.startswith("/") and not normalized.startswith("//"):
                # Other absolute paths → full URL
                normalized = f"https://{self.wiki_domain}{normalized}"
        elif normalized.startswith("#"):
            return normalized
        elif normalized.startswith("//"):
            normalized = f"https:{normalized}"
        elif normalized.startswith("about:blank#"):
            normalized = normalized.replace("about:blank", "", 1)
        return normalized

    def _to_markdown_link(self, href: str, text: str, source_dir: str) -> Optional[str]:
        """Convert wiki internal /wiki/... links to relative Markdown links.

        Decodes percent-encoded characters in the title before manifest lookup.
        """
        # Generic HTML path (empty wiki_domain): no wiki /wiki/ resolution
        if not self.wiki_domain:
            return None
        if not href.startswith(f"https://{self.wiki_domain}/wiki/"):
            return None
        title = href[len(f"https://{self.wiki_domain}/wiki/"):]
        title = title.split("?")[0].split("#")[0]
        # Decode percent-encoding before underscore-to-space replacement
        # (e.g. Mom%27s_Knife → Mom's_Knife → "Mom's Knife")
        title = unquote(title)
        title = title.replace("_", " ")
        if title.startswith(("File:", "Category:", "Template:", "Talk:", "Special:", "Help:")):
            return None
        # Follow redirect if applicable
        if title in self._redirect_map:
            title = self._redirect_map[title]
        target = self.title_to_path.get(title)
        if target is None:
            target = self.title_to_path.get(title.replace(" ", "_"))
        if target is None:
            return None
        target_dir, target_file = target
        # Encode parentheses in file path to prevent Markdown link parsing issues
        def _encode_parens(s: str) -> str:
            """Encode ( and ) but avoid double-encoding %28/%29."""
            s = s.replace("%28", "\x00LEFT\x00").replace("%29", "\x00RIGHT\x00")
            s = s.replace("(", "%28").replace(")", "%29")
            s = s.replace("\x00LEFT\x00", "%28").replace("\x00RIGHT\x00", "%29")
            return s

        if target_dir == source_dir:
            return f"[{text}]({_encode_parens(target_file)})"
        source_path = source_dir.replace("/", os.sep) if source_dir else "."
        target_path = os.path.join(target_dir.replace("/", os.sep), target_file) if target_dir else target_file
        rel = os.path.relpath(target_path, source_path).replace(os.sep, "/")
        return f"[{text}]({_encode_parens(rel)})"

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _join_inline_parts(self, parts) -> str:
        result = ""
        for part in parts:
            if not part:
                continue
            if part == "\n":
                result = result.rstrip() + "\n"
                continue
            if not result or result.endswith(("\n", " ")):
                result += part
                continue
            if part.startswith(("\n", ".", ",", ";", ":", "!", "?", ")", "]")):
                result += part
                continue
            result += f" {part}"
        return result.strip()

    def _normalize_text(self, text: str | None) -> str:
        if text is None:
            return ""
        collapsed = re.sub(r"\s+", " ", text)
        return collapsed.strip()

    def _has_block_children(self, node) -> bool:
        return any(child.tag in self._BLOCK_TAGS for child in self._child_nodes(node))

    @staticmethod
    def _child_nodes(node):
        child = node.child
        while child is not None:
            yield child
            child = child.next


# ------------------------------------------------------------------
# Public API — standalone function for external callers
# ------------------------------------------------------------------

def convert_html_to_markdown(
    html: str,
    wiki_domain: str,
    extraction_config: dict | None = None,
) -> str:
    """Convert HTML to Markdown using HtmlToMarkdownConverter.

    Convenience wrapper for external callers (e.g. sample_converter.py)
    that do not need to manage a converter instance.

    Args:
        html: Raw HTML string to convert.
        wiki_domain: Wiki domain (e.g. "bindingofisaacrebirth.wiki.gg").
        extraction_config: Optional extraction config dict from strategy.

    Returns:
        Markdown string.
    """
    converter = HtmlToMarkdownConverter(
        wiki_domain=wiki_domain,
        extraction_config=extraction_config,
    )
    return converter.convert_body(html)

