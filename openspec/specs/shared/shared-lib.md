# Shared Domain: Shared Libraries — Merged Spec

## Source Attribution

| Source Spec | Type | Notes |
|------------|------|-------|
| `shared-strategy-loader` | new | Unified strategy YAML frontmatter parsing |
| `shared-config-resolver` | new | Rate limit config resolution, anti-crawl loading, exclude categories |

Paths have been updated to reflect the current directory structure (`scripts.pipeline`, `scripts/pipeline/`).

---

# Shared Libraries Specification

## Purpose

Define the shared Python library modules under `scripts/lib/` that provide reusable services for strategy parsing, rate limit configuration resolution, anti-crawl strategy loading, and exclude category resolution. These modules eliminate code duplication across the pipeline and explore subsystems.

---

## Requirements

### Requirement: `parse_strategy()` 共享暴露

The system SHALL provide `parse_strategy(strategy_path: str) -> dict` as a shared function importable from `scripts.lib.strategy_loader`.

The function SHALL:
1. Open the file at `strategy_path` with UTF-8 encoding
2. Split content on `---` markers (first pair only) to extract YAML frontmatter
3. Parse frontmatter with `yaml.safe_load()`
4. Return the full parsed dict

#### Scenario: Standard strategy file

- **WHEN** `parse_strategy()` receives a path to a valid `strategy.md` with YAML frontmatter delimited by `---`
- **THEN** SHALL return the frontmatter as a dict
- **AND** SHALL raise `ValueError` if frontmatter is missing

### Requirement: `parse_frontmatter_from_content()` 预留占位

The system SHALL provide `parse_frontmatter_from_content(content: str) -> Optional[dict]` as a shared utility for parsing YAML frontmatter from raw file content strings using regex.

The function SHALL:
1. Apply regex `^---\n(.*?)\n---` with `re.S | re.M` flags
2. Parse matched group with `yaml.safe_load()`
3. Return `None` if no match found

#### Scenario: Content string with frontmatter

- **WHEN** `parse_frontmatter_from_content()` receives a string starting with `---\nkey: value\n---`
- **THEN** SHALL return `{"key": "value"}`
- **AND** SHALL return `None` for strings without `---` markers

### Requirement: 导入路径一致性

The system SHALL ensure that `scripts.lib` is importable as a Python 3 sub-package under the `scripts` package (which has no `__init__.py` at present — the import path relies on `sys.path` manipulation or `-m` invocation).

Given that pipeline scripts are invoked via `python3 -m scripts.pipeline`, the relative import `from ...lib.strategy_loader import parse_strategy` SHALL work correctly when invoked from `scripts/pipeline/pipeline/orchestrator.py`.

#### Scenario: Pipeline import

- **WHEN** `orchestrator.py` is loaded via `python3 -m scripts.pipeline`
- **AND** it uses `from ...lib.strategy_loader import parse_strategy`
- **THEN** SHALL resolve correctly without `ModuleNotFoundError`

---

## Config Resolver Requirements

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

The implementation SHALL be byte-identical in behavior to the current logic, using `_load_anti_crawl_strategy()` for tier resolution.

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
