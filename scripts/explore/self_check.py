from __future__ import annotations
"""SelfCheck — S1-S12 checks for sample conversion quality + auto-remediation loop."""

import copy
import json
import re
from typing import Optional

from bs4 import BeautifulSoup

FIXABLE_ISSUES = {
    "base64_residue",
    "space_normalization",
    "link_resolution",
    "image_wrapper",
    "table_class_missing",
    # New fixable types (S1-S12 upgrade)
    "relative_image_url",
    "relative_link",
    "infobox_html_residue",
    "section_loss",
    "nav_leak",
    "youtube_title",
    "id_navigation_leak",
}

_FIX_TO_CLEANUP = {
    "link_resolution": "unwrap_image_wrappers",
    "image_wrapper": "unwrap_image_wrappers",
    "table_class_missing": "strip_fandom_infobox_tables",
    "edit": "strip_edit_links",
    "ambox": "convert_ambox_to_text",
}

_FIX_TO_NORMALIZATION = {
    "space_normalization": "fix_spaces",
}

def _markdown_links(markdown: str) -> list[dict]:
    """Read inline Markdown destinations with balanced parentheses and escapes."""
    links = []
    pattern = re.compile(r'(!?)\[((?:\\.|[^\]\\])*)\]\(')
    for match in pattern.finditer(markdown):
        start = match.end()
        depth, end, escaped = 1, start, False
        while end < len(markdown):
            char = markdown[end]
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if depth:
            continue
        destination = markdown[start:end].strip()
        if destination.startswith('<') and '>' in destination:
            destination = destination[1:destination.index('>')]
        else:
            destination = re.split(r'\s+[\"\']', destination, maxsplit=1)[0]
        links.append({'image': bool(match[1]), 'label': match[2],
                      'url': re.sub(r'\\(.)', r'\1', destination),
                      'start': match.start(), 'end': end + 1})
    return links


def _source_url(url: str, context: dict) -> str:
    from urllib.parse import urljoin
    from html import unescape
    return urljoin(context.get('base_url', ''), unescape(url))


def build_source_context(html: str, extraction: dict, *, input_scope: str,
                         source_url: str = '') -> dict:
    """Capture original source regions without invoking renderer/preprocessor."""
    context = {'raw_html': html, 'input_scope': input_scope, 'extraction': extraction,
               'base_url': extraction.get('image_handling', {}).get('base_url') or source_url,
               'error': None}
    if not html:
        context['error'] = 'source_unavailable'
        return context
    soup = BeautifulSoup(html, 'html.parser')
    selector = extraction.get('selectors', {}).get('content')
    try:
        if input_scope == 'content_fragment':
            body = soup
        elif input_scope == 'full_document':
            body = soup.select_one(selector) if selector else (soup.body or soup)
        else:
            context['error'] = 'source_scope_unknown'
            return context
        if body is None:
            context['error'] = 'content_selector_no_match'
            return context
        infobox = extraction.get('infobox', {})
        boxes = soup.select(infobox.get('selector', 'aside.portable-infobox')) if infobox.get('enabled') else []
        regions = [body] + boxes
        included = {id(node) for region in regions for node in [region, *region.descendants]}
        selectors = list(extraction.get('cleanup_selectors', []))
        # Explicit removal policy, not a replay of the transformation result.
        cleanup = extraction.get('cleanup', [])
        policy = {
            'strip_edit_links': '.mw-editsection',
            'strip_footer': '#catlinks, #mw-hidden-catlinks, .printfooter, .mw-footer, #footer',
            'strip_category_links': '#catlinks, .mw-normal-catlinks, #mw-hidden-catlinks, .catlinks, [class*=category], [id*=catlinks]',
            'strip_skip_links': '.skip-link, [class*=skip-to], #jump-to-nav, a[href^="#mw-"]',
            'strip_fandom_infobox_tables': 'table.item-table-header, table.item-table-body, table.item-table-description, table.item-table-appearance, table.infobox-table, table.portable-infobox',
        }
        selectors.extend(value for key, value in policy.items() if key in cleanup)
        excluded = {id(node) for sel in selectors for region in soup.select(sel)
                    for node in [region, *region.descendants]}
        # Infobox extraction happens before body cleanup and is separately retained.
        box_nodes = {id(node) for box in boxes for node in [box, *box.descendants]}
        retained = included - (excluded - box_nodes)
        context.update(soup=soup, body=body, retained=retained, excluded=excluded)
    except Exception as exc:
        context['error'] = f'source_scope_invalid: {exc}'
    return context


