"""Phase A: Page Discovery."""

import logging

from .client import ApiClient
from .strategies import DiscoveryStrategy, title_to_filepath

log = logging.getLogger("pipeline")


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
    namespaces = api.get("namespaces", [api.get("namespace", 0)])
    if not isinstance(namespaces, list):
        namespaces = [namespaces]

    manifest = {
        "pages": [],
        "list_page_content": {},
        "namespaces": namespaces,
    }
    for page in pages:
        title = page["title"]
        cats = categories_map.get(title, [])
        ns = page.get("ns", 0)

        # Use semantic directory mapping for path
        target_dir, filename = title_to_filepath(title, ns)

        # For non-category pages, also run classification for subdirectory hint
        if ns != 14:
            classified_dir = discovery_strategy.classify_page(
                title, cats, list_pages, page_categories, category_filters, namespace=ns
            )
            # If classification gives a more specific subdir, append it
            # Strip namespace prefix if target_dir already provides it
            if classified_dir and classified_dir != "Misc":
                if target_dir == "Slay_the_Spire_2" and classified_dir.startswith("StS2/"):
                    classified_dir = classified_dir[len("StS2/"):]
                if target_dir == "" and classified_dir.startswith("StS1/"):
                    classified_dir = classified_dir[len("StS1/"):]
                if target_dir:
                    target_dir = f"{target_dir}/{classified_dir}"
                else:
                    target_dir = classified_dir

        manifest["pages"].append({
            "title": title,
            "pageid": page.get("pageid"),
            "ns": ns,
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
