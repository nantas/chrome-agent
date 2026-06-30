"""Phase Convert — read from cache and convert to Markdown."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from ..registry import build_pipeline
from .. import cache as cache_mod
from ...strategies import (
    ExactTitleLinkResolver,
    SimpleSubstitutionTemplateProcessor,
)
from ...strategies import LinkResolver, TemplateProcessor
from scripts.lib.extraction.converter import HtmlToMarkdownConverter
from scripts.lib.extraction.preprocessor import preprocess_html
from ...strategies import convert_wikitext_to_markdown
from ...client import PageNotFoundError

from ..state import load_state, save_state, is_page_completed


def _first_image_name(images: list[str], extraction_config: dict | None) -> str | None:
    """Apply skip_patterns filter, return first image name (spaces to underscores) or None."""
    skip_patterns = (extraction_config or {}).get("image_filtering", {}).get("skip_patterns", [])
    filtered = images
    if skip_patterns:
        filtered = [img for img in images if not any(re.search(pat, img) for pat in skip_patterns)]
    return filtered[0].replace(" ", "_") if filtered else None

log = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Redirect detection helpers
# ---------------------------------------------------------------------------

_REDIRECT_MSG_RE = re.compile(
    r'class="redirectMsg"|>Redirect to:<', re.IGNORECASE
)
_REDIRECT_TARGET_RE = re.compile(
    r'class="redirectMsg".*?<a\s+href="/wiki/([^""]+)"',
    re.IGNORECASE | re.DOTALL,
)


def _detect_redirect(html: str) -> Optional[str]:
    """Detect if HTML is a redirect page. Returns target title or None."""
    if not html or not _REDIRECT_MSG_RE.search(html):
        return None
    m = _REDIRECT_TARGET_RE.search(html)
    if m:
        # URL-decode and underscore-to-space normalization
        from urllib.parse import unquote
        return unquote(m.group(1)).replace("_", " ")
    return ""  # redirect detected but target not extractable


def convert_single_page(raw: dict, page_info: dict, manifest_pages: list[dict],
                        domain: str, frontmatter_fields: list[str],
                        template_map: dict[str, str],
                        link_resolver: LinkResolver,
                        template_processor: TemplateProcessor,
                        extraction_config: Optional[dict] = None,
                        redirect_map: dict[str, str] | None = None) -> dict:
    """Convert a raw content dict to Markdown.

    Args:
        raw: Dict from fetch_single_page / cache with html/wikitext/images.
        page_info: Page manifest entry with title, target_directory, etc.
        manifest_pages: Full manifest page list (for link resolution).
        domain: Wiki domain.
        frontmatter_fields: Fields to extract into frontmatter.
        template_map: Template name mapping.
        link_resolver: Link resolver instance.
        template_processor: Template processor instance.
        extraction_config: Extraction rules from strategy.

    Returns:
        Result dict with title, status, content, warnings, frontmatter, rendered_html.
    """
    title = page_info["title"]
    source_dir = page_info["target_directory"]
    source_url = f"https://{domain}/wiki/{title.replace(' ', '_')}"

    # Determine conversion path:
    # 1. If cached content has a content_acquisition field, use it as primary heuristic
    # 2. Fall back to field presence detection for backward compat
    acq = raw.get("content_acquisition")
    html = raw.get("html")
    wikitext = raw.get("wikitext")

    is_html_rendered = acq == "html_rendered" or (html and not wikitext and not acq)
    is_wikitext = acq in ("wikitext_only", "hybrid_wikitext_plus_rendered") or (wikitext and not acq and not is_html_rendered)

    # HTML-rendered path
    if is_html_rendered:
        return _process_html_page(
            raw, title, source_dir, source_url, domain,
            manifest_pages, frontmatter_fields, extraction_config,
            redirect_map
        )

    # Wikitext path
    if is_wikitext and wikitext:
        md_content, warnings, frontmatter = convert_wikitext_to_markdown(
            wikitext, title, source_url, manifest_pages, source_dir,
            frontmatter_fields, template_map, link_resolver, template_processor, domain,
            redirect_map
        )

        result = {
            "title": title,
            "status": "ok",
            "content": md_content,
            "warnings": warnings,
            "frontmatter": frontmatter,
            "rendered_html": raw.get("rendered_html"),
        }

        # Inject images into frontmatter if available (applying skip_patterns)
        images = raw.get("images")
        if images and isinstance(images, list) and len(images) > 0:
            img_name = _first_image_name(images, extraction_config)
            if img_name:
                frontmatter["image"] = img_name
                from urllib.parse import quote as url_quote
                img_url = f"https://{domain}/Special:Redirect/file/{url_quote(img_name, safe='')}"
                if "---" in md_content:
                    end_fm = md_content.find("\n---", 3)
                    if end_fm >= 0:
                        insert_pos = end_fm + 4
                        img_md = f"\n\n![{img_name}]({img_url})\n"
                        result["content"] = md_content[:insert_pos] + img_md + md_content[insert_pos:]

        return result

    # Both html and wikitext present or hybrid strategy — use HTML path
    if html and not is_wikitext:
        return _process_html_page(
            raw, title, source_dir, source_url, domain,
            manifest_pages, frontmatter_fields, extraction_config,
            redirect_map
        )

    return {"title": title, "status": "empty", "error": "No content available (html and wikitext both empty)"}


# ---------------------------------------------------------------------------

def _process_html_page(raw: dict, title: str, source_dir: str, source_url: str,
                       domain: str, manifest_pages: list[dict],
                       frontmatter_fields: list[str],
                       extraction_config: dict | None = None,
                       redirect_map: dict[str, str] | None = None) -> dict:
    """Process a page using HTML-rendered content."""
    html = raw.get("html") or ""
    if not html:
        return {"title": title, "status": "empty", "error": "Empty HTML"}

    converter = HtmlToMarkdownConverter(wiki_domain=domain, extraction_config=extraction_config)
    converter.build_link_index(manifest_pages, redirect_map)

    # Preprocess HTML with the same pipeline as explore (context="explore") so that
    # cleanup operations run identically in both paths — explore samples then
    # serve as a valid quality proxy for pipeline production output.
    # NOTE: extract_card_stats() below still uses the raw `html` (needs the intact
    # infobox structure), so the preprocessed result stays in a local var.
    cleaned_html = preprocess_html(html, extraction_config or {}, context="explore")
    md_content = converter.convert_body(cleaned_html, source_dir=source_dir)

    # Build frontmatter
    frontmatter = {"title": title, "source_url": source_url}

    # Try to extract frontmatter from wikitext fallback if available
    wikitext = raw.get("wikitext")
    if wikitext:
        # Use a simple template processor for frontmatter extraction
        from ...strategies import SimpleSubstitutionTemplateProcessor
        tp = SimpleSubstitutionTemplateProcessor()
        fm = tp.extract_frontmatter(wikitext, frontmatter_fields)
        frontmatter.update(fm)

    # Inject first image into frontmatter if available (applying skip_patterns)
    images = raw.get("images")
    if images and isinstance(images, list) and len(images) > 0:
        img_name = _first_image_name(images, extraction_config)
        if img_name:
            frontmatter["image"] = img_name

    # Assemble final content with YAML frontmatter
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
            fm_lines.append(f'{key}: "{value.replace(chr(34), chr(92)+chr(34))}"')
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---\n")

    body = md_content.strip()
    if body and not body.startswith("#"):
        body = f"# {title}\n\n{body}"
    elif not body:
        body = f"# {title}\n"

    # Inject complete card image after title if available
    img_name = frontmatter.get("image")
    if img_name:
        img_url = f"https://{domain}/images/{img_name}"
        img_block = f"\n![{title}]({img_url})\n"
        # Insert after first heading
        first_nl = body.find("\n")
        if first_nl >= 0:
            body = body[:first_nl] + img_block + body[first_nl:]

    # Inject structured card stats if DRUID infobox was present
    from ...strategies import extract_card_stats
    card_stats = extract_card_stats(html, domain=domain)
    if card_stats:
        # Insert card stats after the first section (after first --- divider or before first ##)
        first_section = body.find("\n## ")
        if first_section >= 0:
            body = body[:first_section] + "\n\n" + card_stats + body[first_section:]
        else:
            body = body + "\n\n" + card_stats

    full_content = "\n".join(fm_lines) + body + "\n"

    return {
        "title": title,
        "status": "ok",
        "content": full_content,
        "warnings": [],
        "frontmatter": frontmatter,
        "rendered_html": html,
    }


# ---------------------------------------------------------------------------

def run_convert(output_dir: str, manifest: dict, strategy: dict,
                      domain: str, repo_root: str,
                      resume_enabled: bool = False) -> tuple[dict, dict]:
    """Execute Phase Convert: read from cache and convert to Markdown.

    No network requests are made. All input comes from local cache files.

    Args:
        output_dir: Output directory for extracted content.
        manifest: Page manifest dict with ``pages`` list.
        strategy: Strategy configuration dict.
        domain: Wiki domain.
        repo_root: Repository root path for cache directory.

    Returns:
        (results_map, stats) where results_map is title -> result dict.
    """
    platform = strategy.get("api", {}).get("platform", "mediawiki")
    api = strategy.get("api", {})
    output_config = api.get("output", {})
    frontmatter_fields = output_config.get("frontmatter_fields", [])
    template_map = output_config.get("template_map", {})
    extraction_config = strategy.get("extraction", {})

    # Build link resolver and template processor from strategy
    link_resolver_strategies = strategy.get("api", {}).get("content_profile", {}).get("link_resolver", "exact_title_match")
    template_processor_strategies = strategy.get("api", {}).get("content_profile", {}).get("template_processor", "simple_substitution")

    # Use strategy-derived instances
    strategies_obj = None
    try:
        strategies_obj = build_pipeline(strategy, domain)
    except ValueError:
        pass

    link_resolver = strategies_obj.link_resolver if strategies_obj else ExactTitleLinkResolver()
    template_processor = strategies_obj.template_processor if strategies_obj else SimpleSubstitutionTemplateProcessor()

    pages = manifest["pages"]
    results = {}
    success_count = 0
    cache_miss_count = 0
    failed_count = 0
    flush_counter = 0
    flush_interval = 50

    # Load resume state if enabled
    state = load_state(output_dir) if resume_enabled else None
    completed_pages_set = set(state.get("completed_pages", [])) if state else set()

    log.info("Phase Convert: converting %d pages from cache (platform=%s, resume=%s)...",
             len(pages), platform, resume_enabled)

    redirect_map: dict[str, str] = {}  # source_title -> target_title
    redirect_titles: set[str] = set()

    # Pre-scan: detect redirect pages and build full redirect_map
    for page in pages:
        title = page["title"]
        raw = cache_mod.load_page_cache(repo_root, platform, domain, title)
        if raw is None:
            continue
        rendered_html = raw.get("rendered_html") or raw.get("html") or ""
        redirect_target = _detect_redirect(rendered_html)
        if redirect_target is not None:
            redirect_titles.add(title)
            if redirect_target:
                redirect_map[title] = redirect_target

    if redirect_titles:
        log.info("Pre-scan: detected %d redirect pages", len(redirect_titles))

    # Pre-scan: detect target_path conflicts
    conflict_titles: set[str] = set()
    target_path_map: dict[str, list[str]] = {}  # path -> [titles]
    for page in pages:
        t_dir = page.get("target_directory", "")
        t_file = page.get("target_filename", "")
        path_key = os.path.join(t_dir, t_file) if t_dir or t_file else ""
        if path_key:
            if path_key not in target_path_map:
                target_path_map[path_key] = []
            target_path_map[path_key].append(page["title"])
    for path_key, titles in target_path_map.items():
        if len(titles) > 1:
            winner = titles[0]
            losers = titles[1:]
            conflict_titles.update(losers)
            log.error("Target path conflict: '%s' — winner: '%s', losers: %s",
                      path_key, winner, losers)

    redirect_count = 0
    for page in pages:
        title = page["title"]
        target_dir = page.get("target_directory", "")
        target_filename = page.get("target_filename", "")

        # Resume: skip already converted pages
        if resume_enabled and completed_pages_set and title in completed_pages_set:
            filepath = os.path.join(output_dir, target_dir, target_filename)
            if os.path.exists(filepath):
                results[title] = {
                    "title": title,
                    "status": "ok",
                    "content": None,
                    "skipped": True,
                }
                success_count += 1
                log.debug("Page '%s' skipped (already converted)", title)
                continue

        # Load from cache
        raw = cache_mod.load_page_cache(repo_root, platform, domain, title)
        if raw is None:
            cache_miss_count += 1
            results[title] = {
                "title": title,
                "status": "error",
                "error": "cache_miss",
            }
            log.warning("Cache miss for '%s' — skipping (run --phase fetch first)", title)
            continue

        # Check content_acquisition mismatch warning
        current_acq = strategy.get("api", {}).get("content_profile", {}).get("content_acquisition")
        cached_acq = raw.get("content_acquisition")
        if current_acq and cached_acq and current_acq != cached_acq:
            log.warning("Content acquisition mismatch for '%s': cached='%s', current='%s'. Conversion may be incomplete. Use --re-fetch to refresh.",
                        title, cached_acq, current_acq)

        try:
            # Skip target-conflict pages (detected in pre-scan)
            if title in conflict_titles:
                results[title] = {"title": title, "status": "target_conflict"}
                failed_count += 1
                log.error("Skipping '%s': target path conflict", title)
                continue

            # Skip redirect pages (detected in pre-scan)
            if title in redirect_titles:
                redirect_count += 1
                results[title] = {
                    "title": title,
                    "status": "redirect",
                    "redirect_target": redirect_map.get(title),
                }
                if title in redirect_map:
                    log.info("Redirect detected: '%s' → '%s'", title, redirect_map[title])
                else:
                    log.info("Redirect detected: '%s' (target not extractable)", title)
                continue

            result = convert_single_page(
                raw, page, pages, domain,
                frontmatter_fields, template_map,
                link_resolver, template_processor, extraction_config,
                redirect_map
            )
            results[title] = result
            if result["status"] == "ok":
                success_count += 1

                # Incremental write: write .md file immediately
                if result.get("content"):
                    filepath = os.path.join(output_dir, target_dir, target_filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(result["content"])

                # Track completed and flush state periodically
                completed_pages_set.add(title)
                flush_counter += 1
                if flush_counter >= flush_interval:
                    if state is not None:
                        state["completed_pages"] = list(completed_pages_set)
                        save_state(output_dir, state)
                    flush_counter = 0
            else:
                failed_count += 1
                log.warning("Convert failed for '%s': %s", title, result.get("error", "unknown"))
        except Exception as e:
            failed_count += 1
            results[title] = {"title": title, "status": "error", "error": str(e)}
            log.warning("Convert failed for '%s': %s", title, e)

    # Final state flush
    if state is not None and completed_pages_set:
        state["completed_pages"] = list(completed_pages_set)
        save_state(output_dir, state)

    stats = {
        "total": len(pages),
        "success": success_count,
        "failure": failed_count,
        "cache_miss": cache_miss_count,
        "failed": failed_count,
        "redirect": redirect_count,
    }
    log.info("Convert phase complete: %d total, %d converted, %d redirect, %d cache_miss, %d failed",
             stats["total"], success_count, redirect_count, cache_miss_count, failed_count)

    return results, stats
