"""Persistent page content cache for MediaWiki API extraction pipeline.

Cache directory layout:
    <repo_root>/.cache/<platform>/<domain>/<safe_title>.json

platform derivation:
    - strategy with api.platform → use that value (e.g. "mediawiki")
    - no api.platform (Scrapling path) → fixed "scrapling"
"""

from __future__ import annotations

import json
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
    """Convert a page title to a safe cache filename (spaces → underscores, .json suffix)."""
    safe = title.replace(" ", "_")
    # Collapse consecutive underscores
    while "__" in safe:
        safe = safe.replace("__", "_")
    # Strip leading/trailing underscores
    safe = safe.strip("_")
    return f"{safe}.json"


def save_page_cache(repo_root: str, platform: str, domain: str,
                    raw_data: dict) -> Path:
    """Atomically write a page cache entry. Returns the path written.

    ``raw_data`` must already contain all required fields (title, html,
    wikitext, images, etc.).  ``fetched_at`` is injected if absent.
    """
    title = raw_data.get("title", "")
    cache_dir = get_domain_cache_dir(repo_root, platform, domain)
    filename = raw_to_cache_filename(title)
    target = cache_dir / filename

    # Inject timestamp if not present
    if "fetched_at" not in raw_data:
        raw_data["fetched_at"] = datetime.now(timezone.utc).isoformat()

    # Atomic write via temp file in same directory
    tmp_path = cache_dir / f".tmp_{filename}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
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


def load_page_cache(repo_root: str, platform: str, domain: str,
                    title: str) -> Optional[dict]:
    """Load a cached page entry. Returns ``None`` if not found."""
    cache_dir = get_domain_cache_dir(repo_root, platform, domain)
    filename = raw_to_cache_filename(title)
    target = cache_dir / filename
    if not target.exists():
        return None
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def is_cached(repo_root: str, platform: str, domain: str, title: str) -> bool:
    """Check whether a page cache entry exists."""
    cache_dir = get_domain_cache_dir(repo_root, platform, domain)
    filename = raw_to_cache_filename(title)
    return (cache_dir / filename).exists()


def list_cached_pages(repo_root: str, platform: str, domain: str) -> set[str]:
    """Return the set of cached page titles for a domain.

    Filenames are converted back from underscore-space convention.
    """
    cache_dir = get_domain_cache_dir(repo_root, platform, domain)
    titles: set[str] = set()
    if not cache_dir.exists():
        return titles
    for entry in cache_dir.iterdir():
        if entry.suffix == ".json" and not entry.name.startswith("."):
            # Reverse the safe-title conversion: underscores → spaces
            title = entry.stem.replace("_", " ")
            titles.add(title)
    return titles
