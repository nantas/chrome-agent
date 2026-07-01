"""SampleConverter — fetch sample pages and convert to Markdown using scaffold extraction rules."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import re
import urllib.request
import urllib.parse

# Ensure project root is importable when run as a script
if __name__ == "__main__":
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)


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


def _apply_extraction(
    html: str,
    extraction_rules: dict,
    known_pages: set[str],
) -> str:
    """Apply extraction rules from config to HTML.

    Delegates the core 4-step extraction pipeline to
    converter.convert_page_full(), then applies explore-specific
    post-processing (normalization, URL conversion, cleanup ops).

    Spec: sample-converter / apply-extraction-uses-shared-lib
    """
    import importlib
    _mod = importlib.import_module('scripts.lib.extraction.converter')
    _convert_page_full = _mod.convert_page_full

    base_url = extraction_rules.get("image_handling", {}).get("base_url", "")

    # Delegate core 4-step extraction (infobox → preprocess → convert → prepend)
    # to the shared converter kernel.
    md = _convert_page_full(html, extraction_rules)

    # Post-conversion normalization (config-driven)
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

    # Post-conversion cleanup ops (gated by cleanup list, not text_normalization)
    cleanup = extraction_rules.get("cleanup", [])
    if "strip_empty_parens" in cleanup:
        md = re.sub(r"\(\s*\)", "", md)

    if "fix_separators" in cleanup:
        md = re.sub(r"(\!\[[^\]]*\]\([^)]+\))\s*(?=\[)", r"\1 ", md)
        md = re.sub(r"(\[[^\]]+\]\([^)]+\))\s*(?=\[)", r"\1 ", md)
        md = re.sub(r"  +", " ", md)

    if "normalize_internal" in cleanup:
        if base_url:
            md = re.sub(
                r"\[([^\]]*)\]\(/wiki/([^)]+)\)",
                rf"[\1]({base_url}/wiki/\2)", md,
            )

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
