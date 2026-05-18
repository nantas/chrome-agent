"""Pipeline composition, validation, and orchestration."""

import argparse
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from ..converters.link_fixer import fix_links_in_dir

from ..client import ApiClient, probe_api_endpoint
from .phase_a import run_phase_a
from .phase_b import run_phase_b
from .phase_c import run_phase_c
from .phase_0 import run_phase_0
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


# ===========================================================================
# Exclude categories resolution
# ===========================================================================

def _resolve_exclude_categories(strategy: dict, cli_excludes: list[str]) -> list[str]:
    """Resolve exclude_categories via priority chain.

    Priority:
    1. api.exclude_categories (new top-level location)
    2. api.homepage.exclude_categories (legacy fallback)
    3. CLI --exclude-category arguments (merged union)
    """
    api_config = strategy.get("api", {})
    top_level = api_config.get("exclude_categories", None) or []
    legacy = api_config.get("homepage", {}).get("exclude_categories", None) or []

    merged = list(set(top_level) | set(legacy) | set(cli_excludes))
    if merged:
        log.info("Excluded categories: %s (api.exclude_categories=%d, api.homepage.exclude_categories=%d, cli=%d)",
                 ", ".join(sorted(merged)), len(top_level), len(legacy), len(cli_excludes))
    return merged


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
# Discovery summary builder
# ===========================================================================

import math as _math


def build_discovery_summary(manifest: dict, strategy: dict,
                            rate_limit_config: Optional[RateLimitConfig] = None,
                            output_dir: Optional[str] = None,
                            exclude_categories: Optional[list[str]] = None,
                            discovery_method: str = "homepage") -> dict:
    """Build a discovery_summary.json from manifest and strategy.

    Produces a structured summary suitable for SKILL-layer tree diagram
    generation and ask_user confirmation gates.

    Args:
        manifest: Manifest dict with ``pages`` list.
        strategy: Parsed strategy frontmatter dict.
        rate_limit_config: Resolved rate limit config (for time estimation).
        output_dir: Output directory path (for manifest_path field).
        exclude_categories: List of excluded category names.
        discovery_method: One of ``"homepage"``, ``"allpages"``, ``"first_level_links"``.

    Returns:
        Dict conforming to discovery-summary-schema spec.
    """
    pages = manifest.get("pages", [])
    total_pages = len(pages)
    domain = strategy.get("domain", "")

    # Derive exclude set
    exclude_set = set(exclude_categories or [])

    # --- Build categories ---
    if discovery_method == "homepage":
        categories = _build_homepage_categories(pages, strategy, exclude_set)
    else:  # allpages
        categories = _build_allpages_categories(pages, strategy, exclude_set)

    # --- Build excluded list ---
    excluded = _build_excluded_list(pages, strategy, exclude_set, discovery_method)

    # --- Build unclassified ---
    unclassified = _build_unclassified(pages, categories, exclude_set)

    # --- Time estimation ---
    estimated_time_minutes = _estimate_time(total_pages, rate_limit_config)

    # --- Manifest path ---
    manifest_path = None
    if output_dir:
        manifest_path = os.path.join(os.path.abspath(output_dir), "page_manifest.json")

    # --- Warnings & caveats ---
    warnings: list[str] = []
    caveats: list[str] = []
    failure_rate = 0.0

    return {
        "discovery_method": discovery_method,
        "site_title": strategy.get("description", "").split(" - ")[0] if strategy.get("description") else domain,
        "domain": domain,
        "categories": categories,
        "excluded": excluded,
        "unclassified": unclassified,
        "total_pages": total_pages,
        "estimated_time_minutes": estimated_time_minutes,
        "manifest_path": manifest_path,
        "warnings": warnings,
        "caveats": caveats,
        "failure_rate": failure_rate,
    }


