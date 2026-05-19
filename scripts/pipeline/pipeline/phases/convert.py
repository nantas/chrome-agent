"""Phase Convert — read from cache and convert to Markdown."""

from __future__ import annotations

import logging
from typing import Optional

from ..registry import build_pipeline
from .. import cache as cache_mod
from ...strategies import (
    ExactTitleLinkResolver,
    SimpleSubstitutionTemplateProcessor,
)
from ...strategies import LinkResolver, TemplateProcessor
from ...strategies import HtmlToMarkdownConverter
from ...strategies import convert_wikitext_to_markdown
from ...client import PageNotFoundError

log = logging.getLogger("pipeline")


def convert_single_page(raw: dict, page_info: dict, manifest_pages: list[dict],
                        domain: str, frontmatter_fields: list[str],
                        template_map: dict[str, str],
                        link_resolver: LinkResolver,
                        template_processor: TemplateProcessor,
                        extraction_config: Optional[dict] = None) -> dict:
    """Convert a raw content dict to Markdown.

    Args:
        raw: Dict from fetch_single_page / cache with html/wikitext/images.
        page_info: Page manifest entry with title, target_directory, etc.
        manifest_pages: Full manifest page list (for link resolution).
        domain: Wiki domain.
        frontmatter_fields: Fields to extract into frontmatter.
        template_map: Template name mapping.
        link_resolver: Link resolver instance.
        template_processor: Template processor instance.
        extraction_config: Extraction rules from strategy.

    Returns:
        Result dict with title, status, content, warnings, frontmatter, rendered_html.
    """
    title = page_info["title"]
    source_dir = page_info["target_directory"]
    source_url = f"https://{domain}/wiki/{title.replace(' ', '_')}"

    # Determine conversion path:
    # 1. If cached content has a content_acquisition field, use it as primary heuristic
    # 2. Fall back to field presence detection for backward compat
    acq = raw.get("content_acquisition")
    html = raw.get("html")
    wikitext = raw.get("wikitext")

    is_html_rendered = acq == "html_rendered" or (html and not wikitext and not acq)
    is_wikitext = acq in ("wikitext_only", "hybrid_wikitext_plus_rendered") or (wikitext and not acq and not is_html_rendered)

    # HTML-rendered path
    if is_html_rendered:
        return _process_html_page(
            raw, title, source_dir, source_url, domain,
            manifest_pages, frontmatter_fields, extraction_config
        )

    # Wikitext path
    if is_wikitext and wikitext:
        md_content, warnings, frontmatter = convert_wikitext_to_markdown(
            wikitext, title, source_url, manifest_pages, source_dir,
            frontmatter_fields, template_map, link_resolver, template_processor, domain
        )

        result = {
            "title": title,
            "status": "ok",
            "content": md_content,
            "warnings": warnings,
            "frontmatter": frontmatter,
            "rendered_html": raw.get("rendered_html"),
        }

        # Inject images into frontmatter if available
        images = raw.get("images")
        if images and isinstance(images, list) and len(images) > 0:
            from urllib.parse import quote as url_quote
            first_img = images[0]
            img_name = first_img.replace(" ", "_")
            frontmatter["image"] = img_name
            img_url = f"https://{domain}/Special:Redirect/file/{url_quote(img_name, safe='')}"
            if "---" in md_content:
                end_fm = md_content.find("\n---", 3)
                if end_fm >= 0:
                    insert_pos = end_fm + 4
                    img_md = f"\n\n![{img_name}]({img_url})\n"
                    result["content"] = md_content[:insert_pos] + img_md + md_content[insert_pos:]

        return result

    # Both html and wikitext present or hybrid strategy — use HTML path
    if html and not is_wikitext:
        return _process_html_page(
            raw, title, source_dir, source_url, domain,
            manifest_pages, frontmatter_fields, extraction_config
        )

    return {"title": title, "status": "empty", "error": "No content available (html and wikitext both empty)"}


# ---------------------------------------------------------------------------

