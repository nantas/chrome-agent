# mediawiki-api-extraction-pipeline Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: 用户确认将 `parse_strategy()`、`resolve_rate_limit_config()`、`_resolve_exclude_categories()` 和 `RateLimitConfig` 从 `orchestrate.py` 中提取至 `lib/`，并清理与 `rate_limit.py` 的重复代码

## 规范真源声明

- 本文件是此 capability 在本次 change 中的行为规范真源
- 仅记录本次 change 引入的行为变更（几乎所有行为不变，仅代码组织变化）
- 未修改的行为遵守 `openspec/specs/mediawiki-api-extraction-pipeline/spec.md` 的现有 requirements
- `orchestrate.py` 的主编排行为（`run_pipeline()` 的逻辑、退出码、缓存机制、阶段调度）不受本次 change 影响

## MODIFIED Requirements

### Requirement: 函数来源外部化

The system SHALL no longer define `parse_strategy()`, `RateLimitConfig`, `resolve_rate_limit_config()`, `_load_anti_crawl_strategy()`, and `_resolve_exclude_categories()` inline in `orchestrate.py`.

Instead, `orchestrate.py` SHALL import these functions and types from the shared library:

- `parse_strategy()` from `scripts.lib.strategy_loader`
- `resolve_rate_limit_config()` and `resolve_exclude_categories()` from `scripts.lib.config_resolver`
- `RateLimitConfig` from `scripts.lib.config_resolver`

The signature and behavior of each imported function SHALL be identical to the previous inline versions.

#### Scenario: run_pipeline imports correctly
- **WHEN** `run_pipeline()` is invoked
- **THEN** `parse_strategy(args.strategy)` SHALL work identically to before
- **AND** `resolve_rate_limit_config(strategy, args)` SHALL work identically to before
- **AND** `resolve_exclude_categories(strategy, cli_excludes)` SHALL work identically to before

### Requirement: `rate_limit.py` 删除

The system SHALL delete `scripts/mediawiki-api-extract/pipeline/rate_limit.py` after confirming that:
1. All its public symbols (`RateLimitConfig`, `resolve_rate_limit_config()`, `_load_anti_crawl_strategy()`) are migrated to `scripts.lib.config_resolver`
2. `__init__.py` no longer imports from `rate_limit.py`
3. No other file imports from `rate_limit.py`

#### Scenario: No orphan imports
- **WHEN** all changes are applied
- **THEN** `grep -r "rate_limit" scripts/` SHALL NOT match any import statements
- **AND** `python3 -m scripts.mediawiki-api-extract --help` SHALL succeed

## RENAMED Requirements

- FROM: `_resolve_exclude_categories(strategy, cli_excludes)` (private, orchestrate.py)
- TO: `resolve_exclude_categories(strategy, cli_excludes)` (public, config_resolver.py)
