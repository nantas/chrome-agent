"""Strategy registry, pipeline factory, and capability derivation."""

from dataclasses import dataclass

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