def _s1_source_images(markdown: str, context: dict, skip_patterns=None) -> dict:
    from collections import Counter
    if context.get('error'):
        return {'check': 'S1', 'status': 'skip' if context['error'] in {'source_unavailable', 'source_scope_unknown'} else 'fail',
                'detail': context['error']}
    rules = context['extraction']
    patterns = skip_patterns if skip_patterns is not None else rules.get('image_filtering', {}).get('skip_patterns', [])
    lazy = rules.get('lazyload', {})
    expected = Counter()
    for img in context['soup'].find_all('img'):
        if id(img) not in context['retained']:
            continue
        src = img.get('src', '')
        if lazy.get('enabled') and lazy.get('placeholder_pattern', '') in src:
            src = img.get(lazy.get('real_src_attr', ''), '') or src
        elif src.startswith('data:') and img.get('data-src'):
            src = img['data-src']
        if not src or src.startswith('data:') or any(re.search(p, src) for p in patterns):
            continue
        expected[_source_url(src, context)] += 1
    images = [link for link in _markdown_links(markdown) if link['image']]
    if any(link['url'].startswith('/images/') for link in images):
        return {'check': 'S1', 'status': 'fail', 'detail': 'Relative image URLs', 'fixable_type': 'relative_image_url'}
    actual = Counter(_source_url(link['url'], context) for link in images)
    if actual == expected:
        return {'check': 'S1', 'status': 'pass', 'detail': f'{sum(actual.values())} intended images retained'}
    return {'check': 'S1', 'status': 'fail',
            'detail': f'Image multiset mismatch: missing {dict(expected - actual)}, extra {dict(actual - expected)}',
            'fixable_type': 'image_wrapper' if expected - actual else None}


def s1_image_retention(html: str, markdown: str, skip_patterns: list[str] | None = None) -> dict:
    """S1: Compare original <img> count with Markdown ![]() count.
    Upgraded: also verify all images use full URLs (no relative /images/ paths).
    """
    if not html:
        return {"check": "S1", "status": "skip", "detail": "No HTML provided"}

    skip_patterns = skip_patterns or []
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")
    valid_imgs = 0
    for img in img_tags:
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        if "data:image/gif;base64" in src and not data_src:
            continue
        # Skip images matching skip patterns
        if skip_patterns and any(re.search(p, src) for p in skip_patterns):
            continue
        valid_imgs += 1

    md_imgs = len(re.findall(r"!\[.*?\]\(.*?\)", markdown))

    # Check for relative image URLs
    relative_imgs = re.findall(r"!\[.*?\]\((/images/[^)]+)\)", markdown)
    if relative_imgs:
        return {
            "check": "S1",
            "status": "fail",
            "detail": f"Found {len(relative_imgs)} relative image URLs: {relative_imgs[:3]}",
            "fixable_type": "relative_image_url",
        }

    if md_imgs == valid_imgs:
        return {"check": "S1", "status": "pass", "detail": f"{md_imgs} images retained"}
    return {
        "check": "S1",
        "status": "fail",
        "detail": f"Expected {valid_imgs} images, found {md_imgs} in Markdown",
        "fixable_type": "image_wrapper" if md_imgs < valid_imgs else None,
    }


