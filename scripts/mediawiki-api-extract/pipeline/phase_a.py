"""Phase A: Page Discovery."""

import logging

from ..client import ApiClient
from ..strategies import DiscoveryStrategy, title_to_filepath

log = logging.getLogger("mediawiki-api-extract")


def run_phase_a(client: ApiClient, strategy: dict, origin: str,
                discovery_strategy: DiscoveryStrategy,
                *,
                platform_variant: str = "standard") -> dict:
    """Execute Phase A: Page Discovery. Returns manifest dict."""
    api = strategy.get("api", {})
    taxonomy = api.get("taxonomy", {})
    list_pages = taxonomy.get("list_pages", {})
    page_categories = taxonomy.get("page_categories", {})
    category_filters = taxonomy.get("category_filters", [])

    log.info("Phase A: Discovering pages... (platform_variant=%s)", platform_variant)
    pages = discovery_strategy.discover_pages(client, strategy)
    log.info("Discovered %d pages", len(pages))

    # Fandom translation page filtering
    if platform_variant == "fandom":
        before = len(pages)
        pages = [p for p in pages if not (p["title"].endswith("/tr") or p["title"].endswith("_tr"))]
        filtered_tr = before - len(pages)
        if filtered_tr > 0:
            log.info("Filtered %d translation pages (_tr)", filtered_tr)

        # Fandom page existence verification via prop=info
        if platform_variant == "fandom" and pages:
            titles = [p["title"] for p in pages]
            existing_pages = []
            batch_size = 50
            for i in range(0, len(titles), batch_size):
                batch = titles[i:i + batch_size]
                try:
                    data = client.query(prop="info", titles="|".join(batch))
                    query_pages = data.get("query", {}).get("pages", {})
                    missing_titles = set()
                    for _pid, pinfo in query_pages.items():
                        if "missing" in pinfo:
                            missing_titles.add(pinfo.get("title", ""))
                    existing_pages.extend(p for p in pages[i:i + batch_size] if p["title"] not in missing_titles)
                except Exception as e:
                    log.warning("prop=info batch verification failed for batch %d-%d: %s", i, i + batch_size, e)
                    existing_pages.extend(pages[i:i + batch_size])
            before_verify = len(pages)
            pages = existing_pages
            filtered_missing = before_verify - len(pages)
            if filtered_missing > 0:
                pct = filtered_missing / before_verify * 100
                log.info("Filtered %d pages (missing in prop=info, %.1f%%)", filtered_missing, pct)

    page_titles = [p["title"] for p in pages]
    log.info("Phase A: Discovering categories for %d pages...", len(page_titles))
    categories_map = discovery_strategy.discover_categories(client, page_titles)
    log.info("Categories discovered for %d pages", len(categories_map))

    log.info("Phase A: Fetching list page content (%d pages)...", len(list_pages))
    try:
        list_page_content = discovery_strategy.fetch_list_pages(client, list_pages)
    except Exception as e:
        log.warning("Failed to fetch list page content: %s — continuing without", e)
        list_page_content = {}
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
