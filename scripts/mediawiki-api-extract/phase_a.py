"""Phase A: Page Discovery."""

import logging

from .client import ApiClient
from .strategies import DiscoveryStrategy

log = logging.getLogger("mediawiki-api-extract")


def run_phase_a(client: ApiClient, strategy: dict, origin: str,
                discovery_strategy: DiscoveryStrategy) -> dict:
    """Execute Phase A: Page Discovery. Returns manifest dict."""
    api = strategy.get("api", {})
    taxonomy = api.get("taxonomy", {})
    list_pages = taxonomy.get("list_pages", {})
    page_categories = taxonomy.get("page_categories", {})
    category_filters = taxonomy.get("category_filters", [])

    log.info("Phase A: Discovering pages...")
    pages = discovery_strategy.discover_pages(client, strategy)
    log.info("Discovered %d pages", len(pages))

    page_titles = [p["title"] for p in pages]
    log.info("Phase A: Discovering categories for %d pages...", len(page_titles))
    categories_map = discovery_strategy.discover_categories(client, page_titles)
    log.info("Categories discovered for %d pages", len(categories_map))

    log.info("Phase A: Fetching list page content (%d pages)...", len(list_pages))
    list_page_content = discovery_strategy.fetch_list_pages(client, list_pages)
    log.info("List page content fetched for %d pages", len(list_page_content))

    # Build manifest
    manifest = {
        "pages": [],
        "list_page_content": {},
    }
    for page in pages:
        title = page["title"]
        cats = categories_map.get(title, [])
        target_dir = discovery_strategy.classify_page(
            title, cats, list_pages, page_categories, category_filters
        )

        filename_config = api.get("filename", {})
        replacements = filename_config.get("replacements", {})
        safe_title = title
        for char, replacement in replacements.items():
            safe_title = safe_title.replace(char, replacement)
        safe_title = safe_title.replace(" ", "_")
        filename = f"{safe_title}.md"

        manifest["pages"].append({
            "title": title,
            "pageid": page.get("pageid"),
            "ns": page.get("ns", 0),
            "categories": cats,
            "target_directory": target_dir,
            "target_filename": filename,
        })

    manifest["list_page_content"] = list_page_content

    misc_count = sum(1 for p in manifest["pages"] if p["target_directory"] == "Misc")
    total_count = len(manifest["pages"])
    misc_pct = (misc_count / total_count * 100) if total_count > 0 else 0
    log.info("Phase A complete: %d pages classified. Misc: %d (%.1f%%)",
             total_count, misc_count, misc_pct)

    return manifest