def s2_link_resolution(html: str, markdown: str, known_pages: set[str]) -> dict:
    """S2: Verify zero relative /wiki/ links in Markdown (upgraded)."""
    if not html:
        return {"check": "S2", "status": "skip", "detail": "No HTML provided"}

    # Check for relative links in markdown
    relative_links = re.findall(r"\[([^\]]*)\]\((/wiki/[^)]+)\)", markdown)
    if relative_links:
        paths = [url for _, url in relative_links[:5]]
        return {
            "check": "S2",
            "status": "fail",
            "detail": f"Found {len(relative_links)} relative links: {paths}",
            "fixable_type": "relative_link",
        }

    # Also check the legacy resolution (if known_pages provided)
    if known_pages:
        # Skip legacy resolution if markdown uses absolute URLs
        if re.search(r'\[([^\]]+)\]\(https?://[^/]+/wiki/', markdown):
            return {"check": "S2", "status": "pass", "detail": "Links use absolute URLs"}
        soup = BeautifulSoup(html, "html.parser")
        wiki_links = []
        for a in soup.find_all("a", href=re.compile(r"^/wiki/")):
            href = a.get("href", "")
            page_name = href[6:].split("?")[0].replace("_", " ")
            if page_name.startswith(("Special:", "File:", "Image:")):
                continue
            if page_name in known_pages:
                wiki_links.append(page_name)

        unresolved = []
        for page_name in wiki_links:
            expected = f"[{page_name}]({page_name.replace(' ', '_')}.md)"
            if expected not in markdown:
                unresolved.append(page_name)

        if not unresolved:
            return {"check": "S2", "status": "pass", "detail": f"All {len(wiki_links)} wiki links resolved"}
        return {
            "check": "S2",
            "status": "fail",
            "detail": f"Unresolved links: {', '.join(unresolved[:5])}",
            "fixable_type": "link_resolution",
        }

    return {"check": "S2", "status": "pass", "detail": "No relative links found"}


def s3_infobox_extraction(wikitext: str, markdown: str) -> dict:
    """S3: Verify infobox quality — ≥3 fields, key fields non-empty, no HTML residue."""
    has_infobox = bool(re.search(r"\{\{Infobox", wikitext, re.I))
    if not has_infobox:
        return {"check": "S3", "status": "skip", "detail": "No infobox in wikitext"}

    has_frontmatter = "has_infobox: true" in markdown
    has_section = "## Infobox" in markdown

    # Check for infobox table in markdown body
    infobox_match = re.search(
        r"(?:## Infobox.*?\n|(?:\|.*\|.*\n)+)",
        markdown,
        re.DOTALL,
    )

    # Extract infobox table rows for quality checks
    infobox_section = ""
    if "## Infobox" in markdown:
        parts = markdown.split("## Infobox")
        if len(parts) > 1:
            infobox_section = parts[1].split("\n## ")[0]

    # Count fields in infobox table
    table_rows = [l for l in infobox_section.split("\n") if l.strip().startswith("|") and "---" not in l]
    field_count = max(0, len(table_rows) - 1)  # Exclude header

    # Check for HTML residue in infobox values
    html_residue = []
    for row in table_rows:
        if re.search(r"<a\b|<img\b|<span\b|</div>", row):
            html_residue.append(row.strip()[:80])

    if html_residue:
        return {
            "check": "S3",
            "status": "fail",
            "detail": f"HTML residue in infobox: {html_residue[:2]}",
            "fixable_type": "infobox_html_residue",
        }

    if field_count < 3 and (has_frontmatter or has_section):
        return {
            "check": "S3",
            "status": "fail",
            "detail": f"Infobox has only {field_count} fields (need ≥3)",
            "fixable_type": "infobox_incomplete",
        }

    if has_frontmatter or has_section or field_count >= 3:
        return {"check": "S3", "status": "pass", "detail": f"Infobox extracted ({field_count} fields)"}

    return {
        "check": "S3",
        "status": "fail",
        "detail": "Infobox exists but not extracted to Markdown",
        "fixable_type": "infobox_mismatch",
    }


def s4_empty_content(markdown: str) -> dict:
    """S4: Verify Markdown body is non-empty."""
    body = re.sub(r"^---.*?---", "", markdown, flags=re.S, count=1).strip()
    if len(body) == 0:
        return {
            "check": "S4",
            "status": "fail",
            "detail": "Markdown body is empty",
            "fixable_type": "empty_content",
        }
    return {"check": "S4", "status": "pass", "detail": f"Body length: {len(body)} chars"}


