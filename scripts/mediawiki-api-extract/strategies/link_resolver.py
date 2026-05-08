"""Link resolver strategy implementations."""

import logging
import os
import re
from typing import Optional
from urllib.parse import quote as url_quote

log = logging.getLogger("mediawiki-api-extract")


class ExactTitleLinkResolver:
    """Default link resolver using exact title matching."""

    def __init__(self, domain: str = ""):
        self._domain = domain

    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str:
        def replace_link(match):
            target = match.group(1)
            display = match.group(2) if match.group(2) else target
            return self.resolve(target, display, source_dir, manifest_pages)

        text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', replace_link, text)
        text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: self.resolve(m.group(1), m.group(1), source_dir, manifest_pages), text)
        return text

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str:
        pages_by_title = {p["title"]: p for p in manifest_pages}

        ns_prefixes = ["File:", "Category:", "Template:", "Special:", "Help:", "MediaWiki:"]
        for prefix in ns_prefixes:
            if target.startswith(prefix):
                if prefix == "File:":
                    parts = target[len("File:"):].split("|")
                    image_name = parts[0]
                    alt_text = parts[1] if len(parts) > 1 else image_name
                    alt_text = re.sub(r'\d+px', '', alt_text).strip('|').strip()
                    encoded_name = url_quote(image_name, safe='')
                    return f"![{alt_text}](https://{self._domain}/Special:Redirect/file/{encoded_name})"
                return ""

        page = pages_by_title.get(target)
        if page:
            target_dir = page["target_directory"]
            target_file = page["target_filename"]
            if target_dir != source_dir and target_dir != "Misc":
                if source_dir == "Misc" or "/" not in source_dir:
                    rel_path = f"{target_dir}/{target_file}"
                else:
                    source_depth = source_dir.count("/")
                    prefix = "../" * (source_depth + 1)
                    rel_path = f"{prefix}{target_dir}/{target_file}"
                return f"[{display}]({rel_path})"
            elif target_dir == source_dir:
                return f"[{display}]({target_file})"
            else:
                if source_dir != "Misc" and target_dir == "Misc":
                    return f"[{display}](../Misc/{target_file})"
                return f"[{display}]({target_file})"

        return f"[{display}]({target.replace(' ', '_')}.md)"


class ShortNameLinkResolver:
    """Link resolver using short-name index with balanced-bracket parsing and relpath."""

    def __init__(self, domain: str = "", manifest_pages: Optional[list[dict]] = None):
        self._domain = domain
        self._pages_by_title: dict[str, dict] = {}
        self._short_title_index: dict[str, list[dict]] = {}
        if manifest_pages:
            self._build_index(manifest_pages)

    def _build_index(self, manifest_pages: list[dict]):
        self._pages_by_title = {p["title"]: p for p in manifest_pages}
        for p in manifest_pages:
            short = p["title"].split(":")[-1]
            self._short_title_index.setdefault(short, []).append(p)

    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str:
        if manifest_pages and not self._pages_by_title:
            self._build_index(manifest_pages)

        def replace_pipe_link(match):
            target = match.group(1)
            display = match.group(2)
            return self.resolve(target, display, source_dir, manifest_pages)

        text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', replace_pipe_link, text)
        text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: self.resolve(m.group(1), m.group(1), source_dir, manifest_pages), text)
        return text

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str:
        if not self._pages_by_title and manifest_pages:
            self._build_index(manifest_pages)

        pages_by_title = self._pages_by_title

        ns_prefixes = ["File:", "Category:", "Template:", "Special:", "Help:", "MediaWiki:"]
        for prefix in ns_prefixes:
            if target.startswith(prefix):
                if prefix == "File:":
                    parts = target[len("File:"):].split("|")
                    image_name = parts[0]
                    alt_text = parts[1] if len(parts) > 1 else image_name
                    alt_text = re.sub(r'\d+px', '', alt_text).strip('|').strip()
                    encoded_name = url_quote(image_name, safe='')
                    return f"![{alt_text}](https://{self._domain}/Special:Redirect/file/{encoded_name})"
                return ""

        page = pages_by_title.get(target)
        if page:
            return self._make_link(page, display, source_dir)

        short = target.split(":")[-1]
        candidates = self._short_title_index.get(short, [])
        if candidates:
            source_ns = self._guess_namespace(source_dir)
            same_ns = [c for c in candidates if self._guess_namespace(c["target_directory"]) == source_ns]
            page = same_ns[0] if same_ns else candidates[0]
            return self._make_link(page, display, source_dir)

        for full_title in pages_by_title:
            if full_title.endswith(f":{target}") or full_title.endswith(f":{short}"):
                return self._make_link(pages_by_title[full_title], display, source_dir)

        return f"[{display}]({target.replace(' ', '_')}.md)"

    def _guess_namespace(self, target_dir: str) -> str:
        if target_dir.startswith("StS2") or target_dir.startswith("Slay the Spire 2"):
            return "sts2"
        if target_dir.startswith("StS1") or target_dir.startswith("Slay the Spire"):
            return "sts1"
        return ""

    def _make_link(self, page: dict, display: str, source_dir: str) -> str:
        target_dir = page["target_directory"]
        target_file = page["target_filename"]
        if target_dir == source_dir:
            return f"[{display}]({target_file})"
        source_path = source_dir.replace("/", os.sep) if source_dir else "."
        target_path = os.path.join(target_dir.replace("/", os.sep), target_file) if target_dir else target_file
        rel = os.path.relpath(target_path, source_path).replace(os.sep, "/")
        return f"[{display}]({rel})"
