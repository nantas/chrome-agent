"""Unified link fixer for Markdown output directories.

Consolidates link repair logic that was previously scattered across
strategies.py, phase_b.py, phase_c.py, and ad-hoc scripts.
"""

import json
import logging
import os
import re
from typing import Optional
from urllib.parse import unquote

log = logging.getLogger("mediawiki-api-extract.converters")


def fix_links_in_dir(output_dir: str, domain: str,
                     manifest_pages: Optional[list[dict]] = None) -> dict:
    """Scan and fix links in all .md files under output_dir.

    Fixes:
    1. /wiki/Title or https://domain/wiki/Title → relative .md links
    2. .md.md double suffix → .md
    3. Fragment (#Section) preservation
    4. Query parameters (?action=edit) stripping
    5. Unresolved relative links → attempt manifest lookup

    Returns:
        dict with fixed/skipped/unchanged counts.
    """
    # Build title → path index
    title_to_path: dict[str, tuple[str, str]] = {}
    if manifest_pages:
        for p in manifest_pages:
            title_to_path[p["title"]] = (p["target_directory"], p["target_filename"])
            # Also index by slug (underscore version)
            slug = p["title"].replace(" ", "_")
            title_to_path[slug] = (p["target_directory"], p["target_filename"])

    stats = {"fixed": 0, "skipped": 0, "unchanged": 0}

    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            source_dir = os.path.relpath(root, output_dir) if root != output_dir else ""

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = _fix_links_in_content(content, domain, source_dir, title_to_path, output_dir)

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                stats["fixed"] += 1
            else:
                stats["unchanged"] += 1

    log.info("Link fix complete: %d fixed, %d unchanged, %d skipped",
             stats["fixed"], stats["unchanged"], stats["skipped"])
    return stats


def _fix_links_in_content(content: str, domain: str, source_dir: str,
                          title_to_path: dict, output_dir: str) -> str:
    """Fix links within a single file's content."""

    # 1. Fix .md.md double suffix
    content = re.sub(r'\.md\.md\b', '.md', content)

    # 2. Fix wiki path links: [text](https://domain/wiki/Title) or [text](/wiki/Title)
    def fix_wiki_link(match):
        full_match = match.group(0)
        text = match.group(1)
        url = match.group(2)

        # Check if it's a wiki internal link
        wiki_prefix = f"https://{domain}/wiki/"
        if url.startswith(wiki_prefix):
            path = url[len(wiki_prefix):]
        elif url.startswith("/wiki/"):
            path = url[len("/wiki/"):]
        else:
            return full_match

        # Strip query and fragment
        fragment = ""
        if "#" in path:
            path, fragment = path.rsplit("#", 1)
        path = path.split("?")[0]

        # Decode
        path = unquote(path)
        title = path.replace("_", " ")

        # Skip non-content namespaces
        if title.startswith(("File:", "Category:", "Template:", "Talk:", "Special:", "Help:")):
            return full_match

        # Look up in manifest
        target = title_to_path.get(title)
        if target is None:
            target = title_to_path.get(title.replace(" ", "_"))
        if target is None:
            # Cannot resolve — keep original
            return full_match

        target_dir, target_file = target
        rel_path = _compute_relative_path(source_dir, target_dir, target_file)

        if fragment:
            rel_path = f"{rel_path}#{fragment}"

        return f"[{text}]({rel_path})"

    # Match markdown links: [text](url)
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_wiki_link, content)

    # 3. Fix unresolved .md links (Title.md where file doesn't exist but manifest knows it)
    def fix_unresolved_md_link(match):
        text = match.group(1)
        path = match.group(2)

        # Skip external links and anchors
        if path.startswith("http") or path.startswith("#") or path.startswith("/"):
            return match.group(0)

        # Check if target exists
        if source_dir:
            target_full = os.path.join(output_dir, source_dir, path)
        else:
            target_full = os.path.join(output_dir, path)
        target_norm = os.path.normpath(target_full)

        if os.path.exists(target_norm):
            return match.group(0)  # Already resolves, skip

        # Try to find in manifest by filename
        basename = os.path.basename(path).replace(".md", "")
        title_candidate = basename.replace("_", " ")

        target = title_to_path.get(title_candidate)
        if target is None:
            target = title_to_path.get(basename)
        if target is None:
            return match.group(0)

        target_dir, target_file = target
        rel_path = _compute_relative_path(source_dir, target_dir, target_file)
        return f"[{text}]({rel_path})"

    content = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+\.md)\)', fix_unresolved_md_link, content)

    return content


def _compute_relative_path(source_dir: str, target_dir: str, target_file: str) -> str:
    """Compute relative path from source directory to target file."""
    if target_dir == source_dir:
        return target_file

    source_path = source_dir.replace("/", os.sep) if source_dir else "."
    target_path = os.path.join(target_dir.replace("/", os.sep), target_file) if target_dir else target_file
    return os.path.relpath(target_path, source_path).replace(os.sep, "/")
