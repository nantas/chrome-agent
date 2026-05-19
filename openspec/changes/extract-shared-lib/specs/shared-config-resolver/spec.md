# shared-config-resolver Specification

## Scope

提供统一的速率限制配置解析和排除分类解析服务，消除 `orchestrate.py` 与 `rate_limit.py` 之间的代码重复。将 `RateLimitConfig` dataclass、`resolve_rate_limit_config()`、`load_anti_crawl_strategy()` 和 `resolve_exclude_categories()` 合并到 `scripts.lib.config_resolver`。

## ADDED Requirements

### Requirement: `RateLimitConfig` dataclass

The system SHALL provide `RateLimitConfig` dataclass in `scripts.lib.config_resolver` with the following default fields:

| Field | Type | Default |
|-------|------|---------|
| `concurrency` | `int` | `1` |
| `batch_delay_ms` | `int` | `1000` |
| `max_retries` | `int` | `5` |
| `initial_delay_sec` | `float` | `1.0` |
| `backoff_multiplier` | `float` | `2.0` |
| `max_delay_sec` | `float` | `60.0` |
| `jitter` | `bool` | `True` |

#### Scenario: Default construction
- **WHEN** `RateLimitConfig()` is constructed with no arguments
- **THEN** all fields SHALL have their default values

### Requirement: `resolve_rate_limit_config()`

The system SHALL provide `resolve_rate_limit_config(strategy: dict, cli_args: argparse.Namespace) -> RateLimitConfig` in `scripts.lib.config_resolver`.

The function SHALL resolve final rate limit configuration using four-layer priority (highest first):
1. CLI arguments
2. Site Strategy local overrides (`api.rate_limit`)
3. Anti-Crawl tier template
4. Code safe defaults (the `RateLimitConfig` dataclass defaults)

The implementation SHALL be byte-identical in behavior to the current `rate_limit.py:resolve_rate_limit_config()` and `orchestrate.py:resolve_rate_limit_config()`, using `_load_anti_crawl_strategy()` for tier resolution.

#### Scenario: CLI override
- **WHEN** CLI argument `--concurrency 3` is passed with `strategy.api.rate_limit.concurrency = 1`
- **THEN** `config.concurrency` SHALL be `3` (CLI wins)

#### Scenario: Tier fallback chain
- **WHEN** strategy has `api.rate_limit.tier = "moderate"` and matching anti-crawl tier exists
- **THEN** SHALL apply tier values as layer 3 before site-local overrides

### Requirement: `load_anti_crawl_strategy()`

The system SHALL provide `load_anti_crawl_strategy(anti_crawl_id: str, repo_root: str = "") -> Optional[dict]` in `scripts.lib.config_resolver`.

The function SHALL:
1. Construct path from `sites/anti-crawl/<anti_crawl_id>.md`
2. Use `repo_root` parameter to resolve the base path; if empty, resolve relative to `lib/config_resolver.py`
3. Return parsed frontmatter dict, or `None` if file not found or missing frontmatter

#### Scenario: Load existing anti-crawl strategy
- **WHEN** `load_anti_crawl_strategy("default")` is called
- **THEN** SHALL return the parsed YAML frontmatter of `sites/anti-crawl/default.md`

### Requirement: `resolve_exclude_categories()`

The system SHALL provide `resolve_exclude_categories(strategy: dict, cli_excludes: list[str]) -> list[str]` in `scripts.lib.config_resolver`.

The function SHALL resolve exclude_categories with the following priority chain:
1. `api.exclude_categories` (top-level, new preferred location)
2. `api.homepage.exclude_categories` (legacy fallback)
3. CLI `--exclude-category` arguments (merged union)

The function SHALL return a deduplicated merged list.

#### Scenario: All three sources
- **WHEN** strategy has `api.exclude_categories: ["cat_a"]`, `api.homepage.exclude_categories: ["cat_b"]`, and CLI `--exclude-category cat_c`
- **THEN** SHALL return `["cat_a", "cat_b", "cat_c"]` (order unspecified but deduplicated)

#### Scenario: Empty sources
- **WHEN** no exclude categories are defined in any layer
- **THEN** SHALL return an empty list `[]`