def _build_homepage_categories(pages: list, strategy: dict, exclude_set: set) -> list[dict]:
    """Build categories list from homepage-driven manifest."""
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    category_page_types = homepage_cfg.get("category_page_types", {})

    # Group pages by target_directory
    dir_pages: dict[str, list[dict]] = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    # Build category info from strategy categories
    categories: list[dict] = []
    for cat_cfg in strategy_categories:
        cat_name = cat_cfg.get("name", "")
        cat_dir = cat_cfg.get("dir", "")

        if cat_name in exclude_set:
            continue

        cat_type = category_page_types.get(cat_name, "list_page")
        cat_pages = dir_pages.get(cat_dir, [])

        # Determine if there's an index page (is_list_page)
        has_index = any(p.get("is_list_page", False) for p in cat_pages)

        # Sample pages: first 3-5 non-list-page titles
        sample_pages = [
            p["title"] for p in cat_pages
            if not p.get("is_list_page", False)
        ][:5]

        # Page type from strategy structure
        page_type = "entity_page"
        for sp in strategy.get("structure", {}).get("pages", []):
            if sp.get("id") in ("entity_page", "wiki_article"):
                page_type = sp.get("content_type", "entity_page")
                break

        categories.append({
            "name": cat_name,
            "directory": cat_dir,
            "type": cat_type,
            "is_index_page": has_index,
            "page_count": len(cat_pages),
            "sample_pages": sample_pages,
            "page_type": page_type,
        })

    return categories


def _build_allpages_categories(pages: list, strategy: dict, exclude_set: set) -> list[dict]:
    """Build categories list from allpages manifest by target_directory grouping."""
    # Group pages by target_directory
    dir_pages: dict[str, list[dict]] = {}
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir not in dir_pages:
            dir_pages[tdir] = []
        dir_pages[tdir].append(page)

    # Try to map directories to category names from strategy
    homepage_cfg = strategy.get("api", {}).get("homepage", {})
    strategy_categories = homepage_cfg.get("categories", [])
    dir_to_name: dict[str, str] = {}
    for cat_cfg in strategy_categories:
        dir_to_name[cat_cfg.get("dir", "")] = cat_cfg.get("name", "")

    # Build taxonomy-based category mapping
    taxonomy = strategy.get("api", {}).get("taxonomy", {})
    page_categories = taxonomy.get("page_categories", {})

    categories: list[dict] = []
    for dir_name, cat_pages in sorted(dir_pages.items()):
        if dir_name == "misc":
            continue  # Handled by unclassified

        cat_name = dir_to_name.get(dir_name, dir_name.replace("_", " ").title())
        if cat_name in exclude_set:
            continue

        sample_pages = [p["title"] for p in cat_pages][:5]
        has_index = any(p.get("is_list_page", False) for p in cat_pages)

        categories.append({
            "name": cat_name,
            "directory": dir_name,
            "type": "category_page",
            "is_index_page": has_index,
            "page_count": len(cat_pages),
            "sample_pages": sample_pages,
            "page_type": "wiki_article",
        })

    return categories


def _build_excluded_list(pages: list, strategy: dict,
                          exclude_set: set, discovery_method: str) -> list[dict]:
    """Build list of excluded categories with page counts."""
    if not exclude_set:
        return []

    # Count pages per category
    cat_page_counts: dict[str, int] = {}
    for page in pages:
        for cat_name in page.get("source_categories", []):
            cat_page_counts[cat_name] = cat_page_counts.get(cat_name, 0) + 1

    # Also check assigned_category
    for page in pages:
        assigned = page.get("assigned_category", "")
        if assigned:
            cat_page_counts[assigned] = cat_page_counts.get(assigned, 0) + 1

    excluded: list[dict] = []
    for cat_name in sorted(exclude_set):
        count = cat_page_counts.get(cat_name, 0)
        excluded.append({
            "name": cat_name,
            "page_count": count,
            "reason": "api.exclude_categories",
        })

    return excluded


