"""Pipeline orchestration — main entry point and exit codes."""

import argparse
import json
import logging
import os
from typing import Optional
from urllib.parse import urlparse

from ..converters.link_fixer import fix_links_in_dir

from ...lib.strategy_loader import parse_strategy
from ...lib.config_resolver import (
    resolve_rate_limit_config,
    resolve_exclude_categories,
)

from ..client import ApiClient, probe_api_endpoint
from .phases.assemble import run_assemble

from .registry import (
    PipelineStrategies,
    build_pipeline,
)
from .phases.fetch import run_fetch
from .phases.convert import run_convert

log = logging.getLogger("pipeline")


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_SUCCESS = 0
EXIT_PARTIAL_SUCCESS = 1
EXIT_API_UNREACHABLE = 10
EXIT_PHASE_A_FAILURE = 11
EXIT_PHASE_B_FAILURE = 12
EXIT_PHASE_C_FAILURE = 13
EXIT_STRATEGY_ERROR = 14
EXIT_INVALID_ARGS = 20
EXIT_VALIDATION_FAILURE = 30


# ===========================================================================
# Validation
# ===========================================================================

def validate_api_config(api_config: Optional[dict], strategies: PipelineStrategies) -> Optional[str]:
    """Validate the api field from strategy frontmatter. Returns error message or None."""
    if api_config is None:
        return "Strategy has no 'api' field"
    if "platform" not in api_config:
        return "Strategy 'api.platform' is missing"
    if api_config["platform"] != "mediawiki":
        return f"Unsupported api.platform: {api_config['platform']}"

    caps = set(api_config.get("capabilities", []))
    required = (
        strategies.discovery.required_capabilities
        | strategies.content_acquisition.required_capabilities
    )
    if not required.issubset(caps):
        missing = required - caps
        return f"Missing required capabilities: {missing}"
    return None


# ===========================================================================
# Main pipeline
# ===========================================================================

