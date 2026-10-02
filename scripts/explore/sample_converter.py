"""SampleConverter — fetch sample pages and convert to Markdown using scaffold extraction rules."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.parse

# Ensure project root is importable when run as a script
if __name__ == "__main__":
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)


from scripts.lib.content_admission import admit_html_file


def _fetch_sample(
    repo_root: str,
    url: str,
    engine: str,
    output_path: str,
) -> dict:
    """Fetch a single sample page using the determined engine."""
    from scripts.explore.probe_chain import _run_scrapling_get, _run_obscura_fetch, _run_cloakbrowser_fetch
    runners = {"scrapling-get": _run_scrapling_get, "get": _run_scrapling_get,
               "obscura-fetch": _run_obscura_fetch, "obscura": _run_obscura_fetch,
               "cloakbrowser-fetch": _run_cloakbrowser_fetch, "cloakbrowser": _run_cloakbrowser_fetch}
    runner = runners.get(engine)
    if runner is None:
        return {"ok": False, "error": f"Unsupported HTML engine: {engine}"}
    result = runner(repo_root, url, output_path)
    return {"ok": result["status"] == "success", "path": output_path,
            "error": result.get("error_type"), "admission": result.get("admission")}


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


def _apply_extraction(
    html: str,
    extraction_rules: dict,
    known_pages: set[str],
) -> str:
    """Apply extraction rules from config to HTML.

    Thin delegate to converter.convert_page_full() — the shared kernel owns
    the full pipeline (infobox → preprocess → convert → prepend → post-op
    transforms). This mirror contains no transform logic (invariant I2).

    Spec: convert-kernel-three-layer-interface / apply-extraction-uses-shared-lib
    """
    import importlib
    _mod = importlib.import_module('scripts.lib.extraction.converter')
    _convert_page_full = _mod.convert_page_full

    # Delegate the full extraction pipeline (infobox → preprocess → convert →
    # prepend → post-conversion ops) to the shared kernel. Post-op transforms
    # live in the kernel's apply_post_conversion_ops (invariant I2: a mirror
    # orchestrates, contains no transform logic).
    # Spec: convert-kernel-three-layer-interface / apply-extraction-uses-shared-lib.
    return _convert_page_full(html, extraction_rules)


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
        if fetch_result["ok"]:
            admission = admit_html_file(output_path)
            if not admission['admitted']:
                fetch_result = {'ok': False, 'error': admission['reason'], 'admission': admission}
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


def main():
    """CLI entry point for standalone strategy-driven sample conversion.

    Subcommands:
        apply: Convert an existing HTML file using strategy extraction rules.
        fetch-and-apply: Fetch a page via MediaWiki API then convert.
    """
    import argparse
    import sys
    from scripts.lib.strategy_loader import parse_strategy

    parser = argparse.ArgumentParser(
        description="Strategy-driven sample conversion for chrome-agent explore",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # apply: convert existing HTML
    apply_parser = subparsers.add_parser("apply", help="Apply extraction rules to an existing HTML file")
    apply_parser.add_argument("--strategy", required=True, help="Path to strategy.md file")
    apply_parser.add_argument("--html", required=True, help="Path to input HTML file")
    apply_parser.add_argument("--title", required=True, help="Page title for link resolution")
    apply_parser.add_argument("--output", required=True, help="Path to output Markdown file")

    # fetch-and-apply: fetch via MediaWiki API + convert
    fetch_parser = subparsers.add_parser(
        "fetch-and-apply",
        help="Fetch page via MediaWiki API then apply extraction rules",
    )
    fetch_parser.add_argument("--strategy", required=True, help="Path to strategy.md file")
    fetch_parser.add_argument("--page", required=True, help="Page title to fetch")
    fetch_parser.add_argument("--output", required=True, help="Path to output Markdown file")

    args = parser.parse_args()

    # Load extraction rules from strategy using shared strategy_loader
    full_strategy = parse_strategy(args.strategy)
    extraction_rules = full_strategy.get("extraction", {})

    if args.command == "apply":
        # Read HTML from file
        with open(args.html, "r", encoding="utf-8") as f:
            html = f.read()

        # Apply extraction
        known_pages = {args.title}
        md = _apply_extraction(html, extraction_rules, known_pages)

        # Write output
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)

        result = {
            "ok": True,
            "output": os.path.abspath(args.output),
            "length": len(md),
        }
        print(json.dumps(result))

    elif args.command == "fetch-and-apply":
        # Determine base URL: image_handling.base_url first, fallback to api.base_url
        base_url = (
            extraction_rules.get("image_handling", {}).get("base_url", "")
            or full_strategy.get("api", {}).get("base_url", "")
        )
        if not base_url:
            print(json.dumps({"ok": False, "error": "No base_url found in strategy (check image_handling.base_url or api.base_url)"}))
            sys.exit(1)

        # Fetch via MediaWiki API
        tmp_html = args.output + ".tmp.html"
        fetch_result = _fetch_via_mediawiki_api(base_url, args.page, tmp_html)
        if not fetch_result["ok"]:
            if os.path.exists(tmp_html):
                os.unlink(tmp_html)
            print(json.dumps({"ok": False, "error": fetch_result.get("error", "Fetch failed")}))
            sys.exit(1)

        admission = admit_html_file(tmp_html)
        if not admission['admitted']:
            print(json.dumps({'ok': False, 'error': admission['reason'], 'admission': admission}))
            sys.exit(1)

        # Read fetched HTML
        with open(tmp_html, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(tmp_html)

        # Apply extraction
        known_pages = {args.page}
        md = _apply_extraction(html, extraction_rules, known_pages)

        # Write output
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)

        result = {
            "ok": True,
            "output": os.path.abspath(args.output),
            "length": len(md),
        }
        print(json.dumps(result))


if __name__ == "__main__":
    main()
