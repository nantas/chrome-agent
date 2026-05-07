"""Pipeline composition, validation, and orchestration."""

import argparse
import json
import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

from .client import ApiClient, probe_api_endpoint
from .phase_a import run_phase_a
from .phase_b import run_phase_b
from .phase_c import run_phase_c
from .strategies import (
    AllPagesDiscoveryStrategy,
    ContentAcquisitionStrategy,
    DiscoveryStrategy,
    ExactTitleLinkResolver,
    FrontmatterDrivenListPageAssembler,
    LinkResolver,
    ListPageAssembler,
    SimpleSubstitutionTemplateProcessor,
    TemplateProcessor,
    WikitextOnlyAcquisitionStrategy,
)

log = logging.getLogger("mediawiki-api-extract")


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


# ===========================================================================
# Strategy parsing
# ===========================================================================

def parse_strategy(strategy_path: str) -> dict:
    """Parse a site strategy file and return frontmatter as dict."""
    with open(strategy_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Strategy file missing YAML frontmatter: {strategy_path}")

    import yaml  # lazy import; only needed for strategy parsing
    frontmatter = yaml.safe_load(parts[1])
    return frontmatter


# ===========================================================================
# Pipeline strategies container
# ===========================================================================

@dataclass
class PipelineStrategies:
    discovery: DiscoveryStrategy
    content_acquisition: ContentAcquisitionStrategy
    link_resolver: LinkResolver
    template_processor: TemplateProcessor
    list_page_assembler: ListPageAssembler


# ===========================================================================
# Strategy factory
# ===========================================================================

DEFAULT_STRATEGIES = {
    "discovery": ("allpages", AllPagesDiscoveryStrategy),
    "content_acquisition": ("wikitext_only", WikitextOnlyAcquisitionStrategy),
    "link_resolver": ("exact_title_match", ExactTitleLinkResolver),
    "template_processor": ("simple_substitution", SimpleSubstitutionTemplateProcessor),
    "list_page_assembler": ("frontmatter_driven", FrontmatterDrivenListPageAssembler),
}

# Mapping from content_profile keys to PipelineStrategies field names
_PROFILE_KEY_MAP = {
    "discovery_strategy": "discovery",
    "content_acquisition": "content_acquisition",
    "link_resolver": "link_resolver",
    "template_processor": "template_processor",
    "list_page_assembler": "list_page_assembler",
}


def build_pipeline(strategy: dict, domain: str = "") -> PipelineStrategies:
    """Build PipelineStrategies from strategy configuration."""
    content_profile = strategy.get("api", {}).get("content_profile", {})

    kwargs = {}
    for field, (default_id, default_cls) in DEFAULT_STRATEGIES.items():
        # Find the content_profile key that maps to this field
        profile_key = None
        for pk, fk in _PROFILE_KEY_MAP.items():
            if fk == field:
                profile_key = pk
                break
        requested_id = content_profile.get(profile_key, default_id) if profile_key else default_id
        if requested_id != default_id and requested_id not in {default_id}:
            # Unknown strategy ID — warn and fall back to default
            log.warning("Unknown strategy ID '%s' for %s, using default '%s'",
                        requested_id, field, default_id)
            kwargs[field] = default_cls()
        else:
            if field == "link_resolver":
                kwargs[field] = default_cls(domain)
            else:
                kwargs[field] = default_cls()

    return PipelineStrategies(**kwargs)


# ===========================================================================
# Validation
# ===========================================================================

def validate_api_config(api_config: dict | None, strategies: PipelineStrategies) -> str | None:
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

    # Build pipeline strategies
    domain = strategy.get("domain", urlparse(args.url).hostname)
    origin = f"https://{domain}"

    strategies = build_pipeline(strategy, domain)

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

    client = ApiClient(base_url)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Determine phases to run
    phases = args.phase if args.phase else ["A", "B", "C"]

    # --- Phase A ---
    if "A" in phases or "all" in phases:
        try:
            manifest = run_phase_a(client, strategy, origin, strategies.discovery)
            manifest_path = os.path.join(args.output, "page_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            log.info("Manifest saved to %s", manifest_path)
        except Exception as e:
            log.error("Phase A failed: %s", e)
            return EXIT_PHASE_A_FAILURE
    else:
        manifest_path = os.path.join(args.output, "page_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        log.info("Loaded existing manifest: %d pages", len(manifest["pages"]))

    # --- Phase B ---
    results = None
    stats = None
    if "B" in phases or "all" in phases:
        try:
            results, stats = run_phase_b(
                client, manifest, strategy, args.concurrency, domain,
                strategies.content_acquisition, strategies.link_resolver, strategies.template_processor
            )

            if stats["failure_rate"] > 0.5:
                log.error("Phase B failure rate %.1f%% exceeds 50%% threshold — fallback required",
                          stats["failure_rate"] * 100)
                return EXIT_PHASE_B_FAILURE

            results_path = os.path.join(args.output, "extraction_results.json")
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump({
                    "stats": {k: v for k, v in stats.items() if k != "warnings"},
                    "warnings_count": len(stats.get("warnings", [])),
                    "pages": {title: {"status": r["status"], "error": r.get("error")}
                              for title, r in results.items()},
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error("Phase B failed: %s", e)
            return EXIT_PHASE_B_FAILURE
    elif "C" in phases:
        results_path = os.path.join(args.output, "extraction_results.json")
        raise NotImplementedError("Resuming from Phase C only is not yet supported")

    # --- Phase C ---
    if "C" in phases or "all" in phases:
        try:
            phase_c_stats = run_phase_c(
                args.output, manifest, results, strategy, domain,
                strategies.list_page_assembler, strategies.link_resolver
            )
            log.info("Phase C stats: %s", json.dumps(phase_c_stats, indent=2))
        except Exception as e:
            log.error("Phase C failed: %s", e)
            return EXIT_PHASE_C_FAILURE

    # Final summary
    if stats:
        total = len(manifest["pages"])
        success = stats["success"]
        log.info("Pipeline complete: %d/%d pages extracted successfully", success, total)

        if stats["failure"] > 0:
            return EXIT_PARTIAL_SUCCESS
    return EXIT_SUCCESS