def run_pipeline(args: argparse.Namespace) -> int:
    """Run the full extraction pipeline. Returns exit code."""
    # Parse strategy
    try:
        strategy = parse_strategy(args.strategy)
    except Exception as e:
        log.error("Failed to parse strategy: %s", e)
        return EXIT_STRATEGY_ERROR

    # Build pipeline strategies (with schema validation)
    domain = strategy.get("domain", urlparse(args.url).hostname)
    origin = f"https://{domain}"

    try:
        strategies = build_pipeline(strategy, domain)
    except ValueError as e:
        log.error("Strategy schema validation failed: %s", e)
        return EXIT_STRATEGY_ERROR

    # Validate API config
    api_config = strategy.get("api")
    error = validate_api_config(api_config, strategies)
    if error:
        log.error("Strategy API validation failed: %s", error)
        return EXIT_STRATEGY_ERROR

    # Probe API endpoint
    if args.no_api_probe and api_config.get("base_url"):
        base_url = api_config["base_url"]
        log.info("Skipping probe, using strategy base_url: %s", base_url)
    else:
        log.info("Probing API endpoint for %s...", domain)
        base_url = probe_api_endpoint(origin, api_config.get("base_url"))
        if not base_url:
            log.error("API endpoint unreachable for %s — cannot proceed, fallback required", domain)
            return EXIT_API_UNREACHABLE

    # Resolve rate limit configuration
    rate_limit_config = resolve_rate_limit_config(strategy, args)

    # Resolve platform variant
    platform_variant = strategy.get("api", {}).get("platform_variant", "standard")
    log.info("Platform variant: %s", platform_variant)

    client = ApiClient(base_url, rate_limit_config=rate_limit_config)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Resolve exclude_categories via priority chain
    cli_excludes = getattr(args, "exclude_category", None) or []
    merged_excludes = resolve_exclude_categories(strategy, cli_excludes)

    # Determine phases to run
    phases = args.phase if args.phase else ["all"]

    # --- from-manifest: skip discovery, load existing manifest ---
    from_manifest = getattr(args, "from_manifest", None)
    if from_manifest:
        if not os.path.exists(from_manifest):
            log.error("--from-manifest file not found: %s", from_manifest)
            return EXIT_INVALID_ARGS
        with open(from_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_path = from_manifest
        log.info("Loaded manifest from --from-manifest: %s (%d pages)",
                 from_manifest, len(manifest.get("pages", [])))

    elif not from_manifest:
        manifest_path = os.path.join(args.output, "page_manifest.json")
        if not os.path.exists(manifest_path):
            log.error("No manifest specified. Use --from-manifest <path> or ensure page_manifest.json exists in output directory.")
            return EXIT_INVALID_ARGS
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        log.info("Loaded existing manifest: %d pages", len(manifest["pages"]))


    # --- --max-pages: limit manifest before extraction ---
    max_pages = getattr(args, "max_pages", None)
    if max_pages and max_pages > 0:
        all_pages = manifest.get("pages", [])
        if len(all_pages) > max_pages:
            manifest["pages"] = all_pages[:max_pages]
            log.info("--max-pages %d: trimmed manifest from %d to %d pages",
                     max_pages, len(all_pages), max_pages)

    # --- Filter excluded categories from manifest before extraction ---
    if merged_excludes:
        exclude_set = set(merged_excludes)
        all_pages = manifest.get("pages", [])
        before = len(all_pages)
        manifest["pages"] = [
            p for p in all_pages
            if not (set(p.get("source_categories", [])) & exclude_set
                    or p.get("assigned_category", "") in exclude_set
                    or p.get("title", "") in exclude_set)
        ]
        filtered = before - len(manifest["pages"])
        if filtered > 0:
            log.info("Excluded %d pages from %d categories: %s",
                     filtered, len(exclude_set), ", ".join(sorted(exclude_set)))


    # --- Resume state initialization ---
    completed_pages_set = None
    resume_enabled = getattr(args, "resume", True) and not getattr(args, "no_resume", False)
    resume_flush_interval = getattr(args, "resume_flush_interval", 100)

    if resume_enabled and ("fetch" in phases or "convert" in phases or "all" in phases):
        from .state import load_state, initialize_state, save_state

        existing_state = load_state(args.output)
        if existing_state.get("completed_pages"):
            log.info("Resume mode: found %d previously completed pages",
                     len(existing_state["completed_pages"]))
            completed_pages_set = set(existing_state["completed_pages"])
        else:
            # Initialize fresh state
            completed_pages_set = set()
            initialize_state(args.output, manifest, phase="B")
            log.info("Resume mode: initialized fresh pipeline state")
    else:
        log.info("Resume disabled or not applicable — starting fresh")

    # --- Determine repo_root for cache ---
    repo_root = getattr(args, "repo_root", None)
    if not repo_root:
        strategy_dir = os.path.dirname(os.path.abspath(args.strategy))
        candidate = strategy_dir
        for _ in range(10):
            if os.path.isdir(os.path.join(candidate, ".git")) or os.path.isdir(os.path.join(candidate, "scripts")):
                repo_root = candidate
                break
            candidate = os.path.dirname(candidate)
        if not repo_root:
            repo_root = os.getcwd()
            log.warning("Could not determine repo_root, using cwd: %s", repo_root)

    re_fetch = getattr(args, "re_fetch", False)

    # --- Fetch Phase ---
    fetch_stats = None
    if "fetch" in phases or "all" in phases:
        try:
            fetch_stats = run_fetch(
                client, manifest, strategy, rate_limit_config, domain,
                strategies.content_acquisition, repo_root,
                re_fetch=re_fetch,
            )
        except Exception as e:
            log.error("Fetch phase failed: %s", e)
            return EXIT_PHASE_B_FAILURE

        # Early exit for fetch-only
        if "fetch" in phases and "all" not in phases:
            log.info("--phase fetch complete — cache populated")
            return EXIT_SUCCESS

    # --- Convert Phase ---
    if "convert" in phases and "all" not in phases and not from_manifest:
        log.error("--phase convert requires --from-manifest")
        return EXIT_INVALID_ARGS

    results = None
    stats = None
    if "convert" in phases or "all" in phases:
        try:
            results, stats = run_convert(
                args.output, manifest, strategy, domain, repo_root,
                resume_enabled=resume_enabled
            )

            # Save extraction results WITH content and rendered_html
            results_path = os.path.join(args.output, "extraction_results.json")
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump({
                    "stats": {k: v for k, v in stats.items() if k != "warnings"},
                    "pages": {
                        title: {
                            "status": r.get("status"),
                            "error": r.get("error"),
                            "content": r.get("content"),
                            "rendered_html": r.get("rendered_html"),
                            "images": r.get("images"),
                        }
                        for title, r in results.items()
                    },
                }, f, indent=2, ensure_ascii=False)

            if stats.get("failed", 0) > 0 and stats["failed"] / max(stats["total"], 1) > 0.5:
                log.error("Convert phase failure rate exceeds 50%% threshold")
                return EXIT_PHASE_B_FAILURE

        except Exception as e:
            log.error("Convert phase failed: %s", e)
            return EXIT_PHASE_B_FAILURE
    elif "assemble" in phases:
        results_path = os.path.join(args.output, "extraction_results.json")
        results = {}
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Reconstruct results map from saved data
            for title, info in saved.get("pages", {}).items():
                results[title] = {
                    "title": title,
                    "status": info.get("status"),
                    "error": info.get("error"),
                    "content": info.get("content"),
                    "rendered_html": info.get("rendered_html"),
                    "images": info.get("images"),
                }
            log.info("Loaded existing results: %d pages", len(results))
        except FileNotFoundError:
            log.warning("No existing extraction_results.json found — assemble will use empty results")
        except Exception as e:
            log.warning("Failed to load extraction_results.json: %s — assemble will use empty results", e)

    # Flush state after extraction completion
    if resume_enabled and results is not None and completed_pages_set is not None:
        from .state import save_state
        all_completed = set(completed_pages_set) | {
            title for title, r in results.items()
            if r.get("status") == "ok"
        }
        final_state = {
            "completed_pages": list(all_completed),
            "phase": "convert_done",
            "total_pages": len(manifest.get("pages", [])),
        }
        save_state(args.output, final_state)
        log.info("State flushed: %d completed pages", len(all_completed))

    # --- Assembly Phase (C) ---
    if "assemble" in phases or "all" in phases:
        try:
            phase_c_stats = run_assemble(
                args.output, manifest, results, strategy, domain,
                strategies.list_page_assembler, strategies.link_resolver,
                client=client
            )
            log.info("Assembly phase stats: %s", json.dumps(phase_c_stats, indent=2))
        except Exception as e:
            log.error("Assembly phase failed: %s", e)
            return EXIT_PHASE_C_FAILURE

    # Flush final state after assembly completion
    if resume_enabled and completed_pages_set is not None:
        from .state import save_state
        final_completed = list(completed_pages_set) if results is None else list(
            completed_pages_set | {
                title for title, r in results.items()
                if r.get("status") == "ok"
            }
        )
        save_state(args.output, {
            "completed_pages": final_completed,
            "phase": "done",
            "total_pages": len(manifest.get("pages", [])),
        })

    # --- Auto Link Fix ---
    did_extraction = "fetch" in phases or "convert" in phases or "all" in phases or "assemble" in phases
    if did_extraction and not getattr(args, "no_auto_fix_links", False):
        manifest_pages = manifest.get("pages", [])
        try:
            result = fix_links_in_dir(args.output, domain, manifest_pages)
            log.info("Auto link fix: %d fixed, %d unchanged",
                     result.get("fixed", 0), result.get("unchanged", 0))
        except Exception as e:
            log.warning("Auto link fix failed (non-fatal): %s", e)

    # --- L6 Validation ---
    if args.validate or ("assemble" in phases or "all" in phases):
        try:
            from ..strategies import run_validation
            report = run_validation(args.output, client)
            total_issues = (len(report.get("broken_links", []))
                            + len(report.get("empty_content", []))
                            + len(report.get("unavailable_images", [])))
            if total_issues > 0:
                log.warning("L6 validation found %d issues — see validation_report.json", total_issues)
                if args.validate:
                    return EXIT_VALIDATION_FAILURE
        except Exception as e:
            log.error("L6 validation failed: %s", e)
            if args.validate:
                return EXIT_VALIDATION_FAILURE

    # Final summary
    if stats:
        total = len(manifest["pages"])
        success = stats["success"]
        log.info("Pipeline complete: %d/%d pages extracted successfully", success, total)

        if stats["failure"] > 0:
            return EXIT_PARTIAL_SUCCESS
    return EXIT_SUCCESS
