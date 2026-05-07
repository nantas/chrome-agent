"""Phase C: Output Assembly."""

import logging
import os
import re
import time

from .strategies import LinkResolver, ListPageAssembler

log = logging.getLogger("mediawiki-api-extract")


def run_phase_c(output_dir: str, manifest: dict, results: dict,
                strategy: dict, domain: str,
                list_page_assembler: ListPageAssembler,
                link_resolver: LinkResolver) -> dict:
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

        content = result["content"]
        content = content.replace("<!-- DPL_TABLE_PLACEHOLDER -->", "")
        filepath = os.path.join(output_dir, target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

    log.info("Written %d page files", written)

    # Generate index.md for each directory using Phase B converted content
    list_page_content = manifest.get("list_page_content", {})
    frontmatter_fields = api.get("output", {}).get("frontmatter_fields", [])

    for page_title, directory in list_pages.items():
        index_path = os.path.join(output_dir, directory, "index.md")
        dir_path = os.path.join(output_dir, directory)

        pages_in_dir = []
        for page in manifest["pages"]:
            if page["target_directory"] == directory:
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
            body_content = list_result["content"]

        if body_content and "DPL_TABLE_PLACEHOLDER" in body_content:
            assembled = list_page_assembler.assemble_index(
                page_title, pages_in_dir, body_content, frontmatter_fields, domain
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
            lines.append(f"source_url: https://{domain}/w/{page_title.replace(' ', '_')}")
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
