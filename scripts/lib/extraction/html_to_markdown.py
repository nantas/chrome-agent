"""HTML to Markdown converter with table support.

Extracted from the Nintendo Developer Portal crawl (``/tmp/nintendo-rebuild/rebuild_md_v2.py``)
and generalised for reuse as a Pipeline extraction utility.

Key capabilities:
  - rowspan / colspan propagation in HTML tables → Markdown tables
  - Nested table flattening (inner tables collapsed to single-line escaped-pipe text)
  - Image capture / restoration with boilerplate filtering
  - Navigation table and breadcrumb removal
  - Pipe character (``|``) escaping in table cells
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Table conversion helpers
# ---------------------------------------------------------------------------

def _convert_all_tables(
    html: str,
    convert_fn: callable,
    tbl_placeholders: Dict[str, str],
    tbl_idx: List[int],
) -> str:
    """Convert all ``<table>`` blocks, handling nesting via depth counting.

    Inner tables are extracted and replaced *first* (depth-first), so outer
    table processing sees placeholders (``__TBL_N__``) instead of raw nested
    HTML.  ``convert_fn`` receives a match-like object with a ``.group(0)``
    returning the full table HTML string.
    """
    chars: List[str] = list(html)
    i = 0
    while i < len(chars):
        s = "".join(chars[i:])
        start = s.find("<table")
        if start == -1:
            break
        start += i
        # Find matching </table> by depth counting
        depth = 1
        pos = start + 6
        while pos < len(chars) and depth > 0:
            s2 = "".join(chars[pos:])
            next_open = s2.find("<table")
            next_close = s2.find("</table>")
            if next_close == -1:
                break
            next_open = next_open + pos if next_open >= 0 else -1
            next_close = next_close + pos
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 6
            else:
                depth -= 1
                if depth == 0:
                    table_html = "".join(chars[start : next_close + 8])
                    replacement = convert_fn(
                        type("M", (), {"group": lambda self, n=0, t=table_html: t})()
                    )
                    chars[start : next_close + 8] = list(replacement)
                    pos = start + len(replacement)
                else:
                    pos = next_close + 8
        i = pos
    return "".join(chars)


def _convert_table(
    table_html: str,
    tbl_placeholders: Dict[str, str],
    tbl_idx: List[int],
) -> str:
    """Convert a single ``<table>`` HTML block to a Markdown table string.

    Handles rowspan propagation, colspan spanning, nested table flattening
    (via ``tbl_placeholders``), and pipe character escaping.
    """
    tr_blocks = re.findall(
        r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE
    )
    if not tr_blocks:
        return ""

    # First pass: determine max columns
    max_cols = 0
    for tr_html in tr_blocks:
        col_count = 0
        for _m_cell in re.finditer(r"<(th|td)([^>]*?)>", tr_html, re.IGNORECASE):
            attrs = _m_cell.group(2)
            cm = re.search(r'colspan\s*=\s*["\']?(\d+)', attrs)
            col_count += int(cm.group(1)) if cm else 1
        max_cols = max(max_cols, col_count)
    if max_cols == 0:
        return ""

    # Build rows with rowspan propagation
    rowspan_state: Dict[int, int] = {}  # col -> remaining rows
    rows: List[List[str]] = []

    for tr_html in tr_blocks:
        # Decrement rowspan from PREVIOUS rows FIRST
        for c in list(rowspan_state.keys()):
            rowspan_state[c] -= 1
            if rowspan_state[c] <= 0:
                del rowspan_state[c]

        cells = re.findall(
            r"<(th|td)([^>]*?)>(.*?)</\1>", tr_html, re.DOTALL | re.IGNORECASE
        )
        if not cells:
            continue

        all_cells: List[Tuple[str, int, int]] = []
        for _tag, attrs, content in cells:
            cell_text = re.sub(r"<[^>]+>", " ", content)
            cell_text = re.sub(r"\s+", " ", cell_text).strip()
            # Escape pipe characters to preserve Markdown table structure
            cell_text = cell_text.replace("|", "\\|")
            # Escape nested table placeholders
            for k, v in list(tbl_placeholders.items()):
                if k in cell_text:
                    flat = v.replace("|", "\\|").replace("\n", " ")
                    cell_text = cell_text.replace(k, flat)
                    del tbl_placeholders[k]  # consumed
            cm = re.search(r'colspan\s*=\s*["\']?(\d+)', attrs)
            colspan = int(cm.group(1)) if cm else 1
            rm = re.search(r'rowspan\s*=\s*["\']?(\d+)', attrs)
            rowspan = int(rm.group(1)) if rm else 1
            all_cells.append((cell_text, colspan, rowspan))

        # Place cells, skipping columns occupied by rowspan from previous rows
        row_cells = [""] * max_cols
        cell_idx = 0
        col = 0
        while cell_idx < len(all_cells) and col < max_cols:
            if rowspan_state.get(col, 0) > 0:
                col += 1
                continue
            text, colspan, rowspan = all_cells[cell_idx]
            row_cells[col] = text
            if rowspan > 1:
                rowspan_state[col] = rowspan
            col += colspan
            cell_idx += 1

        rows.append(row_cells)

    if not rows:
        return ""

    # Build Markdown table
    md_lines: List[str] = []
    for i, row in enumerate(rows):
        md_lines.append("| " + " | ".join(row) + " |")
        if i == 0:
            md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    key = "__TBL_{}__".format(tbl_idx[0])
    tbl_idx[0] += 1
    tbl_placeholders[key] = "\n\n" + "\n".join(md_lines) + "\n\n"
    return key


# ---------------------------------------------------------------------------
# Image handling
# ---------------------------------------------------------------------------

def _capture_images(html: str) -> Tuple[str, Dict[str, str]]:
    """Replace ``<img>`` tags with placeholders and return the placeholder map.

    Template boilerplate images (``noscript.svg``, ``template/img/*``) are
    discarded rather than preserved.
    """
    img_map: Dict[str, str] = {}
    img_idx = [0]

    def _capture(m: re.Match) -> str:
        tag = m.group(0)
        sm = re.search(r'src="([^"]*)"', tag)
        if not sm:
            return ""
        src = sm.group(1)
        # Discard template / boilerplate images
        if "noscript" in src.lower() or "template/img" in src.lower():
            return ""
        am = re.search(r'alt="([^"]*)"', tag)
        tm = re.search(r'title="([^"]*)"', tag)
        alt = am.group(1) if am else (tm.group(1) if tm else "Image")
        key = "__IMG_{}__".format(img_idx[0])
        img_idx[0] += 1
        img_map[key] = "![{}]({})".format(alt, src)
        return key

    html = re.sub(r"<img[^>]*/?>", _capture, html, flags=re.IGNORECASE)
    return html, img_map


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def html_to_markdown(html: str) -> str:
    """Convert an HTML string to Markdown.

    Steps (in order):
      1. Remove navigation tables (``page_nav`` class) and breadcrumb divs.
      2. Convert content tables to Markdown (rowspan/colspan/nesting).
      3. Remove ``<script>``, ``<style>``, ``<noscript>`` blocks.
      4. Capture images (preserving ``src``, discarding boilerplate).
      5. Convert structural HTML elements to Markdown equivalents.
      6. Strip remaining tags and decode HTML entities.
      7. Restore table and image placeholders.
      8. Clean whitespace and boilerplate artifacts.
    """
    # Step 0: Remove navigation tables and breadcrumbs
    html = re.sub(
        r'<table[^>]*class="[^"]*page_nav[^"]*"[^>]*>.*?</table>',
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r'<div[^>]*class="breadcrumb"[^>]*>.*?</div>',
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Step 1: Convert tables (only if <table> is present)
    tbl_placeholders: Dict[str, str] = {}
    tbl_idx = [0]

    if "<table" in html:

        def _table_convert(m_like):
            return _convert_table(m_like.group(0), tbl_placeholders, tbl_idx)

        html = _convert_all_tables(html, _table_convert, tbl_placeholders, tbl_idx)

    # Step 2: Remove noise tags
    html = re.sub(
        r"<(script|style|noscript)[^>]*>.*?</\1>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"</?(colgroup|thead|tbody|tfoot|col)[^>]*>",
        "",
        html,
        flags=re.IGNORECASE,
    )

    # Step 3: Capture images
    html, img_map = _capture_images(html)

    # Step 4: Convert structural elements
    for i in range(6, 0, -1):
        html = re.sub(
            r"<h{}[^>]*>(.*?)</h{}>".format(i, i),
            r"\n\n{} \1\n\n".format("#" * i),
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
    html = re.sub(
        r"<p[^>]*>(.*?)</p>",
        r"\n\n\1\n\n",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(
        r"<(strong|b)[^>]*>(.*?)</\1>",
        r"**\2**",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<(em|i)[^>]*>(.*?)</\1>",
        r"*\2*",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r"[\2](\1)",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<li[^>]*>(.*?)</li>",
        r"- \1\n",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<pre[^>]*>(.*?)</pre>",
        r"\n```\n\1\n```\n",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<code[^>]*>(.*?)</code>",
        r"`\1`",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<select[^>]*>.*?</select>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r"<option[^>]*>.*?</option>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Strip remaining HTML tags
    html = re.sub(r"<[^>]+>", "", html)

    # Decode entities
    for entity, char in [
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&apos;", "'"),
        ("&nbsp;", " "),
        ("&#39;", "'"),
        ("&copy;", "\u00a9"),
    ]:
        html = html.replace(entity, char)

    # Step 5: Restore tables and images
    for k, v in tbl_placeholders.items():
        html = html.replace(k, v)
    for k, v in img_map.items():
        html = html.replace(k, "\n\n{}\n\n".format(v))

    # Step 6: Clean whitespace
    html = re.sub(r"\n{4,}", "\n\n\n", html)
    html = re.sub(r" {2,}", " ", html)
    html = re.sub(r"\n\|\s*\|\s*\|\s*\n", "\n", html)
    html = re.sub(r"\n+CONFIDENTIAL\n*", "", html)
    html = re.sub(
        r"\n+\[[^\]]+\]\([^)]+\.md\) > \[[^\]]+\]\([^)]+\.md\)\n*$",
        "",
        html,
    )
    html = re.sub(
        r"\n*\| \n*\[<<.*?\n*\| \[.*?>>.*?\n*\| \n*",
        "\n",
        html,
    )

    return html.strip()
