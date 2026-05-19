"""Phase Convert — read from cache and convert to Markdown."""

import logging
from typing import Optional

from ..phase_b import convert_single_page
from ..registry import build_pipeline
from .. import cache as cache_mod
from ...strategies import (
    ExactTitleLinkResolver,
    SimpleSubstitutionTemplateProcessor,
)

log = logging.getLogger("pipeline")


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
