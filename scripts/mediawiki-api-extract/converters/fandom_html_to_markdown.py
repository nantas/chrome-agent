"""
Fandom MediaWiki HTML to Markdown Converter — strategy-driven conversion pipeline.

Handles Fandom-specific quirks:
- Lazy-loaded images (base64 placeholder → data-src)
- Fandom infobox visual tables (item-table-* classes)
- ambox notices
- Wiki internal link resolution
- Text normalization (space fixes, consecutive image spacing)

Requirements:
    pip install markdownify beautifulsoup4
"""

import json
import logging
import os
import re
from typing import Optional
from bs4 import BeautifulSoup, NavigableString

import markdownify

log = logging.getLogger("mediawiki-api-extract.converters.fandom")


def convert_page(
    title: str,
    html: str,
    wikitext: str,
    categories: list[str],
    sections: list[str],
    known_pages: set[str],
) -> str:
    """Convert a single Fandom MediaWiki page to Markdown.

    Args:
        title: Wiki page title
        html: Parsed HTML from action=parse response['text']['*']
        wikitext: Raw wikitext (for infobox extraction)
        categories: Page categories
        sections: Page sections
        known_pages: Set of page titles that have individual articles (for link resolution)

    Returns:
        Markdown string with YAML frontmatter
    """
    soup = BeautifulSoup(html, "html.parser")

    soup = _fix_lazyload_images(soup)
    soup = _remove_edit_sections(soup)
    soup = _remove_toc(soup)
    soup = _clean_fandom_tables(soup)
    soup = _convert_links_to_markdown(soup, known_pages)
    soup = _remove_translation_links(soup)
    soup = _clean_empty_elements(soup)

    md = _html_to_markdown(soup)
    md = _fix_spaces(md)

    infobox = _parse_infobox(wikitext)

    frontmatter = _build_frontmatter(title, categories, sections, infobox)
    infobox_section = _build_infobox_section(infobox)

    return frontmatter + infobox_section + md


def _build_frontmatter(
    title: str,
    categories: list[str],
    sections: list[str],
    infobox: Optional[dict],
) -> str:
    return f"""---
title: {title}
categories: {categories}
sections: {sections}
has_infobox: {infobox is not None}
---

"""


def _build_infobox_section(infobox: Optional[dict]) -> str:
    if not infobox:
        return ""
    lines = ["## Infobox\n", "| Field | Value |\n", "|-------|-------|\n"]
    for k, v in infobox.items():
        v = v.replace("|", "\\|")
        lines.append(f"| {k} | {v} |\n")
    lines.append("\n")
    return "".join(lines)


def _parse_infobox(wikitext: str) -> Optional[dict]:
    """Extract infobox fields from wikitext {{Infobox ...}} template."""
    match = re.search(r"\{\{(Infobox[^}]+)\}\}", wikitext, re.S)
    if not match:
        return None
    raw = match.group(1)
    parts = re.split(r"\n\s*\|", raw)
    fields = {}
    for part in parts[1:]:
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            fields[key.strip()] = val.strip()
    return fields


def _fix_lazyload_images(soup: BeautifulSoup) -> BeautifulSoup:
    """Replace base64 placeholder src with data-src for Fandom lazy-loaded images."""
    for img in soup.find_all("img"):
        src = img.get("src", "")
        data_src = img.get("data-src", "")
        if "data:image" in src and data_src:
            img["src"] = data_src
        classes = img.get("class", [])
        if isinstance(classes, list):
            img["class"] = [c for c in classes if c not in ("lazyload", "lazyloaded")]
    return soup


def _is_image_url(url: str) -> bool:
    """Check if URL points to an image file."""
    if not url:
        return False
    return url.lower().split("?")[0].endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))


def _wiki_title_to_filename(title: str) -> str:
    return title.replace(" ", "_").replace("/", "_") + ".md"


def _resolve_wiki_link(href: str, link_text: str, known_pages: set[str]) -> Optional[str]:
    """Resolve /wiki/Page_Name to markdown link. Returns None for non-wiki links."""
    if not href.startswith("/wiki/"):
        return None
    page_name = href[6:].split("?")[0]
    page_name = page_name.replace("_", " ")
    if page_name.startswith(("Special:", "File:", "Image:")):
        return None
    if page_name in known_pages:
        return f"[{link_text}]({_wiki_title_to_filename(page_name)})"
    return f"[{link_text}](https://neonabyss.fandom.com/wiki/{page_name.replace(' ', '_')})"