def _visible_markdown(markdown: str) -> str:
    from html import unescape
    text = re.sub(r'(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$', '', markdown)
    text = re.sub(r'`[^`]*`', '', text)
    for link in reversed(_markdown_links(text)):
        text = text[:link['start']] + ('\ufffc' if link['image'] else link['label']) + text[link['end']:]
    text = re.sub(r'https?://[^\s)]+', '', text)
    text = re.sub(r'\\([\\*_[\]()|])', r'\1', text)
    text = re.sub(r'[*_]', '', text)
    return unescape(text)


def _source_text(context: dict) -> str:
    from bs4 import NavigableString, Comment
    blocks = {'p', 'div', 'main', 'article', 'section', 'li', 'td', 'th', 'tr',
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'ul', 'ol'}
    def visit(node):
        if isinstance(node, Comment):
            return ''
        if isinstance(node, NavigableString):
            return str(node) if id(node) in context['retained'] else ''
        if getattr(node, 'name', '') == 'img':
            return '\ufffc'
        if getattr(node, 'name', '') in {'script', 'style', 'pre', 'code'}:
            return ''
        value = ''.join(visit(child) for child in getattr(node, 'children', []))
        return '\n' + value + '\n' if getattr(node, 'name', '') in blocks else value
    return visit(context['soup'])


def _repetitions(text: str) -> list[str]:
    result = []
    pattern = re.compile(r'\b(\w+(?:[ \t]+\w+){0,3})[ \t]+\1\b')
    # Preserve block/cell boundaries: matching across unrelated blocks invents repetition.
    for block in re.split(r'[\n|]', text):
        block = re.sub(r'[ \t]+', ' ', block)
        result.extend(match[1] for match in pattern.finditer(block))
    return result


def s5_text_integrity(markdown: str, source_context: Optional[dict] = None) -> dict:
    """S5: Scan for formatting anomalies including HTML residue."""
    anomalies = []

    # Missing space around version numbers
    # Exclude: entity IDs in backticks (e.g. `5.100.1`) and multi-segment dotted numbers (e.g. 5.350.57)
    # KI-2: also strip image markdown to avoid false matches on URL hash fragments
    _scan_md = re.sub(r'!\[.*?\]\([^)]+?\)', '', markdown)
    _scan_md = re.sub(r'https?://[^\s)]+', '', _scan_md)
    _version_pattern = re.compile(
        r"(?<!`)"           # not preceded by backtick
        r"([a-z])"
        r"(\d+(?:\.\d+)?)"  # only match 1-2 segment numbers (version-like: 1.0, v2)
        r"(?![\d.])"        # not followed by more digits/dots
        r"([a-z])"
        r"(?!`)"            # not followed by backtick
    )
    if _version_pattern.search(_scan_md):
        anomalies.append("Missing space around version numbers")

    # Base64 placeholder residue
    if "data:image/gif;base64" in markdown:
        anomalies.append("Base64 placeholder residue")

    # Escape artifacts
    if r"\*\*\*" in markdown or re.search(r"\\\*+", markdown):
        anomalies.append("Escape artifacts")

    # Source occurrences form a finite budget; a typo never exempts new copies.
    from collections import Counter
    repeats = _repetitions(_visible_markdown(markdown))
    notes = []
    uncertain = bool(repeats) and (source_context is None or bool(source_context.get('error')))
    if repeats and not uncertain:
        budget = Counter(_repetitions(_source_text(source_context)))
        for repeated in repeats:
            if budget[repeated]:
                budget[repeated] -= 1
                notes.append(f"Source-existing repetition: {repeated} {repeated}")
            else:
                anomalies.append(f"Introduced repeated text: {repeated} {repeated}")

    # NEW: Raw closing HTML tags
    if re.search(r"</a>|</span>|</div>", markdown):
        anomalies.append("Raw HTML closing tags")

    # NEW: Unresolved HTML entities
    if re.search(r"&amp;|&lt;|&gt;", markdown):
        anomalies.append("Unresolved HTML entities")

    if anomalies:
        return {
            "check": "S5",
            "status": "fail",
            "detail": "; ".join(anomalies),
            "notes": notes,
            "fixable_type": "space_normalization" if "Missing space" in "; ".join(anomalies) else None,
        }
    return {"check": "S5", "status": "skip" if uncertain else "pass",
            "detail": "Repetition source evidence unavailable" if uncertain else "No introduced anomalies detected",
            "notes": notes}


