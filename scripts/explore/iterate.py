"""iterate.py — update extraction rules and re-run sample conversion based on user feedback."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Shared schema imports must work when the CLI launches this script outside the repo.
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import yaml

from sample_converter import convert
from self_check import run_checks, summarize, plan_remediation, build_source_context
from scripts.lib.extraction.schema import validate_extraction


def iterate(
    repo_root: str,
    scaffold_path: str,
    feedback: str,
    samples: list[dict],
    engine: str,
    run_dir: str,
) -> dict:
    """Iterate on strategy extraction rules based on user feedback.

    Args:
        feedback: User feedback text describing issues
        samples: List of {url, title, type}
        engine: Preferred engine
        run_dir: Output directory

    Returns:
        {ok, updated_extraction, sample_results, self_check, iteration}
    """
    if not os.path.exists(scaffold_path):
        return {"ok": False, "error": f"Scaffold not found: {scaffold_path}"}

    with open(scaffold_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse frontmatter
    match = re.search(r"^---\n(.*?)\n---", content, re.S)
    if not match:
        return {"ok": False, "error": "Missing YAML frontmatter"}

    frontmatter = yaml.safe_load(match.group(1))
    extraction = frontmatter.get("extraction", {})
    domain = frontmatter.get("domain", "")
    api = frontmatter.get("api", {})
    mediawiki = (api.get("platform") == "mediawiki" or api.get("type") == "mediawiki"
                 or str(frontmatter.get("platform", "")).startswith("mediawiki"))
    errors = validate_extraction(extraction) if mediawiki else []
    if errors:
        return {"ok": False, "error": "invalid_configuration", "errors": errors}
    fb = feedback.lower()
    requests = []
    actions = [
        (("image", "picture", "photo"), ("image_wrapper", "base64_residue")),
        (("table", "infobox"), ("table_class_missing",)),
        (("link",), ("link_resolution",)),
        (("space",), ("space_normalization",)),
        (("toc", "contents"), ("toc",)),
        (("edit",), ("edit",)),
        (("ambox", "notice"), ("ambox",)),
    ]
    for words, kinds in actions:
        if any(word in fb for word in words):
            requests.extend({"fixable_type": kind, "detail": feedback} for kind in kinds)
    plan = plan_remediation(extraction, requests, validate=mediawiki)
    extraction = plan["extraction"]
    errors = validate_extraction(extraction) if mediawiki else []
    if errors or plan.get("errors"):
        return {"ok": False, "error": "invalid_configuration", "errors": errors or plan["errors"], "remediation": plan}
    frontmatter["extraction"] = extraction

    # Rewrite scaffold with updated rules
    new_frontmatter = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = re.sub(r"^---\n(.*?)\n---", lambda _: f"---\n{new_frontmatter}---", content, count=1, flags=re.S)

    with open(scaffold_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Re-run sample conversion
    sample_results = convert(repo_root, samples, extraction, engine, run_dir)

    # Re-run self-check
    known_pages = {s["title"] for s in samples}
    all_checks = []
    for sr in sample_results:
        if sr["ok"]:
            html_path = os.path.join(run_dir, f"sample_{sr['title'].replace(' ', '_').replace('/', '_')}.html")
            html = ""
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html = f.read()
            checks = run_checks(
                html, sr["markdown"], "", known_pages, sr.get("type", "article"),
                wiki_domain=domain,
                skip_patterns=extraction.get("image_filtering", {}).get("skip_patterns"),
                source_context=build_source_context(html, extraction,
                    input_scope=sr.get("input_scope", "unknown"), source_url=sr.get("url", "")),
            )
            all_checks.extend(checks)

    self_check = summarize(all_checks) if all_checks else None

    return {
        "ok": True,
        "updated_extraction": extraction,
        "remediation": plan,
        "sample_results": sample_results,
        "self_check": self_check,
        "scaffold_path": scaffold_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Iterate on strategy extraction rules")
    parser.add_argument("repo_root", help="Repository root path")
    parser.add_argument("scaffold_path", help="Path to strategy.md")
    parser.add_argument("--feedback", required=True, help="User feedback text")
    parser.add_argument("--samples", required=True, help="JSON array of sample objects")
    parser.add_argument("--engine", default="scrapling-get", help="Fetch engine")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    args = parser.parse_args()

    samples = json.loads(args.samples)
    result = iterate(args.repo_root, args.scaffold_path, args.feedback, samples, args.engine, args.run_dir)
    print(json.dumps(result, indent=2, default=str))
    if not result["ok"]:
        exit(1)


if __name__ == "__main__":
    main()