def _convert_links_to_markdown(soup: BeautifulSoup, known_pages: set[str]) -> BeautifulSoup:
    """Convert wiki <a> tags to markdown text nodes; unwrap image wrappers."""
    for a in list(soup.find_all("a")):
        href = a.get("href", "")
        if not href:
            a.unwrap()
            continue

        # Image-only links: unwrap <a>, keep only the <img>
        children = list(a.children)
        non_empty = [c for c in children if not (isinstance(c, str) and c.strip() == "")]
        if len(non_empty) == 1 and getattr(non_empty[0], "name", None) == "img":
            a.unwrap()
            continue

        # External image file links: unwrap
        if _is_image_url(href):
            a.unwrap()
            continue

        # External non-image links: keep as-is for markdownify
        if href.startswith("http") and not _is_image_url(href):
            continue

        # Wiki internal links
        if href.startswith("/wiki/"):
            text = a.get_text(strip=True)
            md_link = _resolve_wiki_link(href, text, known_pages)
            if md_link:
                a.replace_with(NavigableString(md_link))
            else:
                a.unwrap()
        else:
            a.unwrap()

    return soup


def _clean_fandom_tables(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove Fandom infobox visual tables; convert ambox notices to text."""
    fandom_classes = [
        "item-table-header", "item-table-body", "item-table-description",
        "item-table-appearance", "infobox-table", "portable-infobox",
    ]
    for cls in fandom_classes:
        for el in soup.find_all("table", class_=lambda x: x and cls in x):
            el.decompose()

    for el in soup.find_all("table", class_=lambda x: x and "ambox" in x):
        ambox_imgs = []
        for img in el.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            if src and "data:image" not in src:
                ambox_imgs.append(f"![{alt}]({src})")
        text = el.get_text(strip=True)
        parts = ambox_imgs + ([f"⚠️ {text}"] if text else [])
        replacement_text = " ".join(parts)
        new_p = soup.new_tag("p")
        new_p.string = replacement_text
        el.replace_with(new_p)

    return soup


def _remove_edit_sections(soup: BeautifulSoup) -> BeautifulSoup:
    for el in soup.find_all(class_="mw-editsection"):
        el.decompose()
    return soup


def _remove_toc(soup: BeautifulSoup) -> BeautifulSoup:
    for el in soup.find_all(id="toc"):
        el.decompose()
    for el in soup.find_all(class_="toc"):
        el.decompose()
    for el in soup.find_all("h2"):
        if el.get_text(strip=True) == "Contents":
            el.decompose()
    return soup


def _remove_translation_links(soup: BeautifulSoup) -> BeautifulSoup:
    for a in soup.find_all("a", href=re.compile(r"/wiki/[^/]+/tr")):
        a.decompose()
    return soup


def _clean_empty_elements(soup: BeautifulSoup) -> BeautifulSoup:
    for el in soup.find_all(["p", "div"]):
        if not el.get_text(strip=True) and not el.find("img"):
            el.decompose()
    return soup


def _html_to_markdown(soup: BeautifulSoup) -> str:
    """Convert cleaned HTML to Markdown."""
    md = markdownify.markdownify(
        str(soup),
        heading_style="atx",
        keep_inline_images_in=["td", "th", "span", "a", "div", "p", "li"],
    )
    # Clean up repeated words (e.g. "Feather Bookmark Feather Bookmark")
    md = re.sub(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+\1\b", r"\1", md)
    # Remove empty headers
    md = re.sub(r"#{1,6}\s*\n", "\n", md)
    # Normalize blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Fix bold artifacts
    md = re.sub(r"\*{3,}", "***", md)
    md = re.sub(r"\*{2}\s*\*{2}", "**", md)
    return md.strip()


def _fix_spaces(text: str) -> str:
    """Fix missing spaces from link/image stripping."""
    # version1.4.6on -> version 1.4.6 on
    text = re.sub(r"([a-zA-Z])(\d+(?:\.\d+)*)([a-zA-Z])", r"\1 \2 \3", text)
    # foo.Bar -> foo. Bar
    text = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", text)
    # ![A](x)![B](y) -> ![A](x) ![B](y)
    text = re.sub(r"(\!\[[^\]]*\]\([^)]+\))(\!\[)", r"\1 \2", text)
    return text
