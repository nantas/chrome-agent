"""SampleConverter — fetch sample pages and convert to Markdown using scaffold extraction rules."""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


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

    return {"ok": False, "error": f"Unknown engine: {engine}"}


def _apply_extraction(
    html: str,
    extraction_rules: dict,
    known_pages: set[str],
) -> str:
    """Apply extraction rules from scaffold to HTML."""
    soup = BeautifulSoup(html, "html.parser")
    cleanup = extraction_rules.get("cleanup", [])

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

    if "strip_fandom_infobox_tables" in cleanup:
        for cls in ["item-table-header", "item-table-body", "item-table-description",
                    "item-table-appearance", "infobox-table", "portable-infobox"]:
            for el in soup.find_all("table", class_=lambda x: x and cls in x):
                el.decompose()

    if "convert_ambox_to_text" in cleanup:
        for el in soup.find_all("table", class_=lambda x: x and "ambox" in x):
            text = el.get_text(strip=True)
            new_p = soup.new_tag("p")
            new_p.string = f"⚠️ {text}" if text else ""
            el.replace_with(new_p)

    if "unwrap_image_wrappers" in cleanup:
        for a in soup.find_all("a"):
            children = list(a.children)
            non_empty = [c for c in children if not (isinstance(c, str) and c.strip() == "")]
            if len(non_empty) == 1 and getattr(non_empty[0], "name", None) == "img":
                a.unwrap()

    # Content selector
    selector = extraction_rules.get("selectors", {}).get("content", "#mw-content-text")
    content = soup.select_one(selector) or soup.select_one("body") or soup

    # Convert to Markdown
    import markdownify
    md = markdownify.markdownify(
        str(content),
        heading_style="atx",
        keep_inline_images_in=["td", "th", "span", "a", "div", "p", "li"],
    )

    # Text normalization
    normalization = extraction_rules.get("text_normalization", [])
    if "fix_spaces" in normalization:
        import re
        md = re.sub(r"([a-zA-Z])(\d+(?:\.\d+)*)([a-zA-Z])", r"\1 \2 \3", md)
        md = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", md)
        md = re.sub(r"(\!\[[^\]]*\]\([^)]+\))(\!\[)", r"\1 \2", md)

    if "normalize_blank_lines" in normalization:
        md = re.sub(r"\n{3,}", "\n\n", md)

    if "deduplicate_words" in normalization:
        md = re.sub(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+\1\b", r"\1", md)

    # Remove empty headers
    md = re.sub(r"#{1,6}\s*\n", "\n", md)

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