def s6_table_integrity(html: str, markdown: str) -> dict:
    """S6: Compare rendered structural rows, allowing 10% deviation."""
    if not html:
        return {"check": "S6", "status": "skip", "detail": "No HTML provided"}

    soup = BeautifulSoup(html, "html.parser")
    # Collapsible tables can hold gameplay data, not just navigation. Count
    # each direct row once: descendant-row counting double counts nested tables.
    nav_classes = {"navbox", "nav-box", "nav-main", "nav-header", "nav-footer"}
    tables = [t for t in soup.find_all("table")
              if not (nav_classes & set(t.get("class") or []))]
    if not any(len(t.find_all("tr")) > 2 for t in tables):
        return {"check": "S6", "status": "skip", "detail": "No data tables in original"}
    html_rows = 0
    for table in tables:
        rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
        width = max((sum(int(c.get("colspan", 1) or 1) for c in r.find_all(["th", "td"], recursive=False)) for r in rows), default=0)
        in_header_run = True
        header_counted = False
        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells:
                continue
            # Full-width heading-only rows become standalone section headings.
            is_section = (len(cells) == 1
                          and int(cells[0].get("colspan", 1) or 1) >= width
                          and cells[0].find(re.compile(r"^h[1-6]$")) is not None)
            if is_section:
                in_header_run = True
                header_counted = False
                continue
            # A nested-table container or empty media/control row is layout,
            # not an additional textual data row. Its child tables are counted
            # separately above. Images still make an otherwise empty row data.
            direct = copy.deepcopy(row)
            for nested in direct.find_all("table"):
                nested.decompose()
            if not direct.get_text(strip=True) and direct.find("img") is None:
                in_header_run = False
                continue
            if in_header_run and all(c.name == "th" for c in cells):
                if header_counted:
                    continue
                header_counted = True
            else:
                in_header_run = False
            html_rows += 1
    md_rows = [line for line in markdown.splitlines()
               if line.strip().startswith("|")
               and not re.match(r"^\|[\s\-:|]+\|$", line.strip())]
    if html_rows == 0:
        return {"check": "S6", "status": "skip", "detail": "No data rows in original tables"}

    # Check within 10% tolerance (KI-3: MediaWiki table expansion varies)
    deviation = abs(len(md_rows) - html_rows) / html_rows
    if deviation > 0.10:
        return {
            "check": "S6",
            "status": "fail",
            "detail": f"Row deviation {deviation:.1%}: HTML={html_rows}, MD={len(md_rows)}",
            "fixable_type": "table_class_missing",
        }

    return {"check": "S6", "status": "pass", "detail": f"{len(md_rows)} rows (HTML: {html_rows}, dev: {deviation:.1%})"}


