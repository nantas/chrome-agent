"""Phase Convert HTML — read cached HTML and convert to Markdown.

This is the HTML variant of the Convert phase.  It reads page entries from
the ``chrome-cdp`` cache and converts them to ``.md`` files using the shared
``html_to_markdown()`` converter.

Pipeline integration: the orchestrator (or a manual workflow) calls
``run_convert_html()`` with the same *repo_root* / *domain* pair used by
``fetch_cdp`` so the cache paths align automatically.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

from .. import cache as cache_mod
from scripts.lib.extraction.html_to_markdown import html_to_markdown

log = logging.getLogger("pipeline.convert_html")

PLATFORM = "chrome-cdp"


def _safe_path_to_title(safe_path: str) -> str:
    """Undo the URL-to-safe-path conversion for cache lookups.

    ``fetch_cdp`` stores cache entries with ``title`` set to the safe path
    (``/`` → ``_``).  ``raw_to_cache_filename`` then replaces spaces with
    underscores and adds ``.json``.  Since safe paths contain no spaces,
    the round-trip is identity-safe.
    """
    return safe_path


def run_convert_html(
    pages: List[Dict[str, str]],
    domain: str,
    repo_root: str,
    output_dir: str,
    base_url: Optional[str] = None,
) -> Dict[str, int]:
    """Execute Phase Convert HTML.

    Args:
        pages: List of ``{"url": "...", "title": "..."}`` dicts (same
            manifest format used by ``fetch_cdp``).
        domain: Hostname for cache directory resolution.
        repo_root: Repository root for ``.cache/`` resolution.
        output_dir: Directory to write ``.md`` output files.
        base_url: Optional base URL for ``> Source:`` metadata line.

    Returns:
        Stats dict ``{"total", "converted", "skipped", "failed"}``.
    """
    from urllib.parse import urlparse

    os.makedirs(output_dir, exist_ok=True)

    total = len(pages)
    converted = 0
    skipped = 0
    failed = 0

    log.info(
        "Phase Convert HTML: %d pages (domain=%s, output=%s)",
        total,
        domain,
        output_dir,
    )

    for page in pages:
        url = page["url"]
        title = page.get("title", "")
        safe_path = _url_to_safe_path(url)

        # Load cached HTML
        cached = cache_mod.load_page_cache(repo_root, PLATFORM, domain, safe_path)
        if cached is None:
            log.warning("No cache entry for %s — skipping", safe_path)
            skipped += 1
            continue

        html = cached.get("html", "")
        if not html:
            log.warning("Empty HTML in cache for %s — skipping", safe_path)
            skipped += 1
            continue

        try:
            md_body = html_to_markdown(html)

            # Build output filename: use page title if available, else safe_path stem
            if title:
                out_name = title.replace("/", "_").replace(" ", "_") + ".md"
            else:
                out_name = safe_path.rsplit("_", 1)[-1] if "_" in safe_path else safe_path
                if not out_name.endswith(".md"):
                    out_name += ".md"

            # Assemble full MD with metadata header
            lines = []
            if title:
                lines.append("# {}".format(title))
                lines.append("")
            if url:
                lines.append("> Source: {}".format(url))
                lines.append("")
            lines.append(md_body)

            out_path = os.path.join(output_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            converted += 1
            log.debug("Converted: %s → %s", safe_path, out_name)

        except Exception as exc:
            log.warning("Convert failed for %s: %s", safe_path, exc)
            failed += 1

    stats = {
        "total": total,
        "converted": converted,
        "skipped": skipped,
        "failed": failed,
    }
    log.info(
        "Phase Convert HTML complete: %d total, %d converted, %d skipped, %d failed",
        total,
        converted,
        skipped,
        failed,
    )
    return stats


def _url_to_safe_path(url: str) -> str:
    """Derive cache-safe path from URL (mirrors fetch_cdp._url_to_safe_path)."""
    from urllib.parse import urlparse as _urlparse

    path = _urlparse(url).path.strip("/")
    return path.replace("/", "_")
