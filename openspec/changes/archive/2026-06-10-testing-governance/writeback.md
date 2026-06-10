# Writeback (v2)

## Change: testing-governance
## Source: verification.md v2 (PASS)
## Date: 2026-06-10

---

## Verification Feedback Responses

### WARNING 1 — explore-scaffold wiring
**Action**: Updated `specs/explore-scaffold/spec.md` to reflect current reality: agent recommends via `recommend_samples()`, user manually writes `samples` to frontmatter. Full auto-wiring deferred.

### WARNING 2 — Synthetic Nintendo samples
**Action**: Replaced with 3 real pages from `/tmp/nintendo-final-html/`:
- `Account_Guide/4-4_Account_Link_Status.html` (15,277 chars)
- `Independent_Server_Setup_Manual/4-7.4_Account_API.html` (14,439 chars)
- `Online_Play_Guide/8_Previous_Revision_History.html` (34,724 chars)

Cache entries at `.cache/chrome-cdp/developer.nintendo.com/`, golden files at `sites/strategies/developer.nintendo.com/samples/`.

### SUGGESTION 3 — strategy_loader reuse
**Action**: `_parse_samples_field()` now delegates to `strategy_loader.parse_strategy()` — single parse path.

### SUGGESTION 4 — Combined structural assertion + golden diff reporting
**Action**: Test method collects assertion failures, runs golden diff regardless, reports all issues combined.

---

## Writeback Targets

### 1. AGENTS.md §0.5 — Hard Constraints

**Status: ✅ Done**

- **C5 扩展**: 补充了测试目录约定（`tests/` 顶层）、运行命令
- **C9 新增**: 测试义务硬约束

### 2. AGENTS.md §9 — Reference Index

**Status: ✅ Done**

Added 3 new entries: `tests/`, `scripts/test_runner.py`, `scripts/lib/test_assertions.py`

### 3. AGENTS.md §11 — Prerequisite Reading

**Status: ✅ Done**

Added: **测试相关** → `08-tech-stack.md` §4 + testing-governance specs

### 4. docs/architecture/08-tech-stack.md §4 — Test Infrastructure

**Status: ✅ Done**

完全重写为完整测试基础设施文档

### 5. docs/architecture/03-strategy-schema.md — samples field

**Status: ✅ Done**

新增 `samples` 字段定义 + 独立章节

---

## Writeback Summary

| Target | Type | Status |
|--------|------|--------|
| AGENTS.md §0.5 C5 | Expand | ✅ |
| AGENTS.md §0.5 C9 | New | ✅ |
| AGENTS.md §9 | New entries | ✅ |
| AGENTS.md §11 | New row | ✅ |
| 08-tech-stack.md §4 | Rewrite | ✅ |
| 03-strategy-schema.md | New section | ✅ |

All writeback targets executed during implementation phase. No post-hoc writes needed.
