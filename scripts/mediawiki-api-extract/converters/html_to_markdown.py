"""HTML to Markdown converter — independent of pipeline internals.

Can be imported and used standalone:
    from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter
"""

import logging
import os
import re
from typing import Optional

log = logging.getLogger("mediawiki-api-extract.converters")


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
        "blockquote", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "ol", "p", "pre", "table", "ul",
    }

    def __init__(self, wiki_domain: str, extraction_config: dict | None = None):
        self.wiki_domain = wiki_domain
        self.config = extraction_config or {}
        # Read cleanup selectors from config, fall back to class defaults
        config_cleanup = self.config.get("cleanup_selectors", [])
        self._REMOVAL_SELECTORS = tuple(config_cleanup) if config_cleanup else self._REMOVAL_SELECTORS
        self.title_to_path: dict[str, tuple[str, str]] = {}

    def build_link_index(self, manifest_pages: list[dict]):
        """Build title -> (target_directory, target_filename) index."""
        self.title_to_path = {
            p["title"]: (p["target_directory"], p["target_filename"])
            for p in manifest_pages
        }

    def clean_html(self, html: str) -> str:
        """Remove wiki UI noise and hidden elements."""
        try:
            from selectolax.parser import HTMLParser
        except ImportError:
            return self._regex_clean(html)

        parser = HTMLParser(html)

        for selector in self._REMOVAL_SELECTORS:
            for node in parser.css(selector):
                node.decompose()

        for node in parser.css('img[src*="ModuleEditIcon"]'):
            parent = node.parent
            if parent:
                parent.decompose()

        # Config-driven image filtering
        skip_patterns = self.config.get("image_filtering", {}).get("skip_patterns", [])
        for pattern in skip_patterns:
            for node in parser.css(f'img[src*="{pattern}"]'):
                node.decompose()

        for node in parser.css("[style]"):
            style = node.attributes.get("style", "")
            if "display:none" in style.replace(" ", ""):
                node.decompose()

        body = parser.body
        if body is not None:
            return body.html
        root = parser.css_first(".mw-parser-output")
        if root is not None:
            return root.html
        return parser.html

    def convert(self, html: str, source_dir: str = "") -> str:
        """Convert cleaned HTML to Markdown."""
        try:
            from selectolax.parser import HTMLParser
        except ImportError:
            return self._regex_convert(html)

        parser = HTMLParser(f'<div data-wrapper="root">{html}</div>')
        root = parser.css_first('[data-wrapper="root"]')
        if root is None:
            return ""

        rendered = self._render_blocks(self._child_nodes(root), source_dir=source_dir)
        return rendered.strip()

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
            code = node.text(deep=True, separator="", strip=False).strip("\n")
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
    # Table rendering
    # ------------------------------------------------------------------

    def _render_table(self, node, source_dir: str = "") -> str:
        rows = [self._extract_row(row, source_dir=source_dir) for row in node.css("tr")]
        rows = [row for row in rows if row]
        if not rows:
            return ""
        if self._is_simple_markdown_table(node, rows):
            header = rows[0]
            separator = ["---"] * len(header)
            table_lines = [self._markdown_table_line(header), self._markdown_table_line(separator)]
            table_lines.extend(self._markdown_table_line(row) for row in rows[1:])
            return "\n".join(table_lines)
        fallback_lines = []
        for row in rows:
            if len(row) == 2:
                fallback_lines.append(f"- **{row[0]}:** {row[1]}")
            else:
                fallback_lines.append(f"- {' | '.join(row)}")
        return "\n".join(fallback_lines)

    def _extract_row(self, row, source_dir: str = "") -> list[str]:
        cells = []
        for child in self._child_nodes(row):
            if child.tag not in {"th", "td"}:
                continue
            cells.append(self._render_inline_children(child, source_dir=source_dir) or "")
        return cells

    def _is_simple_markdown_table(self, node, rows: list[list[str]]) -> bool:
        if len(rows) < 2:
            return False
        width = len(rows[0])
        if width == 0:
            return False
        if any(len(row) != width for row in rows):
            return False
        first_row = node.css_first("tr")
        if first_row is None:
            return False
        if not any(child.tag == "th" for child in self._child_nodes(first_row)):
            return False
        for cell in node.css("th, td"):
            if cell.attributes.get("colspan") not in {None, "1"} or cell.attributes.get("rowspan") not in {None, "1"}:
                return False
        return True

    def _markdown_table_line(self, cells: list[str]) -> str:
        escaped = [cell.replace("|", "\\|") for cell in cells]
        return f"| {' | '.join(escaped)} |"

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
            text = node.text(deep=True, separator="", strip=False).strip()
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
        alt = self._normalize_text(node.attributes.get("alt") or node.attributes.get("title") or "image")
        return f"![{alt}]({src})"

    # ------------------------------------------------------------------
    # Link resolution helpers
    # ------------------------------------------------------------------

    def _normalize_href(self, href: Optional[str]) -> Optional[str]:
        if href is None:
            return None
        normalized = href.strip()
        if not normalized:
            return None
        if normalized.startswith("about:/wiki/"):
            normalized = normalized.replace("about:/wiki/", f"https://{self.wiki_domain}/wiki/", 1)
        elif normalized.startswith("/wiki/") or normalized.startswith("/images/"):
            normalized = f"https://{self.wiki_domain}{normalized}"
        elif normalized.startswith("#"):
            return normalized
        elif normalized.startswith("//"):
            normalized = f"https:{normalized}"
        elif normalized.startswith("about:blank#"):
            normalized = normalized.replace("about:blank", "", 1)
        return normalized

    def _to_markdown_link(self, href: str, text: str, source_dir: str) -> Optional[str]:
        """Convert wiki internal /wiki/... links to relative Markdown links."""
        if not href.startswith(f"https://{self.wiki_domain}/wiki/"):
            return None
        title = href[len(f"https://{self.wiki_domain}/wiki/"):]
        title = title.split("?")[0].split("#")[0]
        title = title.replace("_", " ")
        if title.startswith(("File:", "Category:", "Template:", "Talk:", "Special:", "Help:")):
            return None
        target = self.title_to_path.get(title)
        if target is None:
            target = self.title_to_path.get(title.replace(" ", "_"))
        if target is None:
            return None
        target_dir, target_file = target
        if target_dir == source_dir:
            return f"[{text}]({target_file})"
        source_path = source_dir.replace("/", os.sep) if source_dir else "."
        target_path = os.path.join(target_dir.replace("/", os.sep), target_file) if target_dir else target_file
        rel = os.path.relpath(target_path, source_path).replace(os.sep, "/")
        return f"[{text}]({rel})"

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

    def _normalize_text(self, text: str) -> str:
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
    # Regex fallbacks (when selectolax is unavailable)
    # ------------------------------------------------------------------

    def _regex_clean(self, html: str) -> str:
        html = re.sub(r'<div class="mw-editsection"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
        html = re.sub(r'<div[^>]*id="toc"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
        html = re.sub(r'<div[^>]*class="toc"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
        html = re.sub(r'<div[^>]*class="hatnote"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
        # Config-driven image filtering via regex
        skip_patterns = self.config.get("image_filtering", {}).get("skip_patterns", [])
        for pattern in skip_patterns:
            html = re.sub(rf'<img[^>]*src="[^"]*{re.escape(pattern)}[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?</\w+>', '', html, flags=re.DOTALL)
        return html

    def _regex_convert(self, html: str) -> str:
        text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        text = re.sub(r'</p>\s*<p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
