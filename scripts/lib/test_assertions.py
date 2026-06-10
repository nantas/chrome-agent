"""Built-in structural assertions for site sample regression tests.

These assertions are applied to converted Markdown output regardless of
golden diff results.  They guard against common conversion regressions:
  - Unresolved raw HTML tags
  - Unresolved relative links (../Pages/Page_*.html)
  - Malformed Markdown tables
"""

from __future__ import annotations

import re
from typing import List


def assert_no_raw_html_tags(md_text: str) -> None:
    """Fail if *md_text* contains unmatched HTML tags.

    Detects common container / formatting tags that indicate the converter
    left raw HTML behind.  Self-closing tags (``<br/>``, ``<img/>``) and
    inline code fences are ignored.

    Raises:
        AssertionError: With a message listing the offending tags.
    """
    # Skip content inside code fences (```...```)
    stripped = _strip_code_fences(md_text)

    # Match opening tags like <div>, <span>, <table>, etc.
    pattern = re.compile(
        r"<(?P<tag>div|span|table|tr|td|th|ul|ol|li|p|br|hr|img|a|strong|em|b|i|"
        r"h[1-6]|section|article|header|footer|nav|main|pre|code|blockquote)"
        r"(?:\s[^>]*)?/?>",
        re.IGNORECASE,
    )
    # Filter out self-closing and void elements that are acceptable
    void_tags = {"br", "hr", "img"}
    matches = []
    for m in pattern.finditer(stripped):
        tag = m.group("tag").lower()
        if tag in void_tags:
            continue
        # Allow <br> and <br/> as they're common in markdown
        if tag == "br":
            continue
        matches.append(m.group(0))

    # Also check for unclosed angle-bracket patterns that are clearly HTML
    html_block_pattern = re.compile(r"</?(?:div|span|table|section|article|header|footer|nav)\b[^>]*>", re.IGNORECASE)
    for m in html_block_pattern.finditer(stripped):
        tag_text = m.group(0)
        if tag_text not in matches:
            matches.append(tag_text)

    if matches:
        unique = sorted(set(matches))
        raise AssertionError(
            f"Found {len(matches)} raw HTML tag(s) in converted output:\n"
            + "\n".join(f"  {t}" for t in unique[:20])
        )


def assert_links_resolved(md_text: str) -> None:
    """Fail if *md_text* contains unresolved relative links.

    Detects ``../Pages/Page_*.html`` patterns that indicate the link resolver
    did not convert internal references to ``.md`` paths.

    Raises:
        AssertionError: With a message listing the unresolved links.
    """
    stripped = _strip_code_fences(md_text)

    pattern = re.compile(r"\.\./Pages/Page_[^)\s\"']+\.html")
    matches = pattern.findall(stripped)

    if matches:
        unique = sorted(set(matches))
        raise AssertionError(
            f"Found {len(matches)} unresolved relative link(s) in converted output:\n"
            + "\n".join(f"  {link}" for link in unique[:20])
        )


def assert_valid_md_tables(md_text: str) -> None:
    """Fail if *md_text* contains malformed Markdown tables.

    Checks that every table-like block (lines starting with ``|``) has
    consistent column counts across all data rows.

    Raises:
        AssertionError: With a message describing the column mismatch.
    """
    stripped = _strip_code_fences(md_text)

    lines = stripped.split("\n")
    table_blocks: List[List[str]] = []
    current_block: List[str] = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("|") and stripped_line.endswith("|"):
            current_block.append(stripped_line)
        else:
            if current_block:
                table_blocks.append(current_block)
                current_block = []
    if current_block:
        table_blocks.append(current_block)

    for block_idx, block in enumerate(table_blocks):
        # Separate separator rows from data/header rows
        data_rows = []
        for row in block:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue  # separator row
            data_rows.append(cells)

        if len(data_rows) < 2:
            continue  # need at least header + one data row to validate

        col_counts = [len(row) for row in data_rows]
        if len(set(col_counts)) > 1:
            raise AssertionError(
                f"Table block {block_idx + 1} has inconsistent column counts: {col_counts}\n"
                + "\n".join(f"  Row {i}: {count} cols — {row}" for i, (row, count) in enumerate(zip(data_rows, col_counts)))
            )


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks (```...```) from *text*."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)
