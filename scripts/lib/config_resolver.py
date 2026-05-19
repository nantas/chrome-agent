"""Shared configuration resolution utilities."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from typing import Optional

import yaml

log = logging.getLogger("pipeline")


@dataclass
class RateLimitConfig:
    concurrency: int = 1
    batch_delay_ms: int = 1000
    max_retries: int = 5
    initial_delay_sec: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_sec: float = 60.0
    jitter: bool = True


def load_anti_crawl_strategy(anti_crawl_id: str, repo_root: str = "") -> Optional[dict]:
    """Load an anti-crawl strategy file and return its frontmatter.

    Args:
        anti_crawl_id: Anti-crawl strategy identifier (filename without .md).
        repo_root: Repository root path. If empty, resolves relative to this file.

    Returns:
        Parsed frontmatter dict, or None if file not found or missing frontmatter.
    """
    if repo_root:
        base_path = os.path.join(repo_root, "sites", "anti-crawl")
    else:
        # Resolve relative to scripts/lib/ -> ../../sites/anti-crawl/
        base_path = os.path.join(os.path.dirname(__file__), "..", "..", "sites", "anti-crawl")
    file_path = os.path.join(base_path, f"{anti_crawl_id}.md")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
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
            ac_strategy = load_anti_crawl_strategy(ref)
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


def resolve_exclude_categories(strategy: dict, cli_excludes: list[str]) -> list[str]:
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
