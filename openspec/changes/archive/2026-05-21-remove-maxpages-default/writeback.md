# Writeback

## Change: remove-maxpages-default
## Date: 2026-05-21

---

## Writeback Targets

### Target 1: `openspec/specs/cli/cli-interface.md`

**Type:** Behavior spec update
**Scope:** Add maxPages null-semantics to CLI spec

**Field Mapping:**
- 在 `--max-pages` 参数相关区域添加行为声明：
  - `--max-pages` 未传入时，`maxPages` 为 `null`，表示不限制页面数
  - `--max-pages N` 传入时，行为不变（限制 N 页）

**Precondition:** verification.md PASS
**Evidence:** verification.md E1-E6

### Target 2: `docs/architecture/04-cli-reference.md`

**Type:** Documentation update
**Scope:** Update parameter tables for crawl/scrape commands

**Field Mapping:**
- L122: `--max-pages` default 从 `3` 改为 `None`（null）
- L152: `--max-pages` default 从 `10` 改为 `None`（null）
- L350: 已为 `None`，无需改动

**Precondition:** verification.md PASS
**Evidence:** verification.md E1-E2

---

## Execution Plan

1. Update `openspec/specs/cli/cli-interface.md` — 添加 maxPages null 语义声明
2. Update `docs/architecture/04-cli-reference.md` — 修改默认值列
3. Record evidence in this file

## Status

- [x] Target 1 executed — 2026-05-21, added `maxPages null semantics` requirement + scenarios to `openspec/specs/cli/cli-interface.md`
- [x] Target 2 executed — 2026-05-21, updated default values from `3`/`10` to `None (null)` in `docs/architecture/04-cli-reference.md` L122, L152
