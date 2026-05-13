"""SelfCheck — S1-S7 checks for sample conversion quality + auto-remediation loop."""

import re
from typing import Optional

from bs4 import BeautifulSoup

CHECKS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]

FIXABLE_ISSUES = {
    "base64_residue",
    "space_normalization",
    "link_resolution",
    "image_wrapper",
    "table_class_missing",
}

NON_FIXABLE_ISSUES = {
    "empty_content",
    "infobox_mismatch",
    "structural_failure",
}


def s1_image_retention(html: str, markdown: str) -> dict:
    """S1: Compare original <img> count with Markdown ![]() count."""
    if not html:
        return {"check": "S1", "status": "skip", "detail": "No HTML provided"}

    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")
    valid_imgs = 0
    for img in img_tags:
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        if "data:image/gif;base64" in src and not data_src:
            continue
        valid_imgs += 1

    md_imgs = len(re.findall(r"!\[.*?\]\(.*?\)", markdown))

    if md_imgs == valid_imgs:
        return {"check": "S1", "status": "pass", "detail": f"{md_imgs} images retained"}
    return {
        "check": "S1",
        "status": "fail",
        "detail": f"Expected {valid_imgs} images, found {md_imgs} in Markdown",
        "fixable_type": "image_wrapper" if md_imgs < valid_imgs else None,
    }


def s2_link_resolution(html: str, markdown: str, known_pages: set[str]) -> dict:
    """S2: Verify internal wiki links are resolved to .md files."""
    if not html:
        return {"check": "S2", "status": "skip", "detail": "No HTML provided"}

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
        "detail": f"Unresolved links: {', '.join(unresolved)}",
        "fixable_type": "link_resolution",
    }


def s3_infobox_extraction(wikitext: str, markdown: str) -> dict:
    """S3: Verify infobox presence in frontmatter or body."""
    has_infobox = bool(re.search(r"\{\{Infobox", wikitext, re.I))
    if not has_infobox:
        return {"check": "S3", "status": "skip", "detail": "No infobox in wikitext"}

    has_frontmatter = "has_infobox: true" in markdown
    has_section = "## Infobox" in markdown

    if has_frontmatter or has_section:
        return {"check": "S3", "status": "pass", "detail": "Infobox extracted"}
    return {
        "check": "S3",
        "status": "fail",
        "detail": "Infobox exists but not extracted to Markdown",
        "fixable_type": "infobox_mismatch",
    }


def s4_empty_content(markdown: str) -> dict:
    """S4: Verify Markdown body is non-empty."""
    # Remove frontmatter
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
    """S5: Scan for formatting anomalies."""
    anomalies = []

    # Missing space around version numbers
    if re.search(r"([a-z])(\d+(?:\.\d+)*)([a-z])", markdown):
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

    if anomalies:
        return {
            "check": "S5",
            "status": "fail",
            "detail": "; ".join(anomalies),
            "fixable_type": "space_normalization" if "Missing space" in "; ".join(anomalies) else None,
        }
    return {"check": "S5", "status": "pass", "detail": "No anomalies detected"}


def s6_table_integrity(html: str, markdown: str) -> dict:
    """S6: Verify table structure preservation for list pages."""
    if not html:
        return {"check": "S6", "status": "skip", "detail": "No HTML provided"}

    soup = BeautifulSoup(html, "html.parser")
    tables = [t for t in soup.find_all("table") if len(t.find_all("tr")) > 2]

    if not tables:
        return {"check": "S6", "status": "skip", "detail": "No data tables in original"}

    # Count markdown table rows (lines starting with |)
    md_rows = [l for l in markdown.split("\n") if l.strip().startswith("|") and "---" not in l]
    if len(md_rows) >= 3:
        return {"check": "S6", "status": "pass", "detail": f"{len(md_rows)} table rows preserved"}
    return {
        "check": "S6",
        "status": "fail",
        "detail": f"Original had {len(tables)} tables but Markdown has only {len(md_rows)} rows",
        "fixable_type": "table_class_missing",
    }


def s7_image_wrapper(markdown: str, page_type: str = "article") -> dict:
    """S7: Detect unnecessary image wrapper links."""
    wrappers = re.findall(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", markdown)

    # Gallery pages may intentionally have wrapped images
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


def run_checks(
    html: str,
    markdown: str,
    wikitext: str,
    known_pages: set[str],
    page_type: str = "article",
) -> list[dict]:
    """Run all S1-S7 checks.

    Returns:
        List of check results: {check, status, detail, fixable_type?}
    """
    results = []
    results.append(s1_image_retention(html, markdown))
    results.append(s2_link_resolution(html, markdown, known_pages))
    results.append(s3_infobox_extraction(wikitext, markdown))
    results.append(s4_empty_content(markdown))
    results.append(s5_text_integrity(markdown))
    results.append(s6_table_integrity(html, markdown))
    results.append(s7_image_wrapper(markdown, page_type))
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

    updated["cleanup"] = sorted(cleanup)
    updated["text_normalization"] = sorted(normalization)
    return updated