def _build_unclassified(pages: list, categories: list[dict],
                         exclude_set: set) -> dict:
    """Build unclassified pages info (pages in 'misc' directory)."""
    # Collect directories that are classified
    classified_dirs = {cat["directory"] for cat in categories}
    excluded_names = exclude_set

    misc_pages: list[dict] = []
    for page in pages:
        tdir = page.get("target_directory", "misc")
        if tdir == "misc" or tdir not in classified_dirs:
            # Check if the page belongs to an excluded category
            cats = set(page.get("source_categories", []))
            assigned = page.get("assigned_category", "")
            if assigned:
                cats.add(assigned)
            if cats & excluded_names:
                continue
            misc_pages.append(page)

    sample_pages = [p["title"] for p in misc_pages][:5]

    return {
        "count": len(misc_pages),
        "directory": "misc",
        "sample_pages": sample_pages,
    }


def _estimate_time(total_pages: int,
                    rate_limit_config: Optional[RateLimitConfig]) -> int:
    """Estimate extraction time in minutes."""
    if total_pages == 0:
        return 0

    if rate_limit_config:
        # Estimate based on rate limit config
        concurrency = max(rate_limit_config.concurrency, 1)
        batch_delay_sec = rate_limit_config.batch_delay_ms / 1000.0
        # Rough estimate: each page takes batch_delay / concurrency seconds
        avg_seconds = max(batch_delay_sec / concurrency, 0.5)
    else:
        avg_seconds = 1.0  # Conservative default

    minutes = _math.ceil(total_pages * avg_seconds / 60)
    return max(minutes, 1)  # Minimum 1 minute for non-empty manifest


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

    # ===========================================================================
    # Discovery phase resolution
    # ===========================================================================
    # Resolve discovery strategy based on --discovery CLI and strategy config
    discovery_strategy = getattr(args, "discovery", "auto")
    has_homepage = bool(strategy.get("api", {}).get("homepage"))

    # Resolve exclude_categories via priority chain
    cli_excludes = getattr(args, "exclude_category", None) or []
    merged_excludes = _resolve_exclude_categories(strategy, cli_excludes)

    _dispatch_discovery = None  # "allpages" or "homepage"
    if discovery_strategy == "homepage":
        if not has_homepage:
            log.error("Strategy has no 'api.homepage' configuration — cannot use homepage discovery")
            return EXIT_STRATEGY_ERROR
        _dispatch_discovery = "homepage"
        log.info("Explicit --discovery homepage — using homepage discovery")
    elif discovery_strategy == "allpages":
        _dispatch_discovery = "allpages"
        if has_homepage:
            log.info("Discovery strategy overridden to allpages by --discovery flag")
        else:
            log.info("Explicit --discovery allpages — using allpages discovery")
    else:  # auto
        if has_homepage:
            _dispatch_discovery = "homepage"
            # Check if discovery_strategy in content_profile contradicts
            content_ds = strategy.get("api", {}).get("content_profile", {}).get("discovery_strategy")
            if content_ds and content_ds != "allpages":
                log.warning("api.homepage defined — using homepage discovery despite discovery_strategy: %s. Use --discovery allpages to override.", content_ds)
            else:
                log.info("Strategy has api.homepage — using homepage discovery")
        else:
            _dispatch_discovery = "allpages"
            log.info("No api.homepage config — using allpages discovery")

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
        # Ensure output dir uses the manifest's parent dir if output not set
        # Discovery is fully skipped — no discovery_summary generated

    # --- Discovery phase (only when NOT using --from-manifest) ---
    if not from_manifest and ("all" in phases or "discover" in phases or "extract" in phases or "assemble" in phases):
        if _dispatch_discovery == "homepage":
            try:
                log.info("Running homepage discovery...")
                manifest = run_phase_0(client, strategy, origin,
                                       platform_variant=platform_variant,
                                       exclude_categories=merged_excludes)
                manifest_path = os.path.join(args.output, "page_manifest.json")
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                log.info("Homepage discovery manifest saved to %s (%d pages)",
                         manifest_path, len(manifest.get("pages", [])))
            except Exception as e:
                log.error("Homepage discovery failed: %s", e)
                return EXIT_PHASE_A_FAILURE
        elif _dispatch_discovery == "allpages":
            try:
                log.info("Running allpages discovery...")
                manifest = run_phase_a(client, strategy, origin, strategies.discovery,
                                       platform_variant=platform_variant,
                                       exclude_categories=merged_excludes)
                manifest_path = os.path.join(args.output, "page_manifest.json")
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                log.info("Allpages discovery manifest saved to %s (%d pages)",
                         manifest_path, len(manifest.get("pages", [])))
            except Exception as e:
                log.error("Allpages discovery failed: %s", e)
                return EXIT_PHASE_A_FAILURE
        else:
            log.error("No discovery strategy resolved")
            return EXIT_STRATEGY_ERROR
    elif not from_manifest:
        # No discovery phase needed (e.g., --phase assemble)
        manifest_path = os.path.join(args.output, "page_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        log.info("Loaded existing manifest: %d pages", len(manifest["pages"]))

    # --- Discovery summary generation ---
    if not from_manifest and ("all" in phases or "discover" in phases or "extract" in phases):
        # Generate discovery_summary.json after discovery
        discovery_method_val = "homepage" if _dispatch_discovery == "homepage" else "allpages"
        summary = build_discovery_summary(
            manifest, strategy,
            rate_limit_config=rate_limit_config,
            output_dir=args.output,
            exclude_categories=merged_excludes,
            discovery_method=discovery_method_val,
        )
        summary_path = os.path.join(args.output, "discovery_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        log.info("Discovery summary saved to %s (%d pages, %d categories)",
                 summary_path, summary["total_pages"], len(summary["categories"]))

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
                    or p.get("assigned_category", "") in exclude_set)
        ]
        filtered = before - len(manifest["pages"])
        if filtered > 0:
            log.info("Excluded %d pages from %d categories: %s",
                     filtered, len(exclude_set), ", ".join(sorted(exclude_set)))

    # --- Early exit for --phase discover ---
    if "discover" in phases and "all" not in phases:
        # Initialize resume state for discover phase
        resume_enabled = getattr(args, "resume", True) and not getattr(args, "no_resume", False)
        if resume_enabled:
            from .state import initialize_state
            initialize_state(args.output, manifest, phase="discover_done")
            log.info("Resume state initialized: phase=discover_done, total_pages=%d",
                     len(manifest.get("pages", [])))
        log.info("--phase discover complete — exiting without extraction or assembly")
        return EXIT_SUCCESS

    # --- Resume state initialization ---
    completed_pages_set = None
    resume_enabled = getattr(args, "resume", True) and not getattr(args, "no_resume", False)
    resume_flush_interval = getattr(args, "resume_flush_interval", 100)

    if resume_enabled and ("extract" in phases or "all" in phases):
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

    # --- Extraction Phase (B) ---
    results = None
    stats = None
    if "extract" in phases or "all" in phases:
        try:
            results, stats = run_phase_b(
                client, manifest, strategy, rate_limit_config, domain,
                strategies.content_acquisition, strategies.link_resolver, strategies.template_processor,
                platform_variant=platform_variant,
                completed_pages=completed_pages_set,
                output_dir=args.output,
                resume_flush_interval=resume_flush_interval,
            )

            if stats["failure_rate"] > 0.5:
                log.error("Extraction phase failure rate %.1f%% exceeds 50%% threshold — fallback required",
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
            log.error("Extraction phase failed: %s", e)
            return EXIT_PHASE_B_FAILURE
    elif "assemble" in phases:
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

    # Flush state after extraction completion
    if resume_enabled and results is not None and completed_pages_set is not None:
        from .state import save_state
        all_completed = set(completed_pages_set) | {
            title for title, r in results.items()
            if r.get("status") == "ok"
        }
        final_state = {
            "completed_pages": list(all_completed),
            "phase": "extract" if "assemble" not in phases else "extract_done",
            "total_pages": len(manifest.get("pages", [])),
        }
        save_state(args.output, final_state)
        log.info("State flushed: %d completed pages", len(all_completed))

    # --- Assembly Phase (C) ---
    if "assemble" in phases or "all" in phases:
        try:
            phase_c_stats = run_phase_c(
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
    did_extraction = "extract" in phases or "all" in phases or "assemble" in phases
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