def s7_image_wrapper(markdown: str, page_type: str = "article") -> dict:
    """S7: Detect unnecessary image wrapper links."""
    wrappers = re.findall(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", markdown)

    if page_type == "gallery":
        return {"check": "S7", "status": "pass", "detail": "Gallery page — wrappers allowed"}

    if wrappers:
        return {
            "check": "S7",
            "status": "fail",
            "detail": f"Found {len(wrappers)} image wrapper links",
            "fixable_type": "image_wrapper",
        }
    return {"check": "S7", "status": "pass", "detail": "No image wrappers detected"}


# ------------------------------------------------------------------
# New checks: S8-S12
# ------------------------------------------------------------------


def s8_section_completeness(html: str, markdown: str) -> dict:
    """S8: Verify all mw-headline sections are preserved as Markdown headings."""
    if not html:
        return {"check": "S8", "status": "skip", "detail": "No HTML provided"}

    soup = BeautifulSoup(html, "html.parser")
    # Extract mw-headline texts (excluding TOC "Contents" heading)
    def plain_heading(text):
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"[*`_]", "", text)
        text = re.sub(r"\s+([,.;:!?\)])", r"\1", text)
        return re.sub(r"\s+", " ", text).strip()

    expected_sections = []
    for span in soup.find_all("span", class_="mw-headline"):
        text = plain_heading(span.get_text(" ", strip=True))
        if text and text != "Contents":
            expected_sections.append(text)

    if not expected_sections:
        return {"check": "S8", "status": "skip", "detail": "No mw-headline sections found"}

    # Extract Markdown headings
    md_headings = set()
    for line in markdown.split("\n"):
        m = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if m:
            md_headings.add(plain_heading(m.group(1)))

    # Check each expected section
    missing = []
    for section in expected_sections:
        # Check exact match or partial match (headings may have extra chars)
        found = section in md_headings or any(section in h for h in md_headings)
        if not found:
            missing.append(section)

    if len(missing) > 2:
        return {
            "check": "S8",
            "status": "fail",
            "detail": f"Missing {len(missing)} sections: {missing[:5]}",
            "fixable_type": "section_loss",
        }

    if missing:
        return {
            "check": "S8",
            "status": "fail",
            "detail": f"Missing sections: {missing}",
            "fixable_type": "section_loss",
        }

    return {"check": "S8", "status": "pass", "detail": f"All {len(expected_sections)} sections present"}


def s9_navigation_leakage(markdown: str, source_context: Optional[dict] = None) -> dict:
    """Attribute excluded navigation sequences using source label/target pairs."""
    if source_context is None or source_context.get('error'):
        return {"check": "S9", "status": "skip", "detail": "Navigation source evidence unavailable"}
    context = source_context
    def pair(label, url):
        return (re.sub(r'\s+', ' ', label).strip(), _source_url(url, context))
    from collections import Counter
    body_links = Counter(pair(a.get_text(' ', strip=True), a['href'])
                  for a in context['soup'].find_all('a', href=True) if id(a) in context['retained'])
    output = [pair(link['label'], link['url']) for link in _markdown_links(markdown) if not link['image']]
    selectors = 'nav, [role="navigation"], .mw-portlet, .vector-menu, #mw-panel, .navbox, .navigation, .toc, #toc'
    ambiguous = False
    for region in context['soup'].select(selectors):
        if id(region) in context['retained']:
            continue
        sequence = [pair(a.get_text(' ', strip=True), a['href']) for a in region.find_all('a', href=True)]
        ambiguous = ambiguous or any(item in body_links and output.count(item) > body_links[item] for item in sequence)
        exclusive = [item for item in sequence if item not in body_links and item[0]]
        # Two adjacent, source-ordered links establish a sequence rather than a topic match.
        for first, second in zip(exclusive, exclusive[1:]):
            if first != second and any(a == first and b == second for a, b in zip(output, output[1:])):
                return {"check": "S9", "status": "fail", "detail": f"Excluded navigation sequence: {first}, {second}",
                        "fixable_type": "nav_leak"}
    return {"check": "S9", "status": "skip" if ambiguous else "pass",
            "detail": "Body/navigation overlap prevents attribution" if ambiguous else "No evidenced navigation leakage"}


def s10_youtube_title_quality(markdown: str) -> dict:
    """S10: Verify YouTube links use descriptive titles, not generic 'YouTube Video'."""
    generic = re.findall(r"\[YouTube Video\s*\([^)]*\)\]\(https://www\.youtube\.com/[^)]+\)", markdown)
    all_youtube = re.findall(r"\[[^\]]*\]\(https://www\.youtube\.com/[^)]+\)", markdown)

    if not all_youtube:
        return {"check": "S10", "status": "skip", "detail": "No YouTube links found"}

    if generic:
        return {
            "check": "S10",
            "status": "fail",
            "detail": f"Found {len(generic)} generic YouTube titles",
            "fixable_type": "youtube_title",
        }

    return {"check": "S10", "status": "pass", "detail": f"{len(all_youtube)} YouTube links with titles"}


