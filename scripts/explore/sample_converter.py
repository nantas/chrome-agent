"""SampleConverter — fetch sample pages and convert to Markdown using scaffold extraction rules."""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString
import markdownify


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

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

    elif engine in ("mediawiki-api",):
        # url is expected to be the API base_url; title passed via output_path hack
        # Not used in default flow — available for strategy-driven API fetch
        return {"ok": False, "error": "mediawiki-api engine requires explicit API call"}

    return {"ok": False, "error": f"Unknown engine: {engine}"}


def _fetch_via_mediawiki_api(
    base_url: str,
    page_title: str,
    output_path: str,
) -> dict:
    """Fetch page HTML via MediaWiki action=parse API with redirect following."""
    import urllib.request
    import urllib.parse

    api_url = f"{base_url}/api.php"
    encoded = urllib.parse.quote(page_title, safe="")
    url = (
        f"{api_url}?action=parse&page={encoded}"
        f"&prop=text|wikitext|sections|displaytitle"
        f"&redirects=true&format=json"
    )
    headers = {"User-Agent": "ChromeAgent/1.0 (sample-converter)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        if "error" in data:
            return {"ok": False, "error": data["error"].get("info", str(data["error"]))}
        html = data["parse"]["text"]["*"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "path": output_path, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Infobox / image helpers
# ---------------------------------------------------------------------------

def _img_to_md(img_tag, skip_patterns: list[str] | None = None) -> str:
    """Convert an <img> tag to Markdown, respecting skip patterns."""
    skip_patterns = skip_patterns or []
    src = img_tag.get("src", "")
    alt = img_tag.get("alt", "")
    if not src:
        return ""
    if any(re.search(p, src) for p in skip_patterns):
        return ""
    return f"![{alt}]({src})"


def _extract_portable_infobox(
    soup: BeautifulSoup,
    base_url: str,
    skip_patterns: list[str] | None = None,
) -> str:
    """Extract <aside class='portable-infobox'> into structured Markdown table.

    Handles wiki.gg portable-infobox (aside element) rather than traditional
    MediaWiki infobox tables.
    """
    aside = soup.find("aside", class_="portable-infobox")
    if not aside:
        return ""

    lines = ["## Infobox", "", "| Field | Value |", "| --- | --- |"]
    for div in aside.find_all("div", class_="pi-data"):
        label_el = div.find("h3", class_="pi-data-label")
        value_el = div.find("div", class_="pi-data-value")
        if not label_el:
            continue
        key = label_el.get_text(strip=True)
        if not value_el:
            lines.append(f"| {key} | |")
            continue

        val_parts: list[str] = []
        for child in value_el.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    val_parts.append(text)
            elif child.name == "img":
                md = _img_to_md(child, skip_patterns)
                if md:
                    val_parts.append(md)
            elif child.name == "a":
                imgs = child.find_all("img")
                if imgs and not child.get_text(strip=True):
                    # Image-only link: <a class="image"><img></a>
                    for img in imgs:
                        md = _img_to_md(img, skip_patterns)
                        if md:
                            val_parts.append(md)
                else:
                    text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if text:
                        val_parts.append(f"[{text}]({href})")
            elif child.name == "code":
                val_parts.append(f"`{child.get_text(strip=True)}`")
            elif child.name in ("div", "span"):
                imgs = child.find_all("img")
                if imgs:
                    for img in imgs:
                        md = _img_to_md(img, skip_patterns)
                        if md:
                            val_parts.append(md)
                else:
                    text = child.get_text(strip=True)
                    if text:
                        val_parts.append(text)
            else:
                text = child.get_text(strip=True)
                if text:
                    val_parts.append(text)

        val = " ".join(val_parts).strip()
        if key and val:
            lines.append(f"| {key} | {val} |")

    if len(lines) <= 4:
        return ""
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def _apply_extraction(
    html: str,
    extraction_rules: dict,
    known_pages: set[str],
) -> str:
    """Apply extraction rules from scaffold to HTML."""
    soup = BeautifulSoup(html, "html.parser")
    cleanup = extraction_rules.get("cleanup", [])
    skip_patterns = extraction_rules.get(
        "image_skip_patterns",
        [p[0] if isinstance(p, list) else p
         for p in extraction_rules.get("image_filtering", {}).get("skip_patterns", [])],
    )
    # Also support strategy-style image_filtering.skip_patterns
    if not skip_patterns:
        raw = extraction_rules.get("image_filtering", {}).get("skip_patterns", [])
        if raw:
            skip_patterns = raw

    # --- Phase 1: Extract structured content before cleanup ---

    # Extract portable-infobox (wiki.gg <aside>) into Markdown table
    base_url = extraction_rules.get("image_handling", {}).get(
        "base_url", extraction_rules.get("base_url", "")
    )
    infobox_md = _extract_portable_infobox(soup, base_url, skip_patterns)
    for aside in soup.find_all("aside", class_="portable-infobox"):
        aside.decompose()

    # --- Phase 2: Standard cleanup ---

    if "fix_lazyload_images" in cleanup:
        for img in soup.find_all("img"):
            src = img.get("src", "")
            data_src = img.get("data-src", "")
            if "data:image" in src and data_src:
                img["src"] = data_src

    if "strip_edit_sections" in cleanup:
        for el in soup.find_all(class_="mw-editsection"):
            el.decompose()

    if "strip_toc" in cleanup:
        for el in soup.find_all(id="toc"):
            el.decompose()
        for el in soup.find_all(class_="toc"):
            el.decompose()

    # Strip hatnotes
    for el in soup.find_all(class_="hatnote"):
        el.decompose()

    # Strip wiki.gg nav-box / nav-main (div-based, not table-based navbox)
    for nav_cls in ["nav-box", "nav-main", "nav-header", "nav-footer"]:
        for el in soup.find_all("div", class_=lambda x: x and nav_cls in str(x)):
            el.decompose()

    # Strip traditional navbox tables
    for nav_cls in ["navbox", "nowraplinks"]:
        for el in soup.find_all("table", class_=lambda x: x and nav_cls in str(x)):
            el.decompose()

    if "strip_fandom_infobox_tables" in cleanup:
        for cls in ["item-table-header", "item-table-body", "item-table-description",
                    "item-table-appearance", "infobox-table"]:
            for el in soup.find_all("table", class_=lambda x: x and cls in x):
                el.decompose()

    if "convert_ambox_to_text" in cleanup:
        for el in soup.find_all("table", class_=lambda x: x and "ambox" in x):
            text = el.get_text(strip=True)
            new_p = soup.new_tag("p")
            new_p.string = f"⚠️ {text}" if text else ""
            el.replace_with(new_p)

    # Unwrap image wrapper links: <a><img></a> and <a class="image"><img></a>
    if "unwrap_image_wrappers" in cleanup:
        for a in soup.find_all("a"):
            children = list(a.children)
            non_empty = [c for c in children
                         if not (isinstance(c, str) and c.strip() == "")]
            if len(non_empty) == 1 and getattr(non_empty[0], "name", None) == "img":
                a.unwrap()
            elif a.get("class") and "image" in a.get("class", []):
                imgs = a.find_all("img")
                if imgs and not a.get_text(strip=True):
                    a.unwrap()

    # Remove decorative/skip-pattern images
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if any(re.search(p, src) for p in skip_patterns):
            img.decompose()

    # --- Phase 3: Content selection and Markdown conversion ---

    selector = extraction_rules.get("selectors", {}).get("content", "#mw-content-text")
    content = soup.select_one(selector) or soup.select_one("body") or soup

    md = markdownify.markdownify(
        str(content),
        heading_style="atx",
        keep_inline_images_in=["td", "th", "span", "a", "div", "p", "li"],
    )

    # Prepend infobox if extracted
    if infobox_md:
        md = infobox_md + "\n\n" + md

    # --- Phase 4: Post-conversion normalization ---

    normalization = extraction_rules.get("text_normalization", [])
    if "fix_spaces" in normalization:
        md = re.sub(r"([a-zA-Z])(\d+(?:\.\d+)*)([a-zA-Z])", r"\1 \2 \3", md)
        md = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", md)
        md = re.sub(r"(\!\[[^\]]*\]\([^)]+\))(\!\[)", r"\1 \2", md)

    if "normalize_blank_lines" in normalization:
        md = re.sub(r"\n{3,}", "\n\n", md)

    if "deduplicate_words" in normalization:
        md = re.sub(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+\1\b", r"\1", md,
        )

    # Remove empty headers
    md = re.sub(r"#{1,6}\s*\n", "\n", md)

    # Convert relative URLs to absolute (if base_url provided)
    if base_url:
        md = re.sub(
            r"!\[([^\]]*)\]\((/images/[^)]+)\)",
            rf"![\1]({base_url}\2)", md,
        )
        md = re.sub(
            r"\[([^\]]*)\]\((/wiki/[^)]+)\)",
            rf"[\1]({base_url}\2)", md,
        )

    # Clean YouTube embed residue
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
        output_path = os.path.join(
            run_dir,
            f"sample_{sample['title'].replace(' ', '_').replace('/', '_')}.html",
        )

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
