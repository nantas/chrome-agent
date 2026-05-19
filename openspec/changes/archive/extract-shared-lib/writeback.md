# Writeback

## Change: extract-shared-lib
**Status:** done
**Date:** 2026-05-19

---

## Summary

提取共享库 `scripts/lib/`，消除 `orchestrate.py` 与 `rate_limit.py` 之间的代码重复。所有公共 API 保持不变，无行为变更。

## Modified Files

| Action | File |
|--------|------|
| Created | `scripts/lib/__init__.py` — 空包声明 |
| Created | `scripts/lib/strategy_loader.py` — `parse_strategy()` + `parse_frontmatter_from_content()` |
| Created | `scripts/lib/config_resolver.py` — `RateLimitConfig` + `resolve_rate_limit_config()` + `load_anti_crawl_strategy()` + `resolve_exclude_categories()` |
| Modified | `scripts/mediawiki-api-extract/pipeline/orchestrate.py` — 删除内联定义，改为从 `lib/` 导入 |
| Modified | `scripts/mediawiki-api-extract/pipeline/__init__.py` — 导出路径更新为 `lib/` |
| Deleted | `scripts/mediawiki-api-extract/pipeline/rate_limit.py` — 内容已迁移至 `lib/config_resolver.py` |

## Behavioral Changes

None. All public symbols retain identical names, signatures, and behavior.

## Capability Impact

| Capability | Change Type | Details |
|------------|-------------|---------|
| `shared-strategy-loader` | ADDED | 新模块 `scripts/lib/strategy_loader.py` |
| `shared-config-resolver` | ADDED | 新模块 `scripts/lib/config_resolver.py` |
| `mediawiki-api-extraction-pipeline` | MODIFIED | 函数来源外部化，行为不变 |

## Writeback Targets

### Obsidian vault: `chrome-agent/Changes/2026-05-19-extract-shared-lib.md`

- Change 状态: done
- 结论: 共享库提取成功，无行为变更，所有测试通过
- 关联 spec: `openspec/changes/extract-shared-lib/specs/`

### Project page: `chrome-agent/Architecture/Change 1 — 提取共享库 lib/`

- 能力变更: 新增 `shared-strategy-loader` 和 `shared-config-resolver`
- 修改 `mediawiki-api-extraction-pipeline` (函数来源外部化)
- 为 Change 2（统一转换器）和 Change 3（orchestrator 拆分）奠定基础