def s11_zero_relative_links(markdown: str) -> dict:
    """S11: Verify zero relative /wiki/ or /images/ link references."""
    wiki_relative = re.findall(r"\]\((/wiki/[^)]+)\)", markdown)
    images_relative = re.findall(r"\]\((/images/[^)]+)\)", markdown)
    all_relative = wiki_relative + images_relative

    if all_relative:
        return {
            "check": "S11",
            "status": "fail",
            "detail": f"Found {len(all_relative)} relative links: {all_relative[:5]}",
            "fixable_type": "relative_link",
        }

    return {"check": "S11", "status": "pass", "detail": "Zero relative links"}


def s12_infobox_semantic_quality(markdown: str) -> dict:
    """S12: Verify infobox field semantic quality."""
    # Extract infobox section
    infobox_section = ""
    if "## Infobox" in markdown:
        parts = markdown.split("## Infobox")
        if len(parts) > 1:
            infobox_section = parts[1].split("\n## ")[0]
    if not infobox_section:
        return {"check": "S12", "status": "skip", "detail": "No infobox section found"}

    issues = []

    # Check Name field
    name_match = re.search(r"\|\s*Name\s*\|\s*([^|]+)\s*\|", infobox_section)
    if name_match:
        name_val = name_match.group(1).strip()
        # camelCase without spaces
        if re.search(r"[a-z][A-Z]", name_val) and " " not in name_val:
            issues.append(("name_spacing", f"Name appears concatenated: '{name_val}'"))
        # filename as name
        if name_val.endswith((".png", ".jpg", ".gif")):
            issues.append(("name_is_filename", f"Name is a filename: '{name_val}'"))

    # Check ID fields
    id_patterns = [
        r"\|\s*(?:Collectible|Trinket|Entity)\s*ID\s*\|\s*([^|]+)\s*\|",
    ]
    for pattern in id_patterns:
        id_match = re.search(pattern, infobox_section, re.IGNORECASE)
        if id_match:
            id_val = id_match.group(1).strip()
            # ID should be digits/dots/dashes only
            if id_val and not re.match(r"^[\d.\-]+$", id_val):
                if re.search(r"\[.*\]\(.*\)", id_val) or "None" in id_val:
                    issues.append(("id_navigation_leak", f"ID has navigation text: '{id_val}'"))

    if issues:
        fixable = next((i[0] for i in issues if i[0] in FIXABLE_ISSUES), None)
        return {
            "check": "S12",
            "status": "fail",
            "detail": "; ".join(i[1] for i in issues),
            "fixable_type": fixable,
        }

    return {"check": "S12", "status": "pass", "detail": "Infobox semantic quality OK"}


# ------------------------------------------------------------------
# Run all checks
# ------------------------------------------------------------------


def run_checks(
    html: str,
    markdown: str,
    wikitext: str,
    known_pages: set[str],
    page_type: str = "article",
    wiki_domain: str = "",
    skip_patterns: list[str] | None = None,
    *, source_context: Optional[dict] = None,
) -> list[dict]:
    """Run all S1-S12 checks.

    Args:
        html: Original HTML source.
        markdown: Converted Markdown.
        wikitext: Original wikitext (for infobox detection).
        known_pages: Set of known page titles.
        page_type: Page type (article, gallery, list).
        wiki_domain: Wiki domain for URL checks.
        skip_patterns: Image skip patterns for S1.
        source_context: Original evidence from build_source_context; scope-dependent
            checks explicitly skip when omitted. Low-level s1_image_retention is
            retained for callers already supplying a known content fragment.

    Returns:
        List of check results: {check, status, detail, fixable_type?}
    """
    results = []
    results.append(_s1_source_images(markdown, source_context, skip_patterns) if source_context is not None
                   else {"check": "S1", "status": "skip", "detail": "Source scope unavailable"})
    results.append(s2_link_resolution(html, markdown, known_pages))
    results.append(s3_infobox_extraction(wikitext, markdown))
    results.append(s4_empty_content(markdown))
    results.append(s5_text_integrity(markdown, source_context))
    results.append(s6_table_integrity(html, markdown))
    results.append(s7_image_wrapper(markdown, page_type))
    results.append(s8_section_completeness(html, markdown))
    results.append(s9_navigation_leakage(markdown, source_context))
    results.append(s10_youtube_title_quality(markdown))
    results.append(s11_zero_relative_links(markdown))
    results.append(s12_infobox_semantic_quality(markdown))
    return results


