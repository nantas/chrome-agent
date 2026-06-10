"""Markdown link resolver — batch-convert internal HTML links to .md or full URLs.

Extracted from the Nintendo Developer Portal crawl (``/tmp/nintendo-rebuild/fix_links.py``
and ``rebuild_md_v2.py``) and generalised for reuse.

The resolver operates in two steps:

1. **Build a page mapping** by scanning ``.md`` files in the output directory
   and extracting ``> Source:`` URLs.
2. **Resolve links** — internal references (e.g. ``../Pages/Page_xxx.html``) are
   converted to relative ``.md`` filenames when the target exists in the mapping,
   or to full external URLs when it does not.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Page mapping
# ---------------------------------------------------------------------------

def build_page_mapping(output_dir: str) -> Dict[str, str]:
    """Build a mapping from URL fragments to ``.md`` filenames.

    Scans every ``.md`` file in *output_dir* and extracts the ``> Source:``
    metadata line.  The mapping key is the URL fragment (e.g.
    ``Pages/Page_123.html`` or ``title.html``) and the value is the ``.md``
    filename.

    Args:
        output_dir: Directory containing the output ``.md`` files.

    Returns:
        Dict mapping URL fragment → ``.md`` filename.
    """
    mapping: Dict[str, str] = {}
    md_dir = Path(output_dir)

    for md_path in md_dir.glob("*.md"):
        text = md_path.read_text(encoding="utf-8")
        source_match = re.search(r"> Source: (.+?)(?:\n|$)", text)
        if not source_match:
            continue
        source = source_match.group(1).strip()

        # Pages/Page_xxx.html pattern (Guide/Manual)
        page_match = re.search(r"(Pages/Page_\d+\.html)", source)
        if page_match:
            mapping[page_match.group(0)] = md_path.name
            continue

        # Generic basename pattern
        basename = source.rstrip("/").rsplit("/", 1)[-1]
        if basename and basename.endswith(".html"):
            mapping[basename] = md_path.name

    return mapping


# ---------------------------------------------------------------------------
# Link resolution
# ---------------------------------------------------------------------------

def resolve_link(
    href: str,
    mapping: Dict[str, str],
    base_web: str,
    doc_base: str,
    uses_contents: bool = True,
) -> str:
    """Resolve a single Markdown link href.

    Resolution rules (in order):

    1. Absolute URLs (``http://``, ``https://``, ``//``), anchor-only
       (``#section``), and ``javascript:`` pseudo-URLs are **passed through**
       unchanged.
    2. ``../Pages/Page_xxx.html`` → check mapping; hit → ``.md`` filename,
       miss → full URL.
    3. ``../title.html`` → full URL (title pages are typically not crawled).
    4. Other ``../``-prefixed links → check mapping for basename; miss → full URL.
    5. ``Pages/Page_xxx.html`` (no prefix) → same logic as #2.
    6. Remaining relative links → basename mapping check, then full URL.

    Args:
        href: The raw href from the Markdown link.
        mapping: URL fragment → ``.md`` filename mapping.
        base_web: Base web URL for generating full external links.
        doc_base: Document path component (e.g. ``Packages/Docs/Guides/Online_Play_Guide``).
        uses_contents: Whether pages live under a ``contents/`` path segment.

    Returns:
        Resolved href string.
    """
    # Rule 1: passthrough
    if href.startswith(("http://", "https://", "//", "#", "javascript:")):
        return href

    mid = "contents/" if uses_contents else ""
    url_base = "{}/{}/{}".format(base_web, doc_base, mid)

    # Rule 2: ../Pages/Page_xxx.html
    page_match = re.match(r"\.\./Pages/(Page_\d+\.html)", href)
    if page_match:
        page_id = "Pages/{}".format(page_match.group(1))
        if page_id in mapping:
            return mapping[page_id]
        return "{}{}".format(url_base, page_id)

    # Rule 3: ../title.html
    if href == "../title.html":
        return "{}title.html".format(url_base)

    # Rule 4: other ../ prefixed
    if href.startswith("../"):
        rest = href[3:]
        basename = rest.rsplit("/", 1)[-1]
        if basename in mapping:
            return mapping[basename]
        return "{}{}".format(url_base, rest)

    # Rule 5: Pages/Page_xxx.html (no prefix)
    page_match2 = re.match(r"Pages/(Page_\d+\.html)", href)
    if page_match2:
        page_id = "Pages/{}".format(page_match2.group(1))
        if page_id in mapping:
            return mapping[page_id]
        return "{}{}".format(url_base, page_id)

    # Rule 6: remaining relative
    if href and not href.startswith("http"):
        basename = href.rstrip("/").rsplit("/", 1)[-1]
        if basename in mapping:
            return mapping[basename]
        return "{}{}".format(url_base, href)

    return href


# ---------------------------------------------------------------------------
# Batch link fixing
# ---------------------------------------------------------------------------

def fix_all_links(
    text: str,
    mapping: Dict[str, str],
    base_web: str,
    doc_base: str,
    uses_contents: bool = True,
) -> str:
    """Fix all Markdown links in *text* using the page mapping.

    Args:
        text: Full Markdown document text.
        mapping: URL fragment → ``.md`` filename mapping.
        base_web: Base web URL for external links.
        doc_base: Document path component.
        uses_contents: Whether pages are under ``contents/``.

    Returns:
        Text with all links resolved.
    """

    def _replace_link(m: re.Match) -> str:
        label = m.group(1)
        href = m.group(2)
        new_href = resolve_link(href, mapping, base_web, doc_base, uses_contents)
        return "[{}]({})".format(label, new_href)

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", _replace_link, text)
