"""Phase Fetch — acquire raw content from API and write to cache."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from ...client import ApiClient, PageNotFoundError
from .. import cache as cache_mod
from ...strategies import ContentAcquisitionStrategy

log = logging.getLogger("pipeline")



def fetch_single_page(client: ApiClient, page_info: dict,
                      content_strategy: ContentAcquisitionStrategy) -> dict:
    """Fetch raw content for a single page via API.

    Returns a raw dict with fields: html, wikitext, rendered_html, images, title.
    Raises PageNotFoundError if the page does not exist.
    """
    title = page_info["title"]
    raw = content_strategy.fetch_page_content(client, title, {})
    raw["title"] = title
    return raw

def run_fetch(client: ApiClient, manifest: dict, strategy: dict,
                    rate_limit_config, domain: str,
                    content_strategy: ContentAcquisitionStrategy,
                    repo_root: str,
                    re_fetch: bool = False) -> dict:
    """Execute Phase Fetch: acquire raw content from API and write to cache.

    Args:
        client: ApiClient instance.
        manifest: Page manifest dict with ``pages`` list.
        strategy: Strategy configuration dict.
        rate_limit_config: Rate limit configuration.
        domain: Wiki domain.
        content_strategy: Content acquisition strategy.
        repo_root: Repository root path for cache directory.
        re_fetch: If True, ignore existing cache and re-fetch all pages.

    Returns:
        Stats dict with total, fetched, skipped, failed counts.
    """
    platform = strategy.get("api", {}).get("platform", "mediawiki")
    pages = manifest["pages"]

    concurrency = rate_limit_config.concurrency if rate_limit_config else 1
    batch_delay_sec = (rate_limit_config.batch_delay_ms / 1000.0) if rate_limit_config else 1.0

    log.info("Phase Fetch: %d pages (concurrency=%d, batch_delay_ms=%d, re_fetch=%s)...",
             len(pages), concurrency,
             rate_limit_config.batch_delay_ms if rate_limit_config else 1000,
             re_fetch)

    # Pre-compute cached pages unless re_fetch
    cached_pages = set() if re_fetch else cache_mod.list_cached_pages(repo_root, platform, domain)
    if cached_pages and not re_fetch:
        log.info("Cache: %d pages already cached, will skip", len(cached_pages))

    # --- Fast path: all pages already cached (spec: full-cache-fastpath) ---
    manifest_titles = {p["title"] for p in pages}
    if not re_fetch and manifest_titles and manifest_titles <= cached_pages:
        log.info("Cache: all %d manifest pages already cached — skipping fetch", len(manifest_titles))
        return {"total": len(pages), "fetched": 0, "skipped": len(pages), "failed": 0}

    # --- Prefilter: separate cached from to_fetch (spec: partial-cache-prefilter) ---
    to_fetch = []
    skipped_count = 0
    for p in pages:
        if not re_fetch and p["title"] in cached_pages:
            skipped_count += 1
        else:
            to_fetch.append(p)

    if skipped_count:
        log.info("Cache: %d pages already cached, %d to fetch", skipped_count, len(to_fetch))

    fetched_count = 0
    failed_count = 0

    def _fetch_one(page_info: dict) -> dict:
        """Fetch a single page and write to cache. Returns status dict."""
        title = page_info["title"]
        try:
            raw = fetch_single_page(client, page_info, content_strategy)
            # Add metadata for cache
            raw.setdefault("content_acquisition", strategy.get("api", {})
                             .get("content_profile", {})
                             .get("content_acquisition", "unknown"))
            raw.setdefault("base_url", client.base_url)
            cache_mod.save_page_cache(repo_root, platform, domain, raw)
            return {"title": title, "status": "ok"}
        except PageNotFoundError:
            log.info("Page not found, skipping: %s", title)
            return {"title": title, "status": "not_found"}
        except Exception as e:
            log.warning("Fetch failed for '%s': %s", title, e)
            return {"title": title, "status": "error", "error": str(e)}

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(_fetch_one, page): page["title"] for page in to_fetch}
        for future in as_completed(futures):
            title = futures[future]
            try:
                result = future.result()
                if result["status"] == "ok":
                    fetched_count += 1
                    # Sleep only on actual network requests (spec: batch-delay-only-on-network-requests)
                    time.sleep(batch_delay_sec)
                elif result["status"] == "not_found":
                    skipped_count += 1
                else:
                    failed_count += 1
                    log.warning("Fetch failed for '%s': %s", title, result.get("error", "unknown"))
            except Exception as e:
                failed_count += 1
                log.warning("Fetch failed for '%s': %s", title, e)

            done = fetched_count + skipped_count + failed_count
            if done % 50 == 0:
                log.info("Phase Fetch progress: %d/%d (fetched=%d, skipped=%d, failed=%d)",
                         done, len(pages), fetched_count, skipped_count, failed_count)

    stats = {
        "total": len(pages),
        "fetched": fetched_count,
        "skipped": skipped_count,
        "failed": failed_count,
    }
    log.info("Fetch phase complete: %d total, %d fetched, %d skipped (cached), %d failed",
             stats["total"], fetched_count, skipped_count, failed_count)
    return stats
