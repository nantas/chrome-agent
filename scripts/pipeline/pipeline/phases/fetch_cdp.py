"""Phase Fetch CDP — acquire raw HTML from chrome-cdp and write to cache.

This is the CDP variant of the Fetch phase.  Unlike ``fetch.py`` (which is
tightly coupled to MediaWiki ``ApiClient`` / ``ContentAcquisitionStrategy``),
this module receives a list of page URLs and a callable that performs the CDP
navigation + HTML extraction.

Cache reuse: calls ``cache.save_page_cache()`` / ``cache.is_cached()`` with
``platform="chrome-cdp"`` so pages persist across sessions.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from .. import cache as cache_mod

log = logging.getLogger("pipeline.cdp")

# Type alias for the CDP extraction callback.
#   cdp_extract(url) → dict with at least {"html": str}
#   On failure the callback should raise or return None.
CdpExtractFn = Callable[[str], Optional[Dict[str, str]]]


def _url_to_safe_path(url: str) -> str:
    """Derive a cache-safe path from a URL path component.

    ``raw_to_cache_filename`` replaces spaces with underscores; for CDP URLs
    we also replace ``/`` with ``_`` to produce a flat filename that encodes
    the full path hierarchy.

    Example::

        /Packages/Docs/Guides/Online_Play_Guide/contents/Pages/Page_123.html
        → Packages_Docs_Guides_Online_Play_Guide_contents_Pages_Page_123.html
    """
    from urllib.parse import urlparse

    path = urlparse(url).path.strip("/")
    return path.replace("/", "_")


def run_fetch_cdp(
    pages: List[Dict[str, str]],
    domain: str,
    repo_root: str,
    cdp_extract: CdpExtractFn,
    re_fetch: bool = False,
    batch_delay_sec: float = 0.5,
) -> Dict[str, int]:
    """Execute Phase Fetch CDP.

    Args:
        pages: List of ``{"url": "...", "title": "..."}`` dicts.
        domain: Hostname for cache directory segmentation.
        repo_root: Repository root for ``.cache/`` resolution.
        cdp_extract: Callable that takes a URL and returns
            ``{"html": "<raw html>"}`` or *None* on failure.
        re_fetch: If *True*, ignore existing cache entries.
        batch_delay_sec: Seconds to sleep between actual network fetches.

    Returns:
        Stats dict ``{"total", "fetched", "skipped", "failed"}``.
    """
    platform = "chrome-cdp"

    log.info(
        "Phase Fetch CDP: %d pages (domain=%s, re_fetch=%s)",
        len(pages),
        domain,
        re_fetch,
    )

    fetched = 0
    skipped = 0
    failed = 0

    for page in pages:
        url = page["url"]
        title = page.get("title", url)
        safe_path = _url_to_safe_path(url)

        # Check cache (unless re_fetch)
        if not re_fetch and cache_mod.is_cached(repo_root, platform, domain, safe_path):
            log.debug("Cache hit: %s", safe_path)
            skipped += 1
            continue

        # Fetch via CDP
        try:
            result = cdp_extract(url)
            if result is None:
                log.warning("CDP extract returned None for %s", url)
                failed += 1
                continue

            raw_data = {
                "title": safe_path,
                "url": url,
                "html": result["html"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            cache_mod.save_page_cache(repo_root, platform, domain, raw_data)
            fetched += 1
            log.debug("Fetched and cached: %s", safe_path)
            time.sleep(batch_delay_sec)

        except Exception as exc:
            log.warning("CDP fetch failed for %s: %s", url, exc)
            failed += 1

    stats = {
        "total": len(pages),
        "fetched": fetched,
        "skipped": skipped,
        "failed": failed,
    }
    log.info(
        "Phase Fetch CDP complete: %d total, %d fetched, %d skipped, %d failed",
        stats["total"],
        fetched,
        skipped,
        failed,
    )
    return stats