def summarize(results: list[dict]) -> dict:
    """Summarize check results."""
    statuses = [r["status"] for r in results]
    passes = statuses.count("pass")
    fails = statuses.count("fail")
    skips = statuses.count("skip")

    fixable = [r for r in results if r.get("status") == "fail" and r.get("fixable_type") in FIXABLE_ISSUES]
    non_fixable = [r for r in results if r.get("status") == "fail" and r.get("fixable_type") not in FIXABLE_ISSUES]

    return {
        "total": len(results),
        "pass": passes,
        "fail": fails,
        "skip": skips,
        "overall_pass": fails == 0,
        "notes": [{"check": r["check"], "detail": note} for r in results for note in r.get("notes", [])],
        "skipped_checks": [{"check": r["check"], "detail": r.get("detail", "")} for r in results if r["status"] == "skip"],
        "fixable_failures": fixable,
        "non_fixable_failures": non_fixable,
    }


def plan_remediation(extraction_rules: dict, issues: list[dict], evidence: Optional[dict] = None,
                     validate: bool = True) -> dict:
    """Plan executable configuration changes, retaining unsupported issue evidence."""
    from scripts.lib.extraction.schema import validate_extraction

    updated = copy.deepcopy(extraction_rules)
    applied, unresolved = [], []
    errors = validate_extraction(updated) if validate else []
    if errors:
        return {"extraction": updated, "applied": [], "changed": False,
                "unresolved": [{"reason_code": "invalid_configuration", "detail": errors}],
                "errors": errors}
    for issue in sorted(issues, key=lambda item: (str(item.get("fixable_type", "")), json.dumps(item, sort_keys=True, default=str))):
        kind = issue.get("fixable_type")
        before = copy.deepcopy(updated)
        reason = None
        if kind in _FIX_TO_CLEANUP:
            updated["cleanup"] = sorted(set(updated.get("cleanup", [])) | {_FIX_TO_CLEANUP[kind]})
        elif kind in _FIX_TO_NORMALIZATION:
            updated["text_normalization"] = sorted(set(updated.get("text_normalization", [])) | {_FIX_TO_NORMALIZATION[kind]})
        elif kind == "toc":
            updated["cleanup_selectors"] = sorted(set(updated.get("cleanup_selectors", [])) | {".toc", "#toc"})
        elif kind == "base64_residue":
            lazyload = copy.deepcopy(updated.get("lazyload", {}))
            lazyload.update((evidence or {}).get("lazyload", {}))
            if all(isinstance(lazyload.get(key), str) and lazyload[key].strip()
                   for key in ("placeholder_pattern", "real_src_attr")):
                lazyload["enabled"] = True
                updated["lazyload"] = lazyload
            else:
                reason = "missing_evidence"
        else:
            reason = "unsupported_consumer"
        if reason:
            unresolved.append({"issue": copy.deepcopy(issue), "fixable_type": kind,
                               "reason_code": reason, "detail": ("Lazyload requires evidenced placeholder_pattern and real_src_attr"
                                                       if reason == "missing_evidence" else "No implemented automatic consumer for this issue")})
        elif before != updated:
            applied.append({"issue": copy.deepcopy(issue), "fixable_type": kind})
    errors = validate_extraction(updated) if validate else []
    if errors:
        return {"extraction": copy.deepcopy(extraction_rules), "applied": [], "changed": False,
                "unresolved": unresolved + [{"reason_code": "invalid_configuration", "detail": errors}],
                "errors": errors}
    return {"extraction": updated, "applied": applied, "unresolved": unresolved,
            "changed": updated != extraction_rules}


def auto_remediate(extraction_rules: dict, fixable_failures: list[dict]) -> dict:
    """Compatibility wrapper returning only the planned extraction configuration."""
    return plan_remediation(extraction_rules, fixable_failures)["extraction"]
