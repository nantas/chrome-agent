"""StrategyScaffoldGenerator — generate strategy scaffold from template + discovery results."""

import json
import os
import re
from pathlib import Path
from typing import Optional

import yaml


def _select_template(repo_root: str, platform: str, protection: str) -> dict:
    """Select the best-matching template from sites/templates/."""
    registry_path = os.path.join(repo_root, "sites", "templates", "registry.json")
    if not os.path.exists(registry_path):
        return {"id": "custom", "file": "custom.yaml"}

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    entries = registry.get("entries", [])

    # Exact platform match
    for entry in entries:
        if entry.get("platform") == platform:
            return entry

    # Protection-level fallback
    for entry in entries:
        if entry.get("protection_level") == protection and platform.startswith(entry.get("platform", "")):
            return entry

    # Generic mediawiki fallback
    if "mediawiki" in platform:
        for entry in entries:
            if entry.get("platform") == "mediawiki":
                return entry

    return {"id": "custom", "file": "custom.yaml"}


def _load_template(repo_root: str, template_file: str) -> dict:
    template_path = os.path.join(repo_root, "sites", "templates", template_file)
    if not os.path.exists(template_path):
        return {}

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter
    match = re.search(r"^---\n(.*?)\n---", content, re.S | re.M)
    if match:
        return yaml.safe_load(match.group(1)) or {}
    return {}


def _map_anti_crawl_refs(protection_type: str) -> list[str]:
    """Map protection type to anti-crawl strategy references."""
    mapping = {
        "cloudflare-managed": ["default", "rate-limit-api"],
        "cloudflare-turnstile": ["cloudflare-turnstile", "default"],
        "rate-limit": ["default", "rate-limit-api"],
        "login-wall": ["login-wall-redirect"],
        "recaptcha": ["recaptcha", "default"],
        "none": ["default"],
    }
    return mapping.get(protection_type, ["default"])


def _map_page_type(page_type: str, nav_sections: list[str]) -> list[dict]:
    """Generate structure.pages[] from discovery results."""
    pages = []

    if page_type == "home":
        pages.append({
            "id": "home_page",
            "label": "Home Page",
            "type": "static_article",
            "content_type": "wiki_main_page",
            "pagination": "none",
            "requires_auth": False,
        })
    elif page_type == "list":
        pages.append({
            "id": "list_page",
            "label": "List Page",
            "type": "static_article",
            "content_type": "wiki_list_page",
            "pagination": "none",
            "requires_auth": False,
        })
    elif page_type == "article":
        pages.append({
            "id": "article_page",
            "label": "Article Page",
            "type": "static_article",
            "content_type": "wiki_article",
            "pagination": "none",
            "requires_auth": False,
        })

    # Add nav sections as potential entry points
    for i, section in enumerate(nav_sections[:5]):
        pages.append({
            "id": f"nav_{i}",
            "label": section,
            "type": "static_article",
            "content_type": "wiki_list_page",
            "pagination": "none",
            "requires_auth": False,
        })

    return pages


def generate(
    repo_root: str,
    domain: str,
    description: str,
    platform: str,
    protection: dict,
    structure: dict,
    api_config: Optional[dict],
) -> dict:
    """Generate a strategy scaffold.

    Returns:
        {
            "path": str,
            "content": str,
            "template_id": str,
        }
    """
    protection_type = protection.get("type", "none")
    protection_level = "high" if protection_type in ("cloudflare-managed", "cloudflare-turnstile", "recaptcha") else \
                       "medium" if protection_type == "rate-limit" else \
                       "authenticated" if protection_type == "login-wall" else "low"

    template = _select_template(repo_root, platform, protection_level)
    template_data = _load_template(repo_root, template["file"])

    # Build scaffold frontmatter
    scaffold = {
        "domain": domain,
        "description": description,
        "protection_level": protection_level,
        "anti_crawl_refs": _map_anti_crawl_refs(protection_type),
        "structure": {
            "pages": _map_page_type(structure.get("page_type", "article"), structure.get("nav_sections", [])),
            "entry_points": [p["id"] for p in _map_page_type(structure.get("page_type", "article"), structure.get("nav_sections", []))],
        },
    }

    # --- Layered API merge ---
    # Layer 1: Template declarative fields (content_profile, platform_variant, rate_limit)
    template_api = template_data.get("api") or {}
    api = {}
    for key in ("platform", "platform_variant", "content_profile", "rate_limit"):
        if key in template_api:
            api[key] = template_api[key]

    # Layer 2: Discovery factual fields (type, base_url, version)
    if api_config:
        api["type"] = api_config.get("type", "mediawiki")
        api["base_url"] = api_config.get("base_url", "")
        api["version"] = api_config.get("version", "")
        # Explicitly excluded: capabilities, site_name, lang, pages, articles

    # Layer 3: Derived capabilities from content_profile
    content_profile = api.get("content_profile", {})
    if content_profile:
        import importlib.util
        _orchestrate_path = os.path.join(
            repo_root, "scripts", "pipeline", "pipeline", "orchestrate.py"
        )
        if os.path.exists(_orchestrate_path):
            _spec = importlib.util.spec_from_file_location(
                "pipeline.pipeline.orchestrate", _orchestrate_path
            )
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            _registry = _mod.STRATEGY_REGISTRY
            # Validate content_profile IDs before generating capabilities
            for field_key, id_value in content_profile.items():
                dimension = _mod.PROFILE_KEY_MAP.get(field_key)
                if dimension and dimension in _registry:
                    if id_value not in _registry[dimension]:
                        raise ValueError(
                            f"Cannot scaffold strategy: content_profile.{field_key}='{id_value}' "
                            f"not registered in '{dimension}'. "
                            f"Available: {list(_registry[dimension].keys())}"
                        )
            # Derive capabilities from validated content_profile
            api["capabilities"] = _mod.derive_capabilities(content_profile)
        else:
            api["capabilities"] = []
    else:
        # No content_profile — use empty capabilities
        api["capabilities"] = []

    scaffold["api"] = api
    scaffold["extraction"] = template_data.get("extraction", {})

    # Update extraction engine based on protection
    if protection.get("engine_override"):
        scaffold["extraction"]["engine"] = protection["engine_override"]

    # Generate file content
    lines = ["# Auto-generated scaffold — review recommended", ""]
    lines.append("---")
    lines.append(yaml.dump(scaffold, allow_unicode=True, sort_keys=False))
    lines.append("---")
    lines.append("")
    lines.append(f"# {domain} Strategy")
    lines.append("")
    lines.append("## Platform Notes")
    lines.append("")
    lines.append(f"{description}")
    lines.append("")
    lines.append("## Extraction Rules")
    lines.append("")
    lines.append("- Review and adjust selectors and cleanup rules")
    lines.append("- Verify page type mappings match actual site structure")

    content = "\n".join(lines)

    # Write scaffold file
    domain_dir = os.path.join(repo_root, "sites", "strategies", domain)
    os.makedirs(domain_dir, exist_ok=True)
    scaffold_path = os.path.join(domain_dir, "strategy.md")

    # Guard: never overwrite a manually-edited strategy
    if os.path.exists(scaffold_path):
        with open(scaffold_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if not first_line.startswith("# Auto-generated scaffold"):
            print(f"[scaffold] SKIP: {scaffold_path} exists and is not auto-generated (first line: {first_line[:60]})")
            return {
                "path": scaffold_path,
                "content": "",
                "template_id": template["id"],
                "skipped": True,
                "reason": "Manually-edited strategy exists — delete it first to regenerate.",
            }

    with open(scaffold_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "path": scaffold_path,
        "content": content,
        "template_id": template["id"],
    }
