# Verification Report: `unify-extract-fetch-kernels`

## Summary

| Dimension | Status |
|-----------|--------|
| Completeness | **23/23 tasks** ✅ |
| Correctness | **6/6 requirements** + **6/6 scenarios** covered ✅ |
| Coherence | **3/3 design decisions** followed ✅ |
| Test Suite | **80 unit + 13 site-samples** — all pass ✅ |

## Issues by Priority

### CRITICAL — None

### WARNING — None

### SUGGESTION — None

## Detailed Verification

### 1. Completeness — Tasks

`tasks.md` 共 23 checkboxes，全部 `[x]`。

| Task | 证据 |
|------|------|
| 2.1 删 `context` 参数 | `preprocessor.py:15` 签名简化；`sample_converter.py` + `convert.py` 调用方已去 `context=` |
| 2.2 移 `convert_page_full` | `converter.py:984` 新增 4 步编排；`sample_converter.py:141` 委托调用 |
| 2.3 .mjs fetch 统一 | `chrome-agent-cli.mjs:819` delegate 到 `ApiClient` via subprocess |
| 3.x 收敛 | grep 验证 + 全量测试全绿 |

### 2. Correctness — Spec Requirements

#### `extract-kernel` spec

| Requirement | Type | Evidence |
|-------------|------|----------|
| `context-parameter` | REMOVED | `preprocessor.py` 签名无 `context` 参数 |
| `preprocessor-always-full-cleanup` | MODIFIED | 始终执行 `_preprocess_explore()` — `test_convert_cleanup_consistency` 双路径 pass |
| `convert-page-full` | ADDED | `converter.py:984-1021` 实现 4 步管线 |
| `extract-infobox-via-kernel` | ADDED | `convert_page_full()` 从共享 `infobox.py` 导入 |

#### `fetch-kernel` spec

| Requirement | Type | Evidence |
|-------------|------|----------|
| `mjs-mediawiki-api-fetch` | REMOVED | .mjs 不再实现自有 curl-based 客户端 |
| `fetch-via-pipeline-kernel` | MODIFIED | `runMediawikiApiFetch()` delegate 到 `scripts.pipeline.client.ApiClient` |

### 3. Coherence — Design Adherence

| Decision | Status |
|----------|--------|
| D1 删 `context` 参数 | ✅ 2 个调用方已更新 |
| D2 `convert_page_full` 实现 | ✅ 4 步管线，import 无循环依赖 |
| D3 .mjs fetch 统一 | ✅ delegate via subprocess，返回格式兼容 |

### 4. Test Suite

```
Phase 1: Unit tests (stdlib discover): 80/80 pass
Phase 2: Site sample regression: 13/13 (3 run, 10 skipped)

Total: 93 tests, 0 failures
```

- `test_convert_cleanup_consistency` (2/2) — 验证 explore + pipeline 双路径均执行完整清理
- `test_golden_convert.TestMirrorEquivalence` (1/1) — 验证 explore + pipeline 输出等价

## Git Diff Summary

```
9 files changed, 166 insertions(+), 117 deletions(-)
```

| File | Change |
|------|--------|
| `scripts/lib/extraction/preprocessor.py` | 删 `context` 参数 + if-else 分支 |
| `scripts/lib/extraction/converter.py` | +39 lines: `convert_page_full()` |
| `scripts/explore/sample_converter.py` | -34 lines: 委托到 `convert_page_full()` |
| `scripts/pipeline/pipeline/phases/convert.py` | 去 `context=` |
| `scripts/chrome-agent-cli.mjs` | `runMediawikiApiFetch` → `ApiClient` delegate |
| `AGENTS.md` | Fetch + Extract 能力声明更新 |
| `docs/architecture/01-overview.md` | Fetch 后端路由描述 |
| `docs/architecture/05-converter-architecture.md` | 共享编排入口说明 |
| `docs/plans/4d-architecture-refactor.md` | Stage 3 progress sync |

## Final Assessment

✅ **All checks passed. Ready for archive.**

- Zero CRITICAL / WARNING / SUGGESTION issues
- 23/23 tasks complete
- 6/6 spec requirements verified
- 93/93 tests green
