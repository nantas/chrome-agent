"""Phase C: Output Assembly."""

import logging
import os
import re
import time

from ..strategies import LinkResolver, ListPageAssembler
from ..strategies import split_card_list_pages

log = logging.getLogger("mediawiki-api-extract")


def run_phase_c(output_dir: str, manifest: dict, results: dict,
                strategy: dict, domain: str,
                list_page_assembler: ListPageAssembler,
                link_resolver: LinkResolver,
                client=None) -> dict:
    """Execute Phase C: Output Assembly. Returns stats dict."""
    api = strategy.get("api", {})
    taxonomy = api.get("taxonomy", {})
    list_pages = taxonomy.get("list_pages", {})

    log.info("Phase C: Assembling output in %s...", output_dir)

    # Create directories
    dirs_created = set()
    for page in manifest["pages"]:
        target_dir = page["target_directory"]
        dir_path = os.path.join(output_dir, target_dir)
        if target_dir not in dirs_created:
            os.makedirs(dir_path, exist_ok=True)
            dirs_created.add(target_dir)

    # Write individual page files
    written = 0
    for page in manifest["pages"]:
        title = page["title"]
        target_dir = page["target_directory"]
        filename = page["target_filename"]

        result = results.get(title)
        if not result or result.get("status") != "ok":
            continue

        content = result.get("content")
        if content is None:
            # Result loaded from saved state — file already written
            written += 1
            continue
        content = content.replace("<!-- DPL_TABLE_PLACEHOLDER -->", "")
        filepath = os.path.join(output_dir, target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

    log.info("Written %d page files", written)

    # Generate category index pages (ns=14)
    category_pages_written = 0
    if client is not None:
        for page in manifest["pages"]:
            if page.get("ns") != 14:
                continue
            title = page["title"]
            target_dir = page["target_directory"]
            filename = page["target_filename"]
            dir_path = os.path.join(output_dir, target_dir)
            if target_dir not in dirs_created:
                os.makedirs(dir_path, exist_ok=True)
                dirs_created.add(target_dir)
            index_path = os.path.join(dir_path, filename)

            # Get description from Phase B result if available
            description = ""
            result = results.get(title)
            if result and result.get("status") == "ok":
                content = result.get("content", "")
                # Extract text after frontmatter
                if content.startswith("---"):
                    end_fm = content.find("\n---", 3)
                    if end_fm >= 0:
                        body = content[end_fm + 4:].lstrip("\n")
                        # Strip heading
                        body = re.sub(r'^#+\s.*$', '', body, flags=re.MULTILINE).strip()
                        description = body

            # Fetch category members
            lines = ["---"]
            lines.append(f'title: "{title}"')
            lines.append(f"source_url: https://{domain}/wiki/{title.replace(' ', '_')}")
            lines.append("---")
            lines.append("")
            if description:
                lines.append(description)
                lines.append("")

            try:
                cmtitle = title.replace(" ", "_")
                members = []
                subcats = []
                continue_token = None
                while True:
                    params = {
                        "list": "categorymembers",
                        "cmtitle": cmtitle,
                        "cmlimit": 500,
                    }
                    if continue_token:
                        params["cmcontinue"] = continue_token
                    data = client.query(**params)
                    for item in data.get("query", {}).get("categorymembers", []):
                        if item.get("ns") == 14:
                            subcats.append(item["title"])
                        else:
                            members.append(item["title"])
                    if "continue" in data:
                        continue_token = data["continue"].get("cmcontinue")
                    else:
                        break

                if members:
                    lines.append("## Pages")
                    lines.append("")
                    for m in sorted(members):
                        # Find target path in manifest
                        target = None
                        for p in manifest["pages"]:
                            if p["title"] == m:
                                target = p
                                break
                        if target:
                            rel_path = target["target_filename"]
                            if target["target_directory"] != target_dir:
                                rel_dir = target["target_directory"]
                                if rel_dir:
                                    rel_path = f"{rel_dir}/{rel_path}"
                            page_name = m.replace("_", " ")
                            lines.append(f"- [{page_name}]({rel_path})")
                        else:
                            page_name = m.replace("_", " ")
                            safe = m.replace(" ", "_").replace(":", "_") + ".md"
                            lines.append(f"- [{page_name}]({safe})")
                    lines.append("")

                if subcats:
                    lines.append("## Subcategories")
                    lines.append("")
                    for s in sorted(subcats):
                        sub_name = s.replace("_", " ")
                        sub_slug = s.replace("Category:", "").replace(" ", "_").replace(":", "_")
                        lines.append(f"- [{sub_name}]({sub_slug}/index.md)")
                    lines.append("")
            except Exception as e:
                log.warning("Failed to fetch category members for %s: %s", title, e)

            with open(index_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            category_pages_written += 1

        if category_pages_written > 0:
            log.info("Written %d category index pages", category_pages_written)

    # Generate index.md for each directory using Phase B converted content
    list_page_content = manifest.get("list_page_content", {})
    frontmatter_fields = api.get("output", {}).get("frontmatter_fields", [])

    for page_title, directory in list_pages.items():
        # Resolve actual target directory from manifest (accounts for namespace prefixing)
        actual_dir = directory
        for page in manifest["pages"]:
            if page["title"] == page_title:
                actual_dir = page["target_directory"]
                break

        dir_path = os.path.join(output_dir, actual_dir)
        if actual_dir not in dirs_created:
            os.makedirs(dir_path, exist_ok=True)
            dirs_created.add(actual_dir)
        index_path = os.path.join(dir_path, "index.md")

        pages_in_dir = []
        for page in manifest["pages"]:
            if page["target_directory"] == actual_dir:
                page_result = results.get(page["title"])
                fm = page_result.get("frontmatter", {}) if page_result and page_result.get("status") == "ok" else {}
                pages_in_dir.append({
                    "title": page["title"],
                    "filename": page["target_filename"],
                    "frontmatter": fm,
                })

        list_result = results.get(page_title)
        body_content = None
        if list_result and list_result.get("status") == "ok":
            body_content = list_result.get("content")

        if body_content and ("DPL_TABLE_PLACEHOLDER" in body_content or list_result.get("rendered_html")):
            list_input = {
                "wikitext": body_content,
                "rendered_html": list_result.get("rendered_html") if list_result else None,
            }
            assembled = list_page_assembler.assemble_index(
                page_title, pages_in_dir, list_input, frontmatter_fields, domain
            )
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(assembled)
        else:
            stripped_body = body_content
            if stripped_body and stripped_body.startswith('---'):
                end_fm = stripped_body.find('\n---', 3)
                if end_fm >= 0:
                    stripped_body = stripped_body[end_fm + 4:].lstrip('\n')

            lines = ["---"]
            lines.append(f'title: "{page_title}"')
            lines.append(f"source_url: https://{domain}/wiki/{page_title.replace(' ', '_')}")
            lines.append(f'category: "{page_title}"')
            lines.append("---")
            lines.append("")
            if stripped_body:
                lines.append(stripped_body)
                lines.append("")
            else:
                lines.append(f"# {page_title}")
                lines.append("")
            lines.append("## Pages in this category")
            lines.append("")
            for p in sorted(pages_in_dir, key=lambda x: x["filename"]):
                page_name = p["filename"].replace(".md", "").replace("_", " ")
                lines.append(f"- [{page_name}]({p['filename']})")
            lines.append("")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        # Generate card list sub-pages from rendered HTML
        list_result = results.get(page_title)
        if list_result and list_result.get("rendered_html"):
            rendered = list_result["rendered_html"]
            sub_pages, info = split_card_list_pages(
                rendered, output_dir, manifest["pages"], domain, page_title
            )
            if sub_pages > 0:
                log.info("Split %s into %d card sub-pages (by color x rarity)", page_title, sub_pages)
                written += sub_pages
                # Replace index.md with directory navigation
                nav_lines = ["---"]
                nav_lines.append(f'title: "{page_title}"')
                nav_lines.append(f"source_url: https://{domain}/wiki/{page_title.replace(' ', '_')}")
                nav_lines.append("---")
                nav_lines.append("")
                nav_lines.append(f"# {page_title}")
                nav_lines.append("")
                nav_lines.append("Card lists grouped by character and rarity.")
                nav_lines.append("")
                colors = sorted(set(it["color"] for it in info))
                for c in colors:
                    cd = c.replace(" ", "_").replace(".", "")
                    count = sum(it["count"] for it in info if it["color"] == c)
                    nav_lines.append(f"- [{c}]({cd}/index.md) ({count} cards)")
                nav_lines.append("")
                with open(index_path, "w", encoding="utf-8") as f_nav:
                    f_nav.write("\n".join(nav_lines) + "\n")

        # Remove redundant list page file
        list_page_filename = None
        for page in manifest["pages"]:
            if page["title"] == page_title:
                list_page_filename = page["target_filename"]
                break
        if list_page_filename:
            redundant_path = os.path.join(dir_path, list_page_filename)
            if os.path.exists(redundant_path) and os.path.abspath(redundant_path) != os.path.abspath(index_path):
                os.remove(redundant_path)
                written -= 1

    # Generate index.md for directories that don't have one yet
    for dir_name in sorted(dirs_created):
        index_path = os.path.join(output_dir, dir_name, "index.md")
        if os.path.exists(index_path):
            continue
        dir_pages = [p for p in manifest["pages"]
                     if p["target_directory"] == dir_name and p["title"] not in list_pages]
        lines = ["---"]
        lines.append(f'title: "{dir_name}"')
        lines.append("source_url: null")
        lines.append(f'category: "{dir_name}"')
        lines.append("---")
        lines.append("")
        lines.append(f"# {dir_name}")
        lines.append("")
        lines.append("## Pages in this category")
        lines.append("")
        for p in sorted(dir_pages, key=lambda x: x["target_filename"]):
            page_name = p["target_filename"].replace(".md", "").replace("_", " ")
            lines.append(f"- [{page_name}]({p['target_filename']})")
        lines.append("")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # Generate Misc index
    misc_dir = os.path.join(output_dir, "Misc")
    if os.path.isdir(misc_dir):
        misc_files = [f for f in os.listdir(misc_dir) if f.endswith(".md") and f != "index.md"]
        if misc_files:
            lines = ["---"]
            lines.append('title: "Misc"')
            lines.append("source_url: null")
            lines.append('category: "Misc"')
            lines.append("---")
            lines.append("")
            lines.append("# Misc")
            lines.append("")
            lines.append("## Pages in this category")
            lines.append("")
            for fname in sorted(misc_files):
                page_name = fname.replace(".md", "").replace("_", " ")
                lines.append(f"- [{page_name}]({fname})")
            lines.append("")
            with open(os.path.join(misc_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

    # Generate top-level _index.md
    total_pages = len(manifest["pages"])
    misc_count = sum(1 for p in manifest["pages"] if p["target_directory"] == "Misc")
    index_lines = ["---"]
    index_lines.append(f"crawl_date: \"{time.strftime('%Y-%m-%d')}\"")
    index_lines.append(f"total_pages: {total_pages}")
    index_lines.append(f"source_domain: \"{domain}\"")
    index_lines.append("---")
    index_lines.append("")
    index_lines.append(f"# {domain} — Wiki Crawl Index")
    index_lines.append("")
    index_lines.append(f"- **Date**: {time.strftime('%Y-%m-%d')}")
    index_lines.append(f"- **Total pages**: {total_pages}")
    index_lines.append(f"- **Misc pages**: {misc_count} ({misc_count/total_pages*100:.1f}%)" if total_pages > 0 else "")
    index_lines.append("")
    index_lines.append("## Directories")
    index_lines.append("")
    for dir_name in sorted(dirs_created):
        dir_files = [p for p in manifest["pages"] if p["target_directory"] == dir_name]
        index_lines.append(f"- [{dir_name}]({dir_name}/index.md) ({len(dir_files)} pages)")
    index_lines.append("")

    with open(os.path.join(output_dir, "_index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    log.info("Phase C complete: %d pages written, %d directories", written, len(dirs_created))

    return {
        "pages_written": written,
        "directories": len(dirs_created),
        "misc_count": misc_count,
        "misc_pct": misc_count / total_pages * 100 if total_pages > 0 else 0,
    }
