# Writeback

## Targets

### WB-1: `docs/plans/2026-05-19-structure-refactor-and-docs.md` — Change 3 状态更新
- **Action**: Update Change 3 status from "planned" / "in-progress" to "complete"
- **Fields**: Status, completion date, summary of changes
- **Precondition**: verification.md shows all spec requirements satisfied
- **Evidence**: verification.md spec-to-implementation matrix

### WB-2: `AGENTS.md` §7 Pipeline Strategy Schema 治理
- **Action**: Update `_STRATEGY_REGISTRY` authority path
- **Old**: `scripts/mediawiki-api-extract/pipeline/orchestrate.py`
- **New**: `scripts/pipeline/pipeline/registry.py`
- **Evidence**: File exists at new path, exports `STRATEGY_REGISTRY`

### WB-3: `AGENTS.md` §9 Development — Python 脚本约定
- **Action**: Update package reference, call method, `__main__.py` description
- **Fields to update**:
  - Package path: `scripts/mediawiki-api-extract/` → `scripts/pipeline/`
  - Call method: `python3 -m scripts.mediawiki-api-extract` → `python3 -m scripts.pipeline`
  - `__main__.py` section: Remove "must use `-m`" caveat (no longer needed — `pipeline` has no hyphen)
  - `_STRATEGY_REGISTRY` authority path in §9 code references
- **Evidence**: verification.md pipeline-package-identity requirements all PASS

### WB-4: `AGENTS.md` §9 常见陷阱
- **Action**: Update `__main__.py` 陷阱说明
- **Old**: "不能直接 `python3 scripts/mediawiki-api-extract/`，必须用 `-m` 方式调用"
- **New**: Package renamed to `pipeline`, standard `-m` invocation works without workaround
- **Evidence**: `__main__.py` simplified, no subprocess re-invoke

### WB-5: `AGENTS.md` §10 Reference Index
- **Action**: Update MediaWiki API 提取管线 reference path
- **Old**: `scripts/mediawiki-api-extract`
- **New**: `scripts/pipeline`
- **Evidence**: Directory renamed

### WB-6: `AGENTS.md` §8 已注册引擎概览
- **Action**: No changes needed — engine registry does not reference package path
- **Status**: N/A
