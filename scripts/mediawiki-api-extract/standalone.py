"""Standalone operations — single-page fetch, reconvert, and incremental reprocess.

These functions can be used without running the full pipeline.
"""

import json
import logging
import os
from typing import Optional
from urllib.parse import unquote, urlparse

from .client import ApiClient, probe_api_endpoint
from .converters.html_to_markdown import HtmlToMarkdownConverter
from .converters.wikitext_to_md import convert_wikitext_to_markdown
from .converters.card_stats import extract_card_stats
from .strategies import (
    SimpleSubstitutionTemplateProcessor,
    ExactTitleLinkResolver,
    title_to_filepath,
)

log = logging.getLogger("mediawiki-api-extract")


def fetch_and_convert(url: str, domain: str, output: str,
                      mode: str = "html",
                      manifest_pages: Optional[list[dict]] = None,
                      extraction_config: Optional[dict] = None) -> str:
    """Fetch a single page and convert to Markdown.

    Args:
        url: Full wiki page URL (e.g. https://slaythespire.wiki.gg/wiki/Strike)
        domain: Wiki domain (e.g. slaythespire.wiki.gg)
        output: Output file path
        mode: "html" or "wikitext"
        manifest_pages: Optional manifest for link resolution

    Returns:
        Output file path on success.
    """
    api_url = probe_api_endpoint(f"https://{domain}")
    if not api_url:
        raise RuntimeError(f"Cannot reach API for {domain}")

    client = ApiClient(api_url)
    title = url.split("/wiki/")[-1] if "/wiki/" in url else url
    title = unquote(title).replace("_", " ")

    if mode == "html":
        data = client.parse(page=title, prop="text", redirects=True)
        html = data.get("parse", {}).get("text", {}).get("*", "")
        if not html:
            raise RuntimeError(f"Empty HTML for {title}")

        # Also get images
        try:
            img_data = client.parse(page=title, prop="images", redirects=True)
            images = img_data.get("parse", {}).get("images", [])
        except Exception:
            images = []

        converter = HtmlToMarkdownConverter(wiki_domain=domain, extraction_config=extraction_config)
        if manifest_pages:
            converter.build_link_index(manifest_pages)
        md_content = converter.convert_body(html, source_dir="")

        # Build frontmatter
        frontmatter = {"title": title, "source_url": url}
        if images:
            from urllib.parse import quote as url_quote
            img_name = images[0].replace(" ", "_")
            frontmatter["image"] = img_name

        # Card stats
        card_stats = extract_card_stats(html, domain=domain)

        # Assemble
        fm_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
                fm_lines.append(f'{key}: "{value}"')
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---\n")

        body = md_content.strip()
        if body and not body.startswith("#"):
            body = f"# {title}\n\n{body}"

        if card_stats:
            first_section = body.find("\n## ")
            if first_section >= 0:
                body = body[:first_section] + "\n\n" + card_stats + body[first_section:]
            else:
                body = body + "\n\n" + card_stats

        full_content = "\n".join(fm_lines) + body + "\n"

    elif mode == "wikitext":
        data = client.parse(page=title, prop="wikitext", redirects=True)
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        if not wikitext:
            raise RuntimeError(f"Empty wikitext for {title}")

        link_resolver = ExactTitleLinkResolver(domain)
        template_processor = SimpleSubstitutionTemplateProcessor()
        full_content, _, _ = convert_wikitext_to_markdown(
            wikitext, title, url, manifest_pages or [], "",
            [], {}, link_resolver, template_processor, domain
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(full_content)

    log.info("Fetched and converted %s → %s", title, output)
    return output


def reconvert_file(filepath: str, domain: str,
                   manifest_pages: Optional[list[dict]] = None,
                   extraction_config: Optional[dict] = None) -> str:
    """Re-convert an existing file using HtmlToMarkdownConverter.

    Args:
        filepath: Path to the file to reconvert
        domain: Wiki domain
        manifest_pages: Optional manifest for link resolution

    Returns:
        Converted content.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter if present
    frontmatter = {}
    body = content
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end >= 0:
            import yaml
            try:
                frontmatter = yaml.safe_load(content[3:end])
            except Exception:
                pass
            body = content[end + 4:]

    # Try to get source_url for re-fetching
    source_url = frontmatter.get("source_url", "")
    if source_url and "/wiki/" in source_url:
        # Re-fetch from API
        return fetch_and_convert(source_url, domain, filepath, mode="html", manifest_pages=manifest_pages)

    # If no source_url, just re-convert the existing HTML-like content
    converter = HtmlToMarkdownConverter(wiki_domain=domain, extraction_config=extraction_config)
    if manifest_pages:
        converter.build_link_index(manifest_pages)

    cleaned = converter.clean_html(body)
    md_content = converter.convert(cleaned, source_dir="")

    # Re-assemble with frontmatter
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
            fm_lines.append(f'{key}: "{value}"')
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---\n")

    full_content = "\n".join(fm_lines) + md_content.strip() + "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    log.info("Reconverted %s", filepath)
    return full_content


def reprocess_pages(page_titles: list[str], api_base_url: str,
                    domain: str, output_dir: str,
                    manifest_path: Optional[str] = None) -> dict:
    """Incrementally reprocess specified pages, skipping discovery.

    Args:
        page_titles: List of wiki page titles to reprocess
        api_base_url: MediaWiki API base URL
        domain: Wiki domain
        output_dir: Output directory for extracted content
        manifest_path: Path to existing manifest (optional)

    Returns:
        Stats dict with success/failure counts.
    """
    client = ApiClient(api_base_url)

    # Load manifest if available
    manifest_pages = []
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_pages = manifest.get("pages", [])

    success = 0
    failure = 0
    errors = []

    for title in page_titles:
        try:
            # Find page in manifest
            page_info = None
            for p in manifest_pages:
                if p["title"] == title:
                    page_info = p
                    break

            if page_info:
                target_dir = page_info["target_directory"]
                target_file = page_info["target_filename"]
            else:
                target_dir, target_file = title_to_filepath(title, 0)

            source_url = f"https://{domain}/wiki/{title.replace(' ', '_')}"
            output_path = os.path.join(output_dir, target_dir, target_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            fetch_and_convert(source_url, domain, output_path,
                              mode="html", manifest_pages=manifest_pages)
            success += 1
            log.info("Reprocessed: %s → %s", title, output_path)
        except Exception as e:
            failure += 1
            errors.append({"title": title, "error": str(e)})
            log.warning("Failed to reprocess %s: %s", title, e)

    stats = {
        "total": len(page_titles),
        "success": success,
        "failure": failure,
        "errors": errors,
    }
    log.info("Reprocess complete: %d/%d success", success, len(page_titles))
    return stats
