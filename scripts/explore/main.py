"""main.py — CLI entry for deep discovery pipeline.

Usage:
    python3 scripts/explore/main.py <repo_root> <url> [--run-dir <dir>]

Outputs JSON to stdout:
    {
        "target_url": str,
        "probe_chain": {...},
        "api_discovery": [...],
        "structure_mapping": {...},
        "protection": {...},
        "scaffold": {...},
        "samples": [...],
        "self_check": {...}
    }
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from probe_chain import probe
from api_discovery import discover
from structure_mapper import map_structure
from protection_identifier import identify
from strategy_scaffold_generator import generate
from sample_converter import convert
from self_check import run_checks, summarize, auto_remediate

# Startup dependency self-check
_missing = []
for _mod in ("bs4", "yaml"):
    try:
        __import__(_mod)
    except ImportError:
        _missing.append(_mod)
if _missing:
    _pkg_map = {"bs4": "beautifulsoup4", "yaml": "pyyaml"}
    _pkgs = ", ".join(_pkg_map.get(m, m) for m in _missing)
    print(f"FATAL: Missing dependencies: {_pkgs}", file=sys.stderr)
    print(f"Install with: pip3 install {_pkgs}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Deep discovery pipeline for chrome-agent explore")
    parser.add_argument("repo_root", help="Repository root path")
    parser.add_argument("url", help="Target URL to explore")
    parser.add_argument("--run-dir", help="Run directory for outputs", default=None)
    parser.add_argument("--samples", help="JSON array of sample URLs", default=None)
    parser.add_argument("--quick", action="store_true", help="Skip user-interactive steps")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    url = args.url
    run_dir = args.run_dir or os.path.join(repo_root, "outputs", f"explore-{url.replace('://', '-').replace('/', '-')}")
    os.makedirs(run_dir, exist_ok=True)

    # Phase 1: Probe chain
    probe_result = probe(repo_root, url, run_dir)

    # Phase 2: API discovery
    api_results = discover(url) if probe_result["success_engine"] else []

    # Phase 3: Structure mapping
    html_content = probe_result.get("html_content") or ""
    api_config = api_results[0] if api_results else None
    structure = map_structure(html_content, api_config) if html_content else {}

    # Phase 4: Protection identification
    protection = identify(probe_result["results"], html_content)

    # Phase 5: Strategy scaffold generation
    domain = __extract_domain(url)
    description = f"Auto-discovered site for {domain}"
    platform = __detect_platform(api_results, html_content)

    scaffold = generate(
        repo_root,
        domain,
        description,
        platform,
        protection,
        structure,
        api_config,
    )

    # Phase 6: Sample conversion (if samples provided)
    sample_results = []
    self_check_summary = None

    if args.samples:
        samples = json.loads(args.samples)
        engine = protection.get("engine_override") or probe_result.get("success_engine") or "scrapling-get"
        extraction_rules = scaffold.get("content", "")
        # Parse extraction rules from scaffold YAML
        import yaml
        import re as _re
        match = _re.search(r"^---\n(.*?)\n---", extraction_rules, _re.S | _re.M)
        extraction_config = yaml.safe_load(match.group(1)) if match else {}
        extraction = extraction_config.get("extraction", {})

        sample_results = convert(repo_root, samples, extraction, engine, run_dir)

        # Phase 7: Self-check with auto-remediation loop (max 2 iterations)
        known_pages = {s["title"] for s in samples}
        all_checks = []
        iteration = 0
        max_iterations = 2
        current_extraction = extraction

        while iteration <= max_iterations:
            all_checks = []
            for sr in sample_results:
                if sr["ok"]:
                    # Use per-sample HTML instead of probe HTML
                    html_path = os.path.join(
                        run_dir,
                        f"sample_{sr['title'].replace(' ', '_').replace('/', '_')}.html"
                    )
                    sample_html = ""
                    if os.path.exists(html_path):
                        with open(html_path, "r", encoding="utf-8") as f:
                            sample_html = f.read()

                    # Fetch wikitext for MediaWiki platforms when available
                    wikitext = ""
                    if api_config and api_config.get("type") == "mediawiki":
                        wikitext = _fetch_wikitext(api_config["base_url"], sr["title"])

                    checks = run_checks(
                        sample_html,
                        sr["markdown"],
                        wikitext,
                        known_pages,
                        sr.get("type", "article"),
                    )
                    all_checks.extend(checks)

            self_check_summary = summarize(all_checks)

            # Auto-remediation: fix known issues and re-convert if needed
            fixable = self_check_summary.get("fixable_failures", [])
            if fixable and iteration < max_iterations:
                current_extraction = auto_remediate(current_extraction, fixable)
                sample_results = convert(repo_root, samples, current_extraction, engine, run_dir)
                iteration += 1
            else:
                break

        if self_check_summary:
            self_check_summary["auto_remediation_iterations"] = iteration

    output = {
        "target_url": url,
        "probe_chain": {
            "results": probe_result["results"],
            "success_engine": probe_result["success_engine"],
        },
        "api_discovery": api_results,
        "structure_mapping": structure,
        "protection": protection,
        "scaffold": {
            "path": scaffold["path"],
            "template_id": scaffold["template_id"],
        },
        "samples": sample_results,
        "self_check": self_check_summary,
        "run_dir": run_dir,
    }

    print(json.dumps(output, indent=2, default=str))


def __extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc


def __detect_platform(api_results: list[dict], html: str) -> str:
    for api in api_results:
        if api.get("type") == "mediawiki":
            return "mediawiki"
    if "fandom" in html.lower():
        return "mediawiki-fandom"
    return "custom"


def _fetch_wikitext(api_base_url: str, page_title: str) -> str:
    """Fetch wikitext for a MediaWiki page via API."""
    import urllib.request
    from urllib.parse import quote

    url = (
        f"{api_base_url}?action=parse&page={quote(page_title)}"
        f"&prop=wikitext&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "chrome-agent-explore/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
