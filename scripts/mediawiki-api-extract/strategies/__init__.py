"""Strategy protocols and implementations for MediaWiki API extraction.

This package provides both the protocol definitions and concrete implementations.
Import from here for backward compatibility:
    from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter, AllPagesDiscoveryStrategy
"""

import json
import logging
import os
import re
from typing import Optional, Protocol, runtime_checkable

log = logging.getLogger("mediawiki-api-extract")


# ===========================================================================
# Protocol definitions
# ===========================================================================

@runtime_checkable
class DiscoveryStrategy(Protocol):
    @property
    def required_capabilities(self) -> set[str]: ...

    def discover_pages(self, client, strategy: dict) -> list[dict]: ...

    def discover_categories(self, client, page_titles: list[str]) -> dict[str, list[str]]: ...

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None) -> str: ...

    def fetch_list_pages(self, client, list_pages: dict[str, str]) -> dict[str, str]: ...


@runtime_checkable
class ContentAcquisitionStrategy(Protocol):
    @property
    def required_capabilities(self) -> set[str]: ...

    def fetch_page_content(self, client, title: str, strategy: dict) -> dict: ...


@runtime_checkable
class LinkResolver(Protocol):
    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str: ...

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str: ...


@runtime_checkable
class TemplateProcessor(Protocol):
    def extract_frontmatter(self, wikitext: str, fields: list[str]) -> dict: ...

    def expand_templates(self, text: str, template_map: dict[str, str]) -> tuple[str, list[str]]: ...

    def remove_infobox(self, wikitext: str, fields: list[str]) -> str: ...

    def clean_remaining_templates(self, text: str) -> str: ...


@runtime_checkable
class ListPageAssembler(Protocol):
    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: Optional[str], frontmatter_fields: list[str],
                       domain: str) -> str: ...


# ===========================================================================
# Semantic Directory Mapping
# ===========================================================================

def title_to_filepath(title: str, ns: int) -> tuple[str, str]:
    """Map a wiki page title to (target_directory, target_filename)."""
    slug = title.replace(" ", "_").replace(":", "_").replace("/", "_")
    if ns == 14:
        name = title.removeprefix("Category:")
        dir_name = name.replace(" ", "_").replace(":", "_").replace("/", "_")
        return (dir_name, "index.md")
    elif ns == 3000:
        name = title.removeprefix("Slay the Spire 2:")
        slug = name.replace(" ", "_").replace(":", "_").replace("/", "_")
        return ("Slay_the_Spire_2", f"{slug}.md")
    else:
        return ("", f"{slug}.md")


# ===========================================================================
# L6 Validation layer
# ===========================================================================

def validate_links(output_dir: str) -> list[dict]:
    broken = []
    link_pattern = re.compile(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)')
    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for match in link_pattern.finditer(content):
                display = match.group(1)
                path_val = match.group(2)
                if path_val.startswith("http") or path_val.startswith("#"):
                    continue
                target = os.path.normpath(os.path.join(os.path.dirname(filepath), path_val))
                if not os.path.exists(target):
                    broken.append({
                        "file": os.path.relpath(filepath, output_dir),
                        "display": display,
                        "target": path_val,
                        "resolved": os.path.relpath(target, output_dir) if os.path.isabs(target) else target,
                    })
    return broken


def validate_content_integrity(output_dir: str) -> list[dict]:
    empty = []
    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            body = content
            if body.startswith("---"):
                end = body.find("\n---", 3)
                if end >= 0:
                    body = body[end + 4:].strip()
            body = re.sub(r'^#+\s.*$', '', body, flags=re.MULTILINE).strip()
            if not body:
                empty.append({
                    "file": os.path.relpath(filepath, output_dir),
                    "reason": "empty_or_frontmatter_only",
                })
    return empty


def validate_images(output_dir: str, client=None) -> list[dict]:
    unavailable = []
    image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    images_to_check: dict[str, list[str]] = {}

    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for match in image_pattern.finditer(content):
                url = match.group(2)
                if url.startswith("http"):
                    images_to_check.setdefault(url, []).append(os.path.relpath(filepath, output_dir))

    if client:
        file_names = []
        url_to_name = {}
        for url in images_to_check:
            if "Special:Redirect/file/" in url:
                name = url.split("Special:Redirect/file/")[-1]
                name = name.split("?")[0]
                file_names.append(f"File:{name}")
                url_to_name[url] = f"File:{name}"
            else:
                name = url.split("/")[-1]
                if name:
                    file_names.append(f"File:{name}")
                    url_to_name[url] = f"File:{name}"

        batch_size = 50
        unavailable_names = set()
        for i in range(0, len(file_names), batch_size):
            batch = file_names[i:i + batch_size]
            try:
                data = client.query(titles="|".join(batch), prop="imageinfo", iiprop="url|size")
                pages = data.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    if "missing" in pinfo:
                        unavailable_names.add(pinfo.get("title", ""))
                    elif not pinfo.get("imageinfo"):
                        unavailable_names.add(pinfo.get("title", ""))
            except Exception as e:
                log.warning("Image validation API query failed for batch %d-%d: %s", i, i + batch_size, e)

        for url, files in images_to_check.items():
            name = url_to_name.get(url)
            if name and name in unavailable_names:
                unavailable.append({"url": url, "files": files, "reason": "api_missing"})
    else:
        for url, files in images_to_check.items():
            unavailable.append({"url": url, "files": files, "reason": "unchecked_external"})

    return unavailable


def run_validation(output_dir: str, client=None) -> dict:
    report = {
        "broken_links": validate_links(output_dir),
        "empty_content": validate_content_integrity(output_dir),
        "unavailable_images": validate_images(output_dir, client),
    }
    report_path = os.path.join(output_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info("Validation report saved to %s", report_path)
    log.info("L6: %d broken links, %d empty files, %d unavailable images",
             len(report["broken_links"]), len(report["empty_content"]), len(report["unavailable_images"]))
    return report


# ===========================================================================
# Re-exports from sub-modules (backward compatibility)
# ===========================================================================

from .discovery import AllPagesDiscoveryStrategy, CategoryMembersDiscoveryStrategy
from .acquisition import WikitextOnlyAcquisitionStrategy, HybridAcquisitionStrategy, HtmlRenderedAcquisitionStrategy
from .link_resolver import ExactTitleLinkResolver, ShortNameLinkResolver
from .template import SimpleSubstitutionTemplateProcessor, StructuredTemplateProcessor, FandomInfoboxTemplateProcessor
from .list_assembler import FrontmatterDrivenListPageAssembler, HybridListPageAssembler

# Re-export converters for backward compatibility
from ..converters.html_to_markdown import HtmlToMarkdownConverter
from ..converters.wikitext_to_md import (
    convert_wikitext_to_markdown,
    convert_wikitable_to_markdown,
    _split_templates,
    _replace_dpl_template,
    _split_template_args,
)
from ..converters.card_stats import extract_card_stats, split_card_list_pages
