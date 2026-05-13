"""Pipeline composition, validation, and orchestration."""

import argparse
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from ..client import ApiClient, probe_api_endpoint
from .phase_a import run_phase_a
from .phase_b import run_phase_b
from .phase_c import run_phase_c
from ..strategies import (
    AllPagesDiscoveryStrategy,
    CategoryMembersDiscoveryStrategy,
    ContentAcquisitionStrategy,
    DiscoveryStrategy,
    ExactTitleLinkResolver,
    FandomInfoboxTemplateProcessor,
    FrontmatterDrivenListPageAssembler,
    HtmlRenderedAcquisitionStrategy,
    HybridAcquisitionStrategy,
    HybridListPageAssembler,
    LinkResolver,
    ListPageAssembler,
    ShortNameLinkResolver,
    SimpleSubstitutionTemplateProcessor,
    StructuredTemplateProcessor,
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
EXIT_VALIDATION_FAILURE = 30


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
class RateLimitConfig:
    concurrency: int = 1
    batch_delay_ms: int = 1000
    max_retries: int = 5
    initial_delay_sec: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_sec: float = 60.0
    jitter: bool = True


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

_STRATEGY_REGISTRY = {
    "discovery": {
        "allpages": AllPagesDiscoveryStrategy,
        "category_members": CategoryMembersDiscoveryStrategy,
    },
    "content_acquisition": {
        "wikitext_only": WikitextOnlyAcquisitionStrategy,
        "hybrid_wikitext_plus_rendered": HybridAcquisitionStrategy,
        "html_rendered": HtmlRenderedAcquisitionStrategy,
    },
    "link_resolver": {
        "exact_title_match": ExactTitleLinkResolver,
        "short_name_with_cross_namespace": ShortNameLinkResolver,
    },
    "template_processor": {
        "simple_substitution": SimpleSubstitutionTemplateProcessor,
        "structured_with_lua_fallback": StructuredTemplateProcessor,
        "fandom_infobox": FandomInfoboxTemplateProcessor,
    },
    "list_page_assembler": {
        "frontmatter_driven": FrontmatterDrivenListPageAssembler,
        "hybrid_frontmatter_and_rendered": HybridListPageAssembler,
    },
}

# Public API for external consumers (bootstrap-strategy, validation)
STRATEGY_REGISTRY = _STRATEGY_REGISTRY
PROFILE_KEY_MAP = _PROFILE_KEY_MAP


def derive_capabilities(content_profile: dict) -> list[str]:
    """Derive pipeline capabilities from content_profile strategy IDs.

    Reads required_capabilities from discovery and content_acquisition
    strategy instances, returns sorted union.
    """
    caps: set[str] = set()
    for field in ("discovery", "content_acquisition"):
        # Find the content_profile key for this dimension
        profile_key = None
        for pk, fk in _PROFILE_KEY_MAP.items():
            if fk == field:
                profile_key = pk
                break

        # Resolve strategy ID: explicit > default
        default_id = DEFAULT_STRATEGIES[field][0]
        strategy_id = content_profile.get(profile_key, default_id) if profile_key else default_id

        registry = _STRATEGY_REGISTRY.get(field, {})
        cls = registry.get(strategy_id)
        if cls is None:
            raise ValueError(
                f"Strategy ID '{strategy_id}' not registered in '{field}'. "
                f"Available: {list(registry.keys())}"
            )
        caps |= cls().required_capabilities

    return sorted(caps)


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

        registry = _STRATEGY_REGISTRY.get(field, {})
        cls = registry.get(requested_id)
        if cls is None:
            raise ValueError(
                f"Strategy ID '{requested_id}' not registered in '{field}'. "
                f"Available: {list(registry.keys())}"
            )

        if field == "link_resolver":
            kwargs[field] = cls(domain)
        else:
            kwargs[field] = cls()

    return PipelineStrategies(**kwargs)


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
# Rate limit configuration resolution
# ===========================================================================

def _load_anti_crawl_strategy(anti_crawl_id: str) -> Optional[dict]:
    """Load an anti-crawl strategy file and return its frontmatter."""
    base_path = os.path.join(os.path.dirname(__file__), "..", "..", "sites", "anti-crawl")
    file_path = os.path.join(base_path, f"{anti_crawl_id}.md")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    import yaml
    return yaml.safe_load(parts[1])


def resolve_rate_limit_config(strategy: dict, cli_args: argparse.Namespace) -> RateLimitConfig:
    """Resolve final rate limit configuration using four-layer priority.
    
    Priority (highest to lowest):
    1. CLI arguments
    2. Site Strategy local overrides (api.rate_limit)
    3. Anti-Crawl tier template
    4. Code safe defaults
    """
    config = RateLimitConfig()  # Layer 4: safe defaults

    # Layer 3: Anti-Crawl tier template
    api_config = strategy.get("api", {})
    rate_limit_cfg = api_config.get("rate_limit", {})
    tier_name = rate_limit_cfg.get("tier")
    
    if tier_name:
        anti_crawl_refs = strategy.get("anti_crawl_refs", [])
        for ref in anti_crawl_refs:
            ac_strategy = _load_anti_crawl_strategy(ref)
            if ac_strategy and "rate_limit_tiers" in ac_strategy:
                tiers = ac_strategy["rate_limit_tiers"]
                if tier_name in tiers:
                    tier = tiers[tier_name]
                    config.concurrency = tier.get("concurrency", config.concurrency)
                    config.batch_delay_ms = tier.get("batch_delay_ms", config.batch_delay_ms)
                    retry = tier.get("retry", {})
                    config.max_retries = retry.get("max_retries", config.max_retries)
                    config.initial_delay_sec = retry.get("initial_delay_sec", config.initial_delay_sec)
                    config.backoff_multiplier = retry.get("backoff_multiplier", config.backoff_multiplier)
                    config.max_delay_sec = retry.get("max_delay_sec", config.max_delay_sec)
                    config.jitter = retry.get("jitter", config.jitter)
                    break
        else:
            log.warning("Tier '%s' not found in any referenced anti-crawl strategy, using defaults", tier_name)

    # Layer 2: Site Strategy local overrides
    if "concurrency" in rate_limit_cfg and rate_limit_cfg["concurrency"] is not None:
        config.concurrency = rate_limit_cfg["concurrency"]
    if "batch_delay_ms" in rate_limit_cfg and rate_limit_cfg["batch_delay_ms"] is not None:
        config.batch_delay_ms = rate_limit_cfg["batch_delay_ms"]
    retry_override = rate_limit_cfg.get("retry", {})
    if "max_retries" in retry_override and retry_override["max_retries"] is not None:
        config.max_retries = retry_override["max_retries"]
    if "initial_delay_sec" in retry_override and retry_override["initial_delay_sec"] is not None:
        config.initial_delay_sec = retry_override["initial_delay_sec"]
    if "backoff_multiplier" in retry_override and retry_override["backoff_multiplier"] is not None:
        config.backoff_multiplier = retry_override["backoff_multiplier"]
    if "max_delay_sec" in retry_override and retry_override["max_delay_sec"] is not None:
        config.max_delay_sec = retry_override["max_delay_sec"]
    if "jitter" in retry_override and retry_override["jitter"] is not None:
        config.jitter = retry_override["jitter"]

    # Layer 1: CLI arguments (highest priority)
    if cli_args.concurrency is not None:
        config.concurrency = cli_args.concurrency
    if getattr(cli_args, "batch_delay_ms", None) is not None:
        config.batch_delay_ms = cli_args.batch_delay_ms
    if getattr(cli_args, "max_retries", None) is not None:
        config.max_retries = cli_args.max_retries
    if getattr(cli_args, "backoff_multiplier", None) is not None:
        config.backoff_multiplier = cli_args.backoff_multiplier
    if getattr(cli_args, "jitter", None) is not None:
        config.jitter = cli_args.jitter

    log.info("Resolved rate limit config: concurrency=%d, batch_delay_ms=%d, max_retries=%d, "
             "backoff_multiplier=%.1f, jitter=%s",
             config.concurrency, config.batch_delay_ms, config.max_retries,
             config.backoff_multiplier, config.jitter)
    return config


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

    # Determine phases to run
    phases = args.phase if args.phase else ["A", "B", "C"]

    # --- Phase A ---
    if "A" in phases or "all" in phases:
        try:
            manifest = run_phase_a(client, strategy, origin, strategies.discovery,
                                       platform_variant=platform_variant)
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
                client, manifest, strategy, rate_limit_config, domain,
                strategies.content_acquisition, strategies.link_resolver, strategies.template_processor,
                platform_variant=platform_variant
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
        with open(results_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # Reconstruct results map from saved data
        results = {}
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

    # --- Phase C ---
    if "C" in phases or "all" in phases:
        try:
            phase_c_stats = run_phase_c(
                args.output, manifest, results, strategy, domain,
                strategies.list_page_assembler, strategies.link_resolver,
                client=client
            )
            log.info("Phase C stats: %s", json.dumps(phase_c_stats, indent=2))
        except Exception as e:
            log.error("Phase C failed: %s", e)
            return EXIT_PHASE_C_FAILURE

    # --- L6 Validation ---
    if args.validate or ("C" in phases or "all" in phases):
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
