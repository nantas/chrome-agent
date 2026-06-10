from __future__ import annotations
"""SelfCheck — S1-S12 checks for sample conversion quality + auto-remediation loop."""

import re
from typing import Optional

from bs4 import BeautifulSoup

CHECKS = [
    "S1", "S2", "S3", "S4", "S5", "S6", "S7",
    "S8", "S9", "S10", "S11", "S12",
]

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

NON_FIXABLE_ISSUES = {
    "empty_content",
    "infobox_mismatch",
    "structural_failure",
    # New non-fixable types
    "infobox_incomplete",
    "name_spacing",
    "name_is_filename",
}

# Navigation keywords for S9
_NAV_KEYWORDS = [
    "Achievements", "Challenges", "Characters", "Bosses", "Trinkets",
    "Items", "Modes", "Curses", "Objects", "Seeds", "Effects", "Endings",
    "Collection", "Version History", "Modding", "Music",
]


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


def s5_text_integrity(markdown: str) -> dict:
    """S5: Scan for formatting anomalies including HTML residue."""
    anomalies = []

    # Missing space around version numbers
    # Exclude: entity IDs in backticks (e.g. `5.100.1`) and multi-segment dotted numbers (e.g. 5.350.57)
    # KI-2: also strip image markdown to avoid false matches on URL hash fragments
    _scan_md = re.sub(r'!\[.*?\]\([^)]+?\)', '', markdown)
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

    # Repeated link text
    if re.search(r"(\w[\w\s]{1,15}?) +\1", markdown):
        anomalies.append("Repeated link text")

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
            "fixable_type": "space_normalization" if "Missing space" in "; ".join(anomalies) else None,
        }
    return {"check": "S5", "status": "pass", "detail": "No anomalies detected"}


def s6_table_integrity(html: str, markdown: str) -> dict:
    """S6: Verify table row count within 5% tolerance."""
    if not html:
        return {"check": "S6", "status": "skip", "detail": "No HTML provided"}

    soup = BeautifulSoup(html, "html.parser")
    # Exclude navigation tables (navbox, nav-box, mw-collapsible)
    _nav_classes = {"navbox", "nav-box", "mw-collapsible", "nav-main", "nav-header", "nav-footer"}
    tables = [
        t for t in soup.find_all("table")
        if len(t.find_all("tr")) > 2 and not (_nav_classes & set(t.get("class") or []))
    ]

    if not tables:
        return {"check": "S6", "status": "skip", "detail": "No data tables in original"}

    # Count original <tr> rows (excluding header rows)
    html_rows = 0
    for table in tables:
        for tr in table.find_all("tr"):
            # Skip header rows (rows with only <th>)
            cells = tr.find_all(["th", "td"])
            if cells and all(c.name == "th" for c in cells):
                continue
            html_rows += 1

    # Count markdown table data rows
    md_rows = [
        l for l in markdown.split("\n")
        if l.strip().startswith("|") and "---" not in l and not re.match(r"^\|[\s\-:|]+\|$", l.strip())
    ]

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
    expected_sections = []
    for span in soup.find_all("span", class_="mw-headline"):
        text = span.get_text(strip=True)
        if text and text != "Contents":
            expected_sections.append(text)

    if not expected_sections:
        return {"check": "S8", "status": "skip", "detail": "No mw-headline sections found"}

    # Extract Markdown headings
    md_headings = set()
    for line in markdown.split("\n"):
        m = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if m:
            md_headings.add(m.group(1).strip())

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


def s9_navigation_leakage(markdown: str) -> dict:
    """S9: Verify navigation sidebar content has NOT leaked into Markdown."""
    lines = markdown.split("\n")
    consecutive_nav = 0
    max_consecutive = 0

    for line in lines:
        has_nav = any(kw in line for kw in _NAV_KEYWORDS)
        if has_nav:
            consecutive_nav += 1
            max_consecutive = max(max_consecutive, consecutive_nav)
        else:
            consecutive_nav = 0

    if max_consecutive >= 3:
        return {
            "check": "S9",
            "status": "fail",
            "detail": f"Found {max_consecutive} consecutive lines with nav keywords",
            "fixable_type": "nav_leak",
        }

    return {"check": "S9", "status": "pass", "detail": "No navigation leakage detected"}


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

    Returns:
        List of check results: {check, status, detail, fixable_type?}
    """
    results = []
    results.append(s1_image_retention(html, markdown, skip_patterns))
    results.append(s2_link_resolution(html, markdown, known_pages))
    results.append(s3_infobox_extraction(wikitext, markdown))
    results.append(s4_empty_content(markdown))
    results.append(s5_text_integrity(markdown))
    results.append(s6_table_integrity(html, markdown))
    results.append(s7_image_wrapper(markdown, page_type))
    results.append(s8_section_completeness(html, markdown))
    results.append(s9_navigation_leakage(markdown))
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
        "fixable_failures": fixable,
        "non_fixable_failures": non_fixable,
    }


def auto_remediate(
    extraction_rules: dict,
    fixable_failures: list[dict],
) -> dict:
    """Suggest extraction rule amendments for fixable failures.

    Returns:
        Updated extraction_rules dict.
    """
    updated = dict(extraction_rules)
    cleanup = set(updated.get("cleanup", []))
    normalization = set(updated.get("text_normalization", []))

    for failure in fixable_failures:
        fix_type = failure.get("fixable_type")
        if fix_type == "base64_residue":
            cleanup.add("fix_lazyload_images")
        elif fix_type == "space_normalization":
            normalization.add("fix_spaces")
        elif fix_type == "link_resolution":
            cleanup.add("unwrap_image_wrappers")
        elif fix_type == "image_wrapper":
            cleanup.add("unwrap_image_wrappers")
        elif fix_type == "table_class_missing":
            cleanup.add("strip_fandom_infobox_tables")
        elif fix_type == "relative_image_url":
            cleanup.add("convert_images_full_url")
        elif fix_type == "relative_link":
            cleanup.add("convert_links_full_url")
        elif fix_type == "infobox_html_residue":
            cleanup.add("use_balanced_div_matching")
        elif fix_type == "section_loss":
            cleanup.add("use_balanced_toc_removal")
        elif fix_type == "nav_leak":
            cleanup.add("remove_nav_header_sidebar")
        elif fix_type == "youtube_title":
            cleanup.add("retry_oembed_titles")
        elif fix_type == "id_navigation_leak":
            cleanup.add("extract_infobox_nav_cur")

    updated["cleanup"] = sorted(cleanup)
    updated["text_normalization"] = sorted(normalization)
    return updated
