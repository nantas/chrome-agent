# Writeback

## Change: enhance-arch-docs-readability
## Date: 2026-05-20
## Verification: PASS (see verification.md)

---

## Summary

为 `docs/architecture/` 中 5 篇文档执行可读性改进：新增 7 个 ASCII 结构化视觉元素，修正 2 个过时引用问题。所有变更通过验证，无残留过时引用。

## Writeback Targets

### 1. `docs/architecture/03-strategy-schema.md`

**Status**: ✅ Updated

**Changes**:
- 新增 "系统上下文图"：展示策略文件在 chrome-agent 架构中的位置关系（strategy ↔ registry ↔ pipeline ↔ explore ↔ extraction）
- 新增 "字段层级树"：YAML key 嵌套关系树状图，✅ 必填 / ❌ 可选标记
- 新增 "content_profile 策略路由图"：5 个维度 → `_STRATEGY_REGISTRY` → Python 策略类

**Writeback evidence**: 3 个 diagram + source annotations 已插入，覆盖 `docs-strategy-schema-diagrams` spec 全部要求。

### 2. `docs/architecture/04-cli-reference.md`

**Status**: ✅ Updated

**Changes**:
- 新增 "命令路由决策树"：explore/fetch/crawl/scrape/batch 路由路径 + 函数名 + 行号
- 新增 "管线阶段流程图"：`--discovery`/`--phase` 参数如何决定五阶段执行

**Writeback evidence**: 2 个 diagram + source annotations 已插入，覆盖 `docs-cli-routing-diagrams` spec 全部要求。

### 3. `docs/architecture/08-tech-stack.md`

**Status**: ✅ Updated

**Changes**:
- 新增 "System Architecture" 节 + 组件依赖关系图：Node.js CLI → Python → lib/ → engines → output
- 新增 "安装脚本链流程图"：install-chrome-agent-cli.sh → 4 个 preflight 脚本
- 修正 Key File Reference 表中的 `html_to_markdown.py` → `converter.py` 路径

**Writeback evidence**: 2 个 diagram + 1 个路径修正，覆盖 `docs-tech-stack-dependency-graph` spec 全部要求。

### 4. `docs/architecture/02-pipeline-flow.md`

**Status**: ✅ Updated

**Changes**:
- Phase 0 → Homepage Discovery（标题、流程图节点、函数引用）
- Phase A → Allpages Discovery（标题、流程图节点、函数引用）
- Phase C → Assembly（标题、流程图节点、函数引用）
- Phase Fetch → Fetch, Phase Convert → Convert
- `run_phase_0()` → `run_homepage_discovery()`
- `run_phase_a()` → `run_allpages_discovery()`
- `run_phase_c()` → `run_assemble()`
- `run_phase_convert()` → `run_convert()`
- `run_phase_fetch()` → `run_fetch()`

**Writeback evidence**: `grep "Phase [0ABC]\|run_phase_" 02-pipeline-flow.md` → zero matches。覆盖 `docs-pipeline-flow-phase-naming` spec 全部要求。

### 5. `docs/architecture/05-converter-architecture.md`

**Status**: ✅ Updated

**Changes**:
- 将 `html_to_markdown.py` 从 Pipeline Converters 表移至 Shared Extraction Library 表，路径更新为 `scripts/lib/extraction/converter.py`
- 更新 §2.3 Design Decision 说明：反映 `finish-refactor-cleanup` 后的实际状态
- 更新概述图、数据流图、约束说明中所有路径引用

**Writeback evidence**: `grep "pipeline/converters/html_to_markdown" 05-converter-architecture.md` → zero matches。覆盖 `docs-converter-path-update` spec 全部要求。

---

## Non-Target Files (Known Stale References)

以下文件包含过时的 Phase/路径引用，但在本 change 范围外（proposal 明确排除）：

| File | Stale References | Recommendation |
|------|-----------------|----------------|
| `docs/architecture/01-overview.md` | `Phase 0`, `Phase A`, `Phase C` in directory tree diagram | Future cleanup |
| `docs/architecture/07-explore-workflow.md` | `pipeline/converters/html_to_markdown.py` in tree diagram | Future cleanup |

---

## Conclusion

所有 5 个 writeback target 已完成更新。变更内容：
- 7 个 ASCII 图表新增（3 + 2 + 2）
- 8 个 Phase 命名更新
- 1 个文件路径迁移更新（html_to_markdown.py → converter.py）
- 1 个 Design Decision 理由更新

无代码变更。无 AGENTS.md 变更。无新增/删除文件。
