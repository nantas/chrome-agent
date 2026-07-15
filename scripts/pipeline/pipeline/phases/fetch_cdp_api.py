"""Phase Fetch CDP API — retrieve content from REST API via CDP Runtime.evaluate.

This module handles API-backed SPA sites where:
- Scrapling HTTP returns empty body (client-side rendered)
- Content is available via RESTful JSON API
- Authentication token is stored in browser localStorage
- API calls must be made from within the page context (CDP Runtime.evaluate)

Unlike ``fetch_cdp.py`` (which navigates to pages and extracts DOM HTML),
this module calls the site's own REST API through in-page ``fetch()`` and
receives content directly (usually Markdown or plain text).

Cache: uses ``cache_mod`` with ``platform="chrome-cdp"``, storing ``content``
(not ``html``) in cache entries.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from .. import cache as cache_mod

log = logging.getLogger("pipeline.cdp_api")

# Type alias: eval_fn(js_expression) -> result.value string or None
CdpApiEvalFn = Callable[[str], Optional[str]]


def _make_safe_path(name: str) -> str:
    """Derive a cache-safe path from a file name.

    Replaces ``/`` and spaces with ``_``.

    Example::

        design/GDD-拼词肉鸽.md → design_GDD-拼词肉鸽.md
    """
    safe = name.replace("/", "_").replace(" ", "_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")


def _build_token_expr(strategy: dict) -> str:
    """Build JS expression to read the auth token from localStorage."""
    auth = strategy.get("api", {}).get("auth", {})
    source = auth.get("source", "localStorage")
    key = auth.get("key", "access_token")
    if source == "localStorage":
        return f'JSON.stringify({{"token": localStorage.getItem("{key}") || ""}})'
    # Future: cookie, sessionStorage
    return f'JSON.stringify({{"token": localStorage.getItem("{key}") || ""}})'


def _build_list_expr(strategy: dict, project_id: str, token: str) -> str:
    """Build JS expression to call the list API."""
    api = strategy.get("api", {})
    auth = api.get("auth", {})
    endpoints = api.get("endpoints", {})
    list_cfg = endpoints.get("list", {})
    url = list_cfg.get("url", "/api/v1/docs/list")
    header_fmt = auth.get("header_format", "Bearer {token}")

    return (
        f'fetch("{url}?project_id={project_id}&type=docs",'
        f'{{headers: {{Authorization: "{header_fmt.format(token=token)}"}}}})'
        f".then(r => r.json()).then(d => JSON.stringify(d))"
    )


def _build_content_expr(strategy: dict, project_id: str, file_name: str, token: str) -> str:
    """Build JS expression to call the content API for a single file."""
    api = strategy.get("api", {})
    auth = api.get("auth", {})
    endpoints = api.get("endpoints", {})
    content_cfg = endpoints.get("content", {})
    url = content_cfg.get("url", "/api/v1/docs/content")
    header_fmt = auth.get("header_format", "Bearer {token}")

    return (
        f'fetch("{url}?project_id={project_id}&name={file_name}",'
        f'{{headers: {{Authorization: "{header_fmt.format(token=token)}"}}}})'
        f".then(r => r.text())"
    )


def run_fetch_cdp_api(
    eval_fn: CdpApiEvalFn,
    strategy: dict,
    domain: str,
    repo_root: str,
    project_id: str,
    path_prefix: str | None = None,
    re_fetch: bool = False,
    batch_delay_sec: float = 0.3,
) -> dict:
    """Execute CDP-to-REST-API bridge fetch.

    Args:
        eval_fn: Callable that takes a JS expression and returns the
            ``Runtime.evaluate`` result value (JSON string), or *None* on failure.
        strategy: Parsed strategy dict (from YAML frontmatter).
        domain: Hostname for cache directory segmentation.
        repo_root: Repository root for ``.cache/`` resolution.
        project_id: Project identifier for API calls.
        path_prefix: Optional path prefix to filter files (e.g. ``"design/"``).
        re_fetch: If *True*, ignore existing cache entries.
        batch_delay_sec: Seconds to sleep between content API calls.

    Returns:
        Results dict mapping safe path → {title, status, content, rendered_html}.
        Compatible with ``extraction_results.json`` consumed by assemble phase.
    """
    platform = "chrome-cdp"
    results: dict = {}

    # 1. Get token from localStorage
    token_expr = _build_token_expr(strategy)
    token_raw = eval_fn(token_expr)
    if token_raw is None:
        log.error("Failed to read token from localStorage")
        return results

    try:
        token_data = json.loads(token_raw)
        token = token_data.get("token", "")
    except (json.JSONDecodeError, TypeError):
        log.error("Invalid token response: %s", token_raw[:100])
        return results

    if not token:
        log.error("Token is empty — user may not be logged in")
        return results

    log.info("Token obtained from localStorage (%d chars)", len(token))

    # 2. Call list API
    list_expr = _build_list_expr(strategy, project_id, token)
    list_raw = eval_fn(list_expr)
    if list_raw is None:
        log.error("List API call returned None")
        return results

    try:
        list_data = json.loads(list_raw)
    except (json.JSONDecodeError, TypeError):
        log.error("Invalid list API response: %s", list_raw[:200])
        return results

    if not list_data.get("success") and "data" not in list_data:
        log.error("List API returned error: %s", list_data.get("msg", "unknown"))
        return results

    entries = list_data.get("data", [])
    log.info("List API returned %d entries", len(entries))

    # 3. Filter: exclude directories and non-matching paths
    files: list[dict] = []
    for entry in entries:
        # Skip directories
        if entry.get("mimeType") == "inode/directory":
            continue
        # Skip non-file types
        if entry.get("type") != "resource_link":
            continue
        # Apply path_prefix filter
        name = entry.get("name", "")
        if path_prefix and not name.startswith(path_prefix):
            continue
        files.append(entry)

    log.info("After filtering: %d files (prefix=%s)", len(files), path_prefix or "none")

    # 4. Fetch each file
    fetched = 0
    skipped = 0
    failed = 0

    for file_entry in files:
        name = file_entry["name"]
        safe_path = _make_safe_path(name)

        # Check cache
        if not re_fetch and cache_mod.is_cached(repo_root, platform, domain, safe_path):
            log.debug("Cache hit: %s", safe_path)
            cached = cache_mod.load_page_cache(repo_root, platform, domain, safe_path)
            if cached:
                results[safe_path] = {
                    "title": safe_path,
                    "status": "ok",
                    "content": cached.get("content", ""),
                    "rendered_html": None,
                }
            skipped += 1
            continue

        # Fetch via CDP
        try:
            content_expr = _build_content_expr(strategy, project_id, name, token)
            content = eval_fn(content_expr)
            if content is None:
                log.warning("Content API returned None for %s", name)
                results[safe_path] = {
                    "title": safe_path,
                    "status": "error",
                    "content": "",
                    "rendered_html": None,
                }
                failed += 1
                continue

            # Save to cache
            cache_mod.save_page_cache(
                repo_root,
                platform,
                domain,
                {
                    "title": safe_path,
                    "name": name,
                    "content": content,
                },
            )

            results[safe_path] = {
                "title": safe_path,
                "status": "ok",
                "content": content,
                "rendered_html": None,
            }
            fetched += 1
            log.debug("Fetched and cached: %s (%d chars)", safe_path, len(content))

        except Exception as exc:
            log.warning("Content API failed for %s: %s", name, exc)
            results[safe_path] = {
                "title": safe_path,
                "status": "error",
                "content": "",
                "rendered_html": None,
            }
            failed += 1

        # Rate limiting
        if batch_delay_sec > 0:
            time.sleep(batch_delay_sec)

    stats = {
        "total": len(files),
        "fetched": fetched,
        "skipped": skipped,
        "failed": failed,
    }
    log.info(
        "Phase Fetch CDP API complete: %d total, %d fetched, %d skipped, %d failed",
        stats["total"], fetched, skipped, failed,
    )
    return results
