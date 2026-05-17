"""SampleConverter — fetch sample pages and convert to Markdown using scaffold extraction rules."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString
import re
import urllib.request
import urllib.parse


def _fetch_sample(
    repo_root: str,
    url: str,
    engine: str,
    output_path: str,
) -> dict:
    """Fetch a single sample page using the determined engine."""
    if engine in ("scrapling-get", "get"):
        preflight = subprocess.run(
            ["./scripts/scrapling-cli.sh", "preflight", "--no-install"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        cli = None
        for line in (preflight.stdout + preflight.stderr).split("\n"):
            if line.startswith("RESOLVED_CLI_PATH="):
                cli = line.split("=", 1)[1]
                break
        if cli:
            result = subprocess.run(
                [cli, "extract", "get", url, output_path],
                capture_output=True,
                text=True,
                cwd=repo_root,
            )
            return {
                "ok": result.returncode == 0 and os.path.exists(output_path),
                "path": output_path,
                "error": result.stderr if result.returncode != 0 else None,
            }
        return {"ok": False, "error": "Scrapling CLI not available"}

    elif engine in ("cloakbrowser-fetch", "cloakbrowser"):
        script = os.path.join(repo_root, "scripts", "cloakbrowser_fetcher.py")
        result = subprocess.run(
            ["python3", script, url, "--output", output_path, "--json"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        try:
            parsed = json.loads(result.stdout)
            return {
                "ok": parsed.get("ok", False),
                "path": output_path,
                "error": parsed.get("error") if not parsed.get("ok") else None,
            }
        except json.JSONDecodeError:
            return {"ok": False, "error": result.stderr or result.stdout}

    elif engine == "mediawiki-api":
        # mediawiki-api requires _fetch_via_mediawiki_api (called from convert())
        return {"ok": False, "error": "mediawiki-api engine requires _fetch_via_mediawiki_api call"}

    elif engine in ("obscura-fetch", "obscura"):
        managed = Path.home() / ".cache" / "chrome-agent-obscura" / "bin" / "obscura"
        env = os.environ.get("OBSCURA_CLI_PATH")
        cli = env if env and os.path.exists(env) else str(managed)
        if os.path.exists(cli):
            result = subprocess.run(
                [cli, "fetch", url, "--dump", "html", "--quiet", "--output", output_path],
                capture_output=True,
                text=True,
                cwd=repo_root,
            )
            return {
                "ok": result.returncode == 0 and os.path.exists(output_path),
                "path": output_path,
                "error": result.stderr if result.returncode != 0 else None,
            }
        return {"ok": False, "error": "Obscura CLI not available"}

    return {"ok": False, "error": f"Unknown engine: {engine}"}


def _fetch_via_mediawiki_api(
    base_url: str,
    page_title: str,
    output_path: str,
) -> dict:
    """Fetch page HTML via MediaWiki action=parse API with redirect following."""
    encoded = urllib.parse.quote(page_title, safe="")
    url = (
        f"{base_url}/api.php?action=parse&page={encoded}"
        f"&redirects=true&prop=text|wikitext|sections|displaytitle&format=json"
    )
    headers = {"User-Agent": "ChromeAgent/1.0 (sample-converter)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        if "error" in data:
            return {
                "ok": False,
                "error": data["error"].get("info", str(data["error"])),
            }
        html = data["parse"]["text"]["*"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "path": output_path, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _extract_infobox(
    soup: BeautifulSoup,
    infobox_cfg: dict,
    base_url: str,
    skip_patterns: list[str],
) -> str:
    """Generic infobox extraction — reads selectors from config.

    Uses descendants with deduplication to handle arbitrary nesting depth
    without double-counting elements inside wrappers like <a><img></a>.
    """
    container = soup.select_one(infobox_cfg["selector"])
    if not container:
        return ""

    field_sel = infobox_cfg.get("field_selector", "tr")
    label_sel = infobox_cfg.get("label_selector", "th")
    value_sel = infobox_cfg.get("value_selector", "td")

    lines = ["## Infobox", "", "| Field | Value |", "| --- | --- |"]

    for field in container.select(field_sel):
        label_el = field.select_one(label_sel)
        value_el = field.select_one(value_sel)
        if not label_el:
            continue
        key = label_el.get_text(strip=True)
        if not value_el:
            lines.append(f"| {key} | |")
            continue

        # Walk descendants with deduplication to avoid double-counting
        # img inside <a><img></a> must not be counted twice
        processed = set()
        val_parts = []

        for child in value_el.descendants:
            if id(child) in processed:
                continue
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    val_parts.append(text)
            elif child.name == "img":
                src = child.get("src", "")
                alt = child.get("alt", "")
                if not src:
                    processed.update(id(c) for c in child.descendants)
                    continue
                if skip_patterns and any(re.search(p, src) for p in skip_patterns):
                    processed.update(id(c) for c in child.descendants)
                    continue
                if base_url and src.startswith("/"):
                    src = base_url + src
                val_parts.append(f"![{alt}]({src})")
                processed.update(id(c) for c in child.descendants)
            elif child.name == "a":
                imgs = child.find_all("img")
                if imgs and not child.get_text(strip=True):
                    # Image-only link: extract images, mark all descendants processed
                    for img in imgs:
                        s = img.get("src", "")
                        a = img.get("alt", "")
                        if not s:
                            continue
                        if skip_patterns and any(re.search(p, s) for p in skip_patterns):
                            continue
                        if base_url and s.startswith("/"):
                            s = base_url + s
                        val_parts.append(f"![{a}]({s})")
                    processed.update(id(c) for c in child.descendants)
                else:
                    text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if href.startswith("/") and base_url:
                        href = base_url + href
                    if text:
                        val_parts.append(f"[{text}]({href})")
                    processed.update(id(c) for c in child.descendants)

        val = " ".join(val_parts).strip()
        if key and val:
            lines.append(f"| {key} | {val} |")

    if len(lines) <= 4:
        return ""
    return "\n".join(lines)

def _apply_extraction(
    html: str,
    extraction_rules: dict,
    known_pages: set[str],
) -> str:
    """Apply extraction rules from config to HTML — pure config interpreter.

    No site-specific class names or HTML structure assumptions.
    All behavior is driven by extraction_rules (from strategy frontmatter).
    """
    soup = BeautifulSoup(html, "html.parser")
    base_url = extraction_rules.get("image_handling", {}).get("base_url", "")
    skip_patterns = extraction_rules.get("image_filtering", {}).get("skip_patterns", [])

    # --- Phase 1: Extract structured infobox (config-driven) ---
    infobox_cfg = extraction_rules.get("infobox", {})
    infobox_md = ""
    if infobox_cfg.get("enabled") and infobox_cfg.get("selector"):
        infobox_md = _extract_infobox(soup, infobox_cfg, base_url, skip_patterns)
        for el in soup.select(infobox_cfg["selector"]):
            el.decompose()

    # --- Phase 2: Strip elements matching configured selectors ---
    for sel in extraction_rules.get("cleanup_selectors", []):
        for el in soup.select(sel):
            el.decompose()

    # --- Phase 3: Lazyload fix (config-driven) ---
    lazyload_cfg = extraction_rules.get("lazyload", {})
    if lazyload_cfg.get("enabled"):
        placeholder = lazyload_cfg.get("placeholder_pattern", "")
        src_attr = lazyload_cfg.get("real_src_attr", "")
        if placeholder and src_attr:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                data_src = img.get(src_attr, "")
                if placeholder in src and data_src:
                    img["src"] = data_src

    # --- Phase 4: Cleanup operations (read from config) ---
    cleanup = extraction_rules.get("cleanup", [])

    if "strip_fandom_infobox_tables" in cleanup:
        for cls in ["item-table-header", "item-table-body", "item-table-description",
                    "item-table-appearance", "infobox-table", "portable-infobox"]:
            for el in soup.find_all("table", class_=lambda x: x and cls in x):
                el.decompose()

    if "convert_ambox_to_text" in cleanup:
        for el in soup.find_all("table", class_=lambda x: x and "ambox" in x):
            text = el.get_text(strip=True)
            new_p = soup.new_tag("p")
            new_p.string = f"\u26a0\ufe0f {text}" if text else ""
            el.replace_with(new_p)

    if "unwrap_image_wrappers" in cleanup:
        for a in soup.find_all("a"):
            children = list(a.children)
            non_empty = [c for c in children if not (isinstance(c, str) and c.strip() == "")]
            if len(non_empty) == 1 and getattr(non_empty[0], "name", None) == "img":
                a.unwrap()
            elif a.get("class") and "image" in a.get("class", []):
                imgs = a.find_all("img")
                if imgs and not a.get_text(strip=True):
                    a.unwrap()

    # Remove decorative images (config-driven skip patterns)
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if any(re.search(p, src) for p in skip_patterns):
            img.decompose()

    # --- Phase 5: Content selection ---
    selector = extraction_rules.get("selectors", {}).get("content", "body")
    content = soup.select_one(selector) or soup.select_one("body") or soup

    # Convert to Markdown
    import markdownify
    md = markdownify.markdownify(
        str(content),
        heading_style="atx",
        keep_inline_images_in=["td", "th", "span", "a", "div", "p", "li"],
    )

    # Prepend infobox if extracted
    if infobox_md:
        md = infobox_md + "\n\n" + md

    # --- Phase 6: Post-conversion normalization (config-driven) ---
    normalization = extraction_rules.get("text_normalization", [])
    if "fix_spaces" in normalization:
        md = re.sub(r"([a-zA-Z])(\d+(?:\.\d+)*)([a-zA-Z])", r"\1 \2 \3", md)
        md = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", md)
        md = re.sub(r"(\!\[[^\]]*\]\([^)]+\))(\!\[)", r"\1 \2", md)
    if "normalize_blank_lines" in normalization:
        md = re.sub(r"\n{3,}", "\n\n", md)
    if "deduplicate_words" in normalization:
        md = re.sub(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+\1\b", r"\1", md)

    # Remove empty headers
    md = re.sub(r"#{1,6}\s*\n", "\n", md)

    # URL conversion (config-driven)
    url_cfg = extraction_rules.get("url_conversion", {})
    if url_cfg.get("enabled") and base_url:
        md = re.sub(
            r"!\[([^\]]*)\]\((/images/[^)]+)\)",
            rf"![\1]({base_url}\2)", md,
        )
        md = re.sub(
            r"\[([^\]]*)\]\((/wiki/[^)]+)\)",
            rf"[\1]({base_url}\2)", md,
        )

    # YouTube embed cleanup (config-driven)
    yt_cfg = extraction_rules.get("youtube_cleanup", {})
    if yt_cfg.get("enabled"):
        md = re.sub(
            r"Load video\s*\nYouTube\s*\n.*?ContinueDismiss",
            "", md, flags=re.S,
        )

    # Clean escape artifacts
    md = md.replace(r"\*\*\*", "***")
    md = re.sub(r"\\(\*+)", r"\1", md)

    # Clean empty parens
    md = re.sub(r"\(\s*\)", "", md)

    return md.strip()



def convert(
    repo_root: str,
    samples: list[dict],
    extraction_rules: dict,
    engine: str,
    run_dir: str,
) -> list[dict]:
    """Fetch and convert sample pages.

    Args:
        samples: List of {url, title, type}
        extraction_rules: Scaffold extraction config
        engine: Preferred engine
        run_dir: Output directory

    Returns:
        List of {title, url, type, markdown, html_length, ok, error}
    """
    # Build known pages set for link resolution
    known_pages = {s["title"] for s in samples}

    results = []
    for sample in samples:
        output_path = os.path.join(run_dir, f"sample_{sample['title'].replace(' ', '_').replace('/', '_')}.html")

        if engine == "mediawiki-api":
            base_url = extraction_rules.get("image_handling", {}).get("base_url", "")
            fetch_result = _fetch_via_mediawiki_api(base_url, sample["title"], output_path)
        else:
            fetch_result = _fetch_sample(repo_root, sample["url"], engine, output_path)
        if not fetch_result["ok"]:
            results.append({
                "title": sample["title"],
                "url": sample["url"],
                "type": sample.get("type", "article"),
                "markdown": "",
                "html_length": 0,
                "ok": False,
                "error": fetch_result.get("error", "Fetch failed"),
            })
            continue

        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()

        md = _apply_extraction(html, extraction_rules, known_pages)

        results.append({
            "title": sample["title"],
            "url": sample["url"],
            "type": sample.get("type", "article"),
            "markdown": md,
            "html_length": len(html),
            "ok": True,
            "error": None,
        })

    return results
