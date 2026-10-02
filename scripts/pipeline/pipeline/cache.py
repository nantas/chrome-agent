"""Persistent page content cache for MediaWiki API extraction pipeline.

Cache directory layout:
    <repo_root>/.cache/<platform>/<domain>/v2-<title_sha256>.json

platform derivation:
    - strategy with api.platform → use that value (e.g. "mediawiki")
    - no api.platform (Scrapling path) → fixed "scrapling"
"""

from __future__ import annotations

import json
import hashlib
import logging
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_cache_root(repo_root: str) -> Path:
    """Return the cache root directory ``<repo_root>/.cache/``."""
    return Path(repo_root) / ".cache"


def get_domain_cache_dir(repo_root: str, platform: str, domain: str) -> Path:
    """Return ``<repo_root>/.cache/<platform>/<domain>/``, creating it if needed."""
    cache_dir = get_cache_root(repo_root) / platform / domain
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def raw_to_cache_filename(title: str) -> str:
    """Return a bounded, filesystem-safe key for the exact title.

    Cache identity is independent of Markdown/Obsidian output filenames.
    """
    return "v2-" + hashlib.sha256(title.encode("utf-8")).hexdigest() + ".json"


def save_page_cache(repo_root: str, platform: str, domain: str,
                    raw_data: dict) -> Path:
    """Atomically write a page cache entry. Returns the path written.

    ``raw_data`` must already contain all required fields (title, html,
    wikitext, images, etc.).  ``fetched_at`` is injected if absent.
    """
    title = raw_data["title"]
    raw_data = {**raw_data, "cache_schema_version": 2}
    cache_dir = get_domain_cache_dir(repo_root, platform, domain)
    filename = raw_to_cache_filename(title)
    target = cache_dir / filename

    # Inject timestamp if not present
    if "fetched_at" not in raw_data:
        raw_data["fetched_at"] = datetime.now(timezone.utc).isoformat()

    # Atomic write via temp file in same directory
    fd, tmp_path = tempfile.mkstemp(dir=cache_dir, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, target)
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return target


log = logging.getLogger("pipeline.cache")


def _read_entry(path: Path) -> Optional[dict]:
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        if isinstance(data, dict) and isinstance(data.get("title"), str):
            return data
        log.warning("Cache rejected %s: missing title", path.name)
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as error:
        log.warning("Cache rejected %s: %s", path.name, error)
    return None


def _candidate_names(title: str) -> list[str]:
    names = [raw_to_cache_filename(title)]
    for value in (title.replace(" ", "_"),
                  title.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")):
        while "__" in value:
            value = value.replace("__", "_")
        name = value.strip("_") + ".json"
        # Never interpret a title as a path, including legacy traversal names.
        if "/" not in name and "\\" not in name and len(name.encode("utf-8")) <= 255:
            names.append(name)
    return list(dict.fromkeys(names))


def load_page_cache(repo_root: str, platform: str, domain: str,
                    title: str) -> Optional[dict]:
    """Read v2 then safe legacy candidates, always validating exact identity."""
    directory = Path(repo_root) / ".cache" / platform / domain
    for name in _candidate_names(title):
        path = directory / name
        if path.is_symlink():
            continue
        data = _read_entry(path)
        if data is not None:
            if data["title"] == title:
                return data
            log.warning("Cache rejected %s: title mismatch", name)
    return None


def is_cached(repo_root: str, platform: str, domain: str, title: str) -> bool:
    return load_page_cache(repo_root, platform, domain, title) is not None


def list_cached_pages(repo_root: str, platform: str, domain: str) -> set[str]:
    """Enumerate original titles from validated metadata, never from filenames."""
    directory = Path(repo_root) / ".cache" / platform / domain
    if not directory.exists():
        return set()
    titles = set()
    for entry in directory.iterdir():
        if entry.suffix != ".json" or entry.name.startswith(".") or entry.is_symlink():
            continue
        data = _read_entry(entry)
        if data is not None and entry.name in _candidate_names(data["title"]):
            titles.add(data["title"])
    return titles


def resolve_acquisition(strategy: dict) -> str:
    """Resolve the registered acquisition ID, including the factory default."""
    from .registry import DEFAULT_STRATEGIES, STRATEGY_REGISTRY
    mode = strategy.get('api', {}).get('content_profile', {}).get(
        'content_acquisition', DEFAULT_STRATEGIES['content_acquisition'][0])
    if mode not in STRATEGY_REGISTRY['content_acquisition']:
        raise ValueError(f'Unknown content acquisition: {mode}')
    return mode


def admit_page(raw: Optional[dict], title: str, mode: str,
               base_url: str = '') -> tuple[Optional[dict], Optional[dict]]:
    """Return an admitted copy or a structured reason; never mutate old data."""
    from ..strategies.acquisition import HybridAcquisitionStrategy
    actual = raw.get('content_acquisition') if isinstance(raw, dict) else None
    error = {'error': 'cache_incompatible', 'expected_mode': mode,
             'actual_mode': actual, 'remediation': 'Run --phase fetch (or --re-fetch) with the current strategy'}
    if raw is None:
        return None, {**error, 'error': 'cache_miss', 'reason': 'missing_or_invalid_entry'}
    if raw.get('title') != title:
        return None, {**error, 'reason': 'title_mismatch'}
    if base_url and raw.get('base_url') and raw['base_url'].rstrip('/') != base_url.rstrip('/'):
        return None, {**error, 'reason': 'source_mismatch'}
    html = raw.get('html')
    wt = raw.get('wikitext')
    has_html = isinstance(html, str) and bool(html.strip())
    has_wt = isinstance(wt, str)
    if actual is None:
        # Markerless legacy is only safe when its representation is unambiguous.
        actual = 'html_rendered' if has_html and not has_wt else 'wikitext_only' if has_wt and not has_html else None
    if actual != mode:
        return None, {**error, 'reason': 'acquisition_mismatch'}
    missing = []
    if mode == 'html_rendered' and not has_html:
        missing.append('html')
    if mode in ('wikitext_only', 'hybrid_wikitext_plus_rendered') and not has_wt:
        missing.append('wikitext')
    if mode == 'hybrid_wikitext_plus_rendered' and has_wt and HybridAcquisitionStrategy.requires_rendered(wt):
        if not isinstance(raw.get('rendered_html'), str) or not raw['rendered_html'].strip():
            missing.append('rendered_html')
    if missing:
        return None, {**error, 'reason': 'missing_payload', 'missing_fields': missing}
    if mode not in ('html_rendered', 'wikitext_only', 'hybrid_wikitext_plus_rendered'):
        return None, {**error, 'reason': 'unknown_mode'}
    from scripts.lib.content_admission import classify_html
    fields = ['html'] if mode == 'html_rendered' else ['rendered_html'] if mode == 'hybrid_wikitext_plus_rendered' and HybridAcquisitionStrategy.requires_rendered(wt) else []
    for field in fields:
        admission = classify_html(raw.get(field))
        if not admission['admitted']:
            return None, {**error, 'reason': admission['reason'], 'admission': admission}
    return {**raw, 'content_acquisition': mode}, None
