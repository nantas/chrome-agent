"""Phase B: Content Extraction."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .client import ApiClient
from .strategies import ContentAcquisitionStrategy, HtmlRenderedAcquisitionStrategy, HtmlToMarkdownConverter, LinkResolver, TemplateProcessor
from .strategies import convert_wikitext_to_markdown

log = logging.getLogger("mediawiki-api-extract")


def process_single_page(client: ApiClient, page_info: dict, manifest_pages: list[dict],
                        domain: str, frontmatter_fields: list[str],
                        template_map: dict[str, str],
                        content_strategy: ContentAcquisitionStrategy,
                        link_resolver: LinkResolver,
                        template_processor: TemplateProcessor,
                        extraction_config: dict | None = None) -> dict:
    """Process a single page: fetch content and convert to Markdown."""
    title = page_info["title"]
    source_dir = page_info["target_directory"]
    source_url = f"https://{domain}/wiki/{title.replace(' ', '_')}"

    try:
        raw = content_strategy.fetch_page_content(client, title, {})

        # HTML-rendered path
        if isinstance(content_strategy, HtmlRenderedAcquisitionStrategy):
            return _process_html_page(
                raw, title, source_dir, source_url, domain,
                manifest_pages, frontmatter_fields, extraction_config
            )

        # Wikitext path (default)
        wikitext = raw.get("wikitext", "")
        if not wikitext:
            return {"title": title, "status": "empty", "error": "Empty wikitext"}

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
    except Exception as e:
        return {"title": title, "status": "error", "error": str(e)}


def _process_html_page(raw: dict, title: str, source_dir: str, source_url: str,
                       domain: str, manifest_pages: list[dict],
                       frontmatter_fields: list[str],
                       extraction_config: dict | None = None) -> dict:
    """Process a page using HTML-rendered content."""
    html = raw.get("html", "")
    if not html:
        return {"title": title, "status": "empty", "error": "Empty HTML"}

    converter = HtmlToMarkdownConverter(wiki_domain=domain, extraction_config=extraction_config)
    converter.build_link_index(manifest_pages)

    cleaned = converter.clean_html(html)
    md_content = converter.convert(cleaned, source_dir=source_dir)

    # Build frontmatter
    frontmatter = {"title": title, "source_url": source_url}

    # Try to extract frontmatter from wikitext fallback if available
    wikitext = raw.get("wikitext")
    if wikitext:
        # Use a simple template processor for frontmatter extraction
        from .strategies import SimpleSubstitutionTemplateProcessor
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
    from .strategies import extract_card_stats
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


def run_phase_b(client: ApiClient, manifest: dict, strategy: dict,
                rate_limit_config, domain: str,
                content_strategy: ContentAcquisitionStrategy,
                link_resolver: LinkResolver,
                template_processor: TemplateProcessor) -> tuple[dict, dict]:
    """Execute Phase B: Content Extraction.

    Returns:
        (results_map, stats) where results_map is title -> {content, status},
        and stats has success/failure counts.
    """
    api = strategy.get("api", {})
    output_config = api.get("output", {})
    frontmatter_fields = output_config.get("frontmatter_fields", [])
    template_map = output_config.get("template_map", {})

    pages = manifest["pages"]
    results = {}
    success_count = 0
    failure_count = 0
    all_warnings = []

    concurrency = rate_limit_config.concurrency if rate_limit_config else 1
    batch_delay_sec = (rate_limit_config.batch_delay_ms / 1000.0) if rate_limit_config else 1.0

    log.info("Phase B: Extracting content for %d pages (concurrency=%d, batch_delay_ms=%d)...",
             len(pages), concurrency, rate_limit_config.batch_delay_ms if rate_limit_config else 1000)

    extraction_config = strategy.get("extraction", {})

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {}
        for page in pages:
            future = executor.submit(
                process_single_page, client, page, pages,
                domain, frontmatter_fields, template_map,
                content_strategy, link_resolver, template_processor,
                extraction_config
            )
            futures[future] = page["title"]

        for future in as_completed(futures):
            title = futures[future]
            try:
                result = future.result()
                results[title] = result
                if result["status"] == "ok":
                    success_count += 1
                    if result.get("warnings"):
                        all_warnings.extend(result["warnings"])
                else:
                    failure_count += 1
                    log.warning("Page %s: %s", title, result.get("error", "unknown error"))
            except Exception as e:
                results[title] = {"title": title, "status": "error", "error": str(e)}
                failure_count += 1

            done = success_count + failure_count
            if done % 50 == 0:
                log.info("Phase B progress: %d/%d (success=%d, failure=%d)",
                         done, len(pages), success_count, failure_count)

            time.sleep(batch_delay_sec)

    stats = {
        "total": len(pages),
        "success": success_count,
        "failure": failure_count,
        "failure_rate": failure_count / len(pages) if pages else 0,
        "warnings": all_warnings,
    }
    log.info("Phase B complete: %d success, %d failure (%.1f%% failure rate)",
             success_count, failure_count, stats["failure_rate"] * 100)

    return results, stats
