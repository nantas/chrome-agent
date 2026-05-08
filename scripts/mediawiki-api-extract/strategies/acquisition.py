"""Content acquisition strategy implementations."""

import logging
import re

from ..client import ApiClient

log = logging.getLogger("mediawiki-api-extract")


class WikitextOnlyAcquisitionStrategy:
    """Default content acquisition fetching prop=wikitext only."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"wikitext_parse"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        data = client.parse(page=title, prop="wikitext")
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        return {"wikitext": wikitext, "html": None}


class HybridAcquisitionStrategy:
    """Content acquisition fetching wikitext, and optionally rendered HTML + images."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"wikitext_parse", "html_parse", "imageinfo_query"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        data = client.parse(page=title, prop="wikitext")
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        result = {"wikitext": wikitext, "rendered_html": None, "images": None}
        if not wikitext:
            return result

        has_dynamic = bool(re.search(r'\{\{\s*#\s*(invoke|dpl|lst|if|ifeq)\s*[:|]', wikitext, re.IGNORECASE))
        if has_dynamic:
            log.debug("Dynamic content detected for %s, fetching rendered HTML and images", title)
            try:
                html_data = client.parse(page=title, prop="text")
                rendered = html_data.get("parse", {}).get("text", {}).get("*", "")
                result["rendered_html"] = rendered
            except RuntimeError as e:
                log.warning("Failed to fetch rendered HTML for %s: %s", title, e)
            try:
                img_data = client.parse(page=title, prop="images")
                images = img_data.get("parse", {}).get("images", [])
                result["images"] = images
            except RuntimeError as e:
                log.warning("Failed to fetch images for %s: %s", title, e)
        return result


class HtmlRenderedAcquisitionStrategy:
    """Content acquisition fetching server-rendered HTML via action=parse&prop=text."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"html_parse"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        data = client.parse(page=title, prop="text")
        html = data.get("parse", {}).get("text", {}).get("*", "")
        result = {"wikitext": None, "html": html, "rendered_html": html, "images": None}

        if not html:
            log.warning("Empty HTML for %s, falling back to wikitext", title)
            try:
                wt_data = client.parse(page=title, prop="wikitext")
                wikitext = wt_data.get("parse", {}).get("wikitext", {}).get("*", "")
                result["wikitext"] = wikitext
            except RuntimeError as e:
                log.warning("Wikitext fallback failed for %s: %s", title, e)

        try:
            img_data = client.parse(page=title, prop="images")
            images = img_data.get("parse", {}).get("images", [])
            result["images"] = images
        except RuntimeError as e:
            log.debug("Failed to fetch images for %s: %s", title, e)

        return result
