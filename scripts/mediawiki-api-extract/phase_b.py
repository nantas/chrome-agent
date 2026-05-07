"""Phase B: Content Extraction."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .client import ApiClient
from .strategies import ContentAcquisitionStrategy, LinkResolver, TemplateProcessor
from .strategies import convert_wikitext_to_markdown

log = logging.getLogger("mediawiki-api-extract")


def process_single_page(client: ApiClient, page_info: dict, manifest_pages: list[dict],
                        domain: str, frontmatter_fields: list[str],
                        template_map: dict[str, str],
                        content_strategy: ContentAcquisitionStrategy,
                        link_resolver: LinkResolver,
                        template_processor: TemplateProcessor) -> dict:
    """Process a single page: fetch content and convert to Markdown."""
    title = page_info["title"]
    source_dir = page_info["target_directory"]
    source_url = f"https://{domain}/w/{title.replace(' ', '_')}"

    try:
        raw = content_strategy.fetch_page_content(client, title, {})
        wikitext = raw.get("wikitext", "")
        if not wikitext:
            return {"title": title, "status": "empty", "error": "Empty wikitext"}

        md_content, warnings, frontmatter = convert_wikitext_to_markdown(
            wikitext, title, source_url, manifest_pages, source_dir,
            frontmatter_fields, template_map, link_resolver, template_processor, domain
        )
        return {"title": title, "status": "ok", "content": md_content,
                "warnings": warnings, "frontmatter": frontmatter}
    except Exception as e:
        return {"title": title, "status": "error", "error": str(e)}


def run_phase_b(client: ApiClient, manifest: dict, strategy: dict,
                concurrency: int, domain: str,
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

    log.info("Phase B: Extracting content for %d pages (concurrency=%d)...",
             len(pages), concurrency)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {}
        for page in pages:
            future = executor.submit(
                process_single_page, client, page, pages,
                domain, frontmatter_fields, template_map,
                content_strategy, link_resolver, template_processor
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

            time.sleep(0.04)

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