def _process_html_page(raw: dict, title: str, source_dir: str, source_url: str,
                       domain: str, manifest_pages: list[dict],
                       frontmatter_fields: list[str],
                       extraction_config: dict | None = None) -> dict:
    """Process a page using HTML-rendered content."""
    html = raw.get("html") or ""
    if not html:
        return {"title": title, "status": "empty", "error": "Empty HTML"}

    converter = HtmlToMarkdownConverter(wiki_domain=domain, extraction_config=extraction_config)
    converter.build_link_index(manifest_pages)

    md_content = converter.convert_body(html, source_dir=source_dir)

    # Build frontmatter
    frontmatter = {"title": title, "source_url": source_url}

    # Try to extract frontmatter from wikitext fallback if available
    wikitext = raw.get("wikitext")
    if wikitext:
        # Use a simple template processor for frontmatter extraction
        from ...strategies import SimpleSubstitutionTemplateProcessor
        tp = SimpleSubstitutionTemplateProcessor()
        fm = tp.extract_frontmatter(wikitext, frontmatter_fields)
        frontmatter.update(fm)

    # Inject first image into frontmatter if available
    images = raw.get("images")
    if images and isinstance(images, list) and len(images) > 0:
        from urllib.parse import quote as url_quote
        img_name = images[0].replace(" ", "_")
        frontmatter["image"] = img_name

    # Assemble final content with YAML frontmatter
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
            fm_lines.append(f'{key}: "{value.replace(chr(34), chr(92)+chr(34))}"')
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---\n")

    body = md_content.strip()
    if body and not body.startswith("#"):
        body = f"# {title}\n\n{body}"
    elif not body:
        body = f"# {title}\n"

    # Inject complete card image after title if available
    img_name = frontmatter.get("image")
    if img_name:
        img_url = f"https://{domain}/images/{img_name}"
        img_block = f"\n![{title}]({img_url})\n"
        # Insert after first heading
        first_nl = body.find("\n")
        if first_nl >= 0:
            body = body[:first_nl] + img_block + body[first_nl:]

    # Inject structured card stats if DRUID infobox was present
    from ...strategies import extract_card_stats
    card_stats = extract_card_stats(html, domain=domain)
    if card_stats:
        # Insert card stats after the first section (after first --- divider or before first ##)
        first_section = body.find("\n## ")
        if first_section >= 0:
            body = body[:first_section] + "\n\n" + card_stats + body[first_section:]
        else:
            body = body + "\n\n" + card_stats

    full_content = "\n".join(fm_lines) + body + "\n"

    return {
        "title": title,
        "status": "ok",
        "content": full_content,
        "warnings": [],
        "frontmatter": frontmatter,
        "rendered_html": html,
    }


# ---------------------------------------------------------------------------

def run_phase_convert(output_dir: str, manifest: dict, strategy: dict,
                      domain: str, repo_root: str) -> tuple[dict, dict]:
    """Execute Phase Convert: read from cache and convert to Markdown.

    No network requests are made. All input comes from local cache files.

    Args:
        output_dir: Output directory for extracted content.
        manifest: Page manifest dict with ``pages`` list.
        strategy: Strategy configuration dict.
        domain: Wiki domain.
        repo_root: Repository root path for cache directory.

    Returns:
        (results_map, stats) where results_map is title -> result dict.
    """
    platform = strategy.get("api", {}).get("platform", "mediawiki")
    api = strategy.get("api", {})
    output_config = api.get("output", {})
    frontmatter_fields = output_config.get("frontmatter_fields", [])
    template_map = output_config.get("template_map", {})
    extraction_config = strategy.get("extraction", {})

    # Build link resolver and template processor from strategy
    link_resolver_strategies = strategy.get("api", {}).get("content_profile", {}).get("link_resolver", "exact_title_match")
    template_processor_strategies = strategy.get("api", {}).get("content_profile", {}).get("template_processor", "simple_substitution")

    # Use strategy-derived instances
    strategies_obj = None
    try:
        strategies_obj = build_pipeline(strategy, domain)
    except ValueError:
        pass

    link_resolver = strategies_obj.link_resolver if strategies_obj else ExactTitleLinkResolver()
    template_processor = strategies_obj.template_processor if strategies_obj else SimpleSubstitutionTemplateProcessor()

    pages = manifest["pages"]
    results = {}
    success_count = 0
    cache_miss_count = 0
    failed_count = 0

    log.info("Phase Convert: converting %d pages from cache (platform=%s)...",
             len(pages), platform)

    for page in pages:
        title = page["title"]

        # Load from cache
        raw = cache_mod.load_page_cache(repo_root, platform, domain, title)
        if raw is None:
            cache_miss_count += 1
            results[title] = {
                "title": title,
                "status": "error",
                "error": "cache_miss",
            }
            log.warning("Cache miss for '%s' — skipping (run --phase fetch first)", title)
            continue

        # Check content_acquisition mismatch warning
        current_acq = strategy.get("api", {}).get("content_profile", {}).get("content_acquisition")
        cached_acq = raw.get("content_acquisition")
        if current_acq and cached_acq and current_acq != cached_acq:
            log.warning("Content acquisition mismatch for '%s': cached='%s', current='%s'. Conversion may be incomplete. Use --re-fetch to refresh.",
                        title, cached_acq, current_acq)

        try:
            result = convert_single_page(
                raw, page, pages, domain,
                frontmatter_fields, template_map,
                link_resolver, template_processor, extraction_config
            )
            results[title] = result
            if result["status"] == "ok":
                success_count += 1
            else:
                failed_count += 1
                log.warning("Convert failed for '%s': %s", title, result.get("error", "unknown"))
        except Exception as e:
            failed_count += 1
            results[title] = {"title": title, "status": "error", "error": str(e)}
            log.warning("Convert failed for '%s': %s", title, e)

    stats = {
        "total": len(pages),
        "success": success_count,
        "failure": failed_count,
        "cache_miss": cache_miss_count,
        "failed": failed_count,
    }
    log.info("Convert phase complete: %d total, %d converted, %d cache_miss, %d failed",
             stats["total"], success_count, cache_miss_count, failed_count)

    return results, stats
