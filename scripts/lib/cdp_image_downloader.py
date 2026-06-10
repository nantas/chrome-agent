"""CDP Image Downloader — download images via Chrome CDP fetch and localise.

Extracted from the Nintendo Developer Portal crawl
(``/tmp/nintendo-rebuild/download_images.py``) and generalised for reuse.

The downloader accepts a **CDP eval callback** rather than hard-coding tab IDs
or subprocess calls, making it testable and reusable across different CDP
session managers.

Key capabilities:
  - Collect unique image URLs from Markdown files
  - Download via ``fetch()`` inside an authenticated CDP session
  - Base64 decode and store locally under ``<output_dir>/images/``
  - Update Markdown references from full URLs to relative paths
  - Deduplication and skip-existing logic
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

log = logging.getLogger("cdp_image_downloader")

# Maximum image size (bytes) — skip larger files
MAX_IMAGE_SIZE = 2_000_000

# Minimum file size (bytes) to consider "already downloaded"
MIN_EXISTING_SIZE = 100

# Type alias: cdp_eval_async(js_code: str) → Optional[str] (raw JSON string)
CdpEvalFn = Callable[[str], Optional[str]]


# ---------------------------------------------------------------------------
# Image URL collection
# ---------------------------------------------------------------------------

def collect_image_urls(
    output_dir: str,
    url_pattern: str = "Attachments/Attach_",
    contents_prefix: str = "/contents/",
) -> Dict[str, str]:
    """Collect unique image URLs from all ``.md`` files in *output_dir*.

    Args:
        output_dir: Directory containing ``.md`` files.
        url_pattern: Substring that must appear in the URL for it to be
            collected (default: Nintendo ``Attachments/Attach_`` pattern).
        contents_prefix: URL path segment after which the relative path
            is extracted (default: ``/contents/``).

    Returns:
        Dict mapping ``image_url`` → ``relative_path`` (e.g.
        ``Attachments/Attach_xxx/yyy.png``).
    """
    url_map: Dict[str, str] = {}
    md_base = Path(output_dir)

    for md_path in sorted(md_base.rglob("*.md")):
        # Skip files inside the images directory
        if "images/" in str(md_path):
            continue
        text = md_path.read_text(encoding="utf-8")
        for m in re.finditer(r"!\[([^\]]*)\]\((https://[^)]+)\)", text):
            url = m.group(2)
            if url_pattern and url_pattern not in url:
                continue
            if url not in url_map:
                parsed = urlparse(url)
                path = parsed.path
                idx = path.find(contents_prefix)
                if idx >= 0:
                    rel = path[idx + len(contents_prefix):]
                else:
                    rel = path.lstrip("/")
                url_map[url] = rel

    return url_map


# ---------------------------------------------------------------------------
# Single image download
# ---------------------------------------------------------------------------

def fetch_image_as_base64(url: str, cdp_eval: CdpEvalFn) -> Optional[Dict]:
    """Download a single image via CDP ``fetch()`` and return base64 data.

    Args:
        url: Image URL to download.
        cdp_eval: CDP eval callback that executes async JS and returns raw
            JSON output.

    Returns:
        Dict with ``mime``, ``b64``, ``size`` on success; ``{"error": "..."}``
        on failure; *None* if the CDP call itself failed.
    """
    # Escape single quotes in URL for JS string literal
    safe_url = url.replace("'", "\\'")
    js_code = """(async () => {{
  try {{
    const resp = await fetch('{url}');
    if (!resp.ok) return JSON.stringify({{error: 'HTTP ' + resp.status}});
    const blob = await resp.blob();
    if (blob.size > {max_size}) return JSON.stringify({{error: 'Too large: ' + blob.size}});
    const dataUrl = await new Promise((resolve) => {{
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    }});
    const comma = dataUrl.indexOf(',');
    return JSON.stringify({{
      mime: dataUrl.substring(5, comma - 7),
      b64: dataUrl.substring(comma + 1),
      size: blob.size
    }});
  }} catch(e) {{
    return JSON.stringify({{error: e.message}});
  }}
}})()""".format(url=safe_url, max_size=MAX_IMAGE_SIZE)

    raw = cdp_eval(js_code)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        log.warning("Failed to parse CDP response for %s", url)
        return None


# ---------------------------------------------------------------------------
# Batch download
# ---------------------------------------------------------------------------

def download_images(
    url_map: Dict[str, str],
    images_dir: str,
    cdp_eval: CdpEvalFn,
    delay_sec: float = 0.3,
) -> Dict[str, int]:
    """Download all images in *url_map* to *images_dir*.

    Args:
        url_map: Mapping ``image_url`` → ``relative_path`` (from
            ``collect_image_urls``).
        images_dir: Base directory for local image storage.
        cdp_eval: CDP eval callback.
        delay_sec: Seconds to sleep between downloads.

    Returns:
        Stats dict ``{"downloaded", "skipped", "failed"}``.
    """
    import time

    os.makedirs(images_dir, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    for url, rel_path in sorted(url_map.items()):
        local_path = os.path.join(images_dir, rel_path)

        # Skip existing
        if os.path.exists(local_path) and os.path.getsize(local_path) > MIN_EXISTING_SIZE:
            log.debug("Skip existing: %s", rel_path)
            skipped += 1
            continue

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        result = fetch_image_as_base64(url, cdp_eval)
        if result is None or "error" in result:
            error = result.get("error", "no result") if result else "no result"
            log.warning("Download failed: %s → %s", rel_path, error)
            failed += 1
            time.sleep(delay_sec)
            continue

        try:
            img_data = base64.b64decode(result["b64"])
            with open(local_path, "wb") as f:
                f.write(img_data)
            downloaded += 1
            log.debug("Downloaded: %s (%d bytes)", rel_path, len(img_data))
        except Exception as exc:
            log.warning("Decode/write failed for %s: %s", rel_path, exc)
            failed += 1

        time.sleep(delay_sec)

    stats = {
        "total": len(url_map),
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
    }
    log.info(
        "Download complete: %d total, %d downloaded, %d skipped, %d failed",
        stats["total"],
        downloaded,
        skipped,
        failed,
    )
    return stats


# ---------------------------------------------------------------------------
# Markdown reference update
# ---------------------------------------------------------------------------

def update_markdown_references(
    output_dir: str,
    url_map: Dict[str, str],
    relative_prefix: str = "../images/",
) -> int:
    """Update Markdown files to use relative image paths.

    After images are downloaded, this replaces full external URLs with
    relative paths like ``../images/Attachments/Attach_xxx/yyy.png``.

    Args:
        output_dir: Directory containing ``.md`` files.
        url_map: Mapping ``image_url`` → ``relative_path``.
        relative_prefix: Prefix for relative image paths.

    Returns:
        Number of files updated.
    """
    md_base = Path(output_dir)
    updated = 0

    for md_path in sorted(md_base.rglob("*.md")):
        if "images/" in str(md_path):
            continue
        text = md_path.read_text(encoding="utf-8")
        original = text
        for url, rel_path in url_map.items():
            local_relative = "{}{}".format(relative_prefix, rel_path)
            text = text.replace("({})".format(url), "({})".format(local_relative))
        if text != original:
            md_path.write_text(text, encoding="utf-8")
            updated += 1

    return updated
