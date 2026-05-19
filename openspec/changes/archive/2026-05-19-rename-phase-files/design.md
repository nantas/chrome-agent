# Design

## Context

本 change 是 `docs/plans/2026-05-19-structure-refactor-and-docs.md` 规划的 5 个实现 change 中的第 4 个，依赖 Change 3（拆分 orchestrator + 重命名包）已完成。

Change 3 将 `mediawiki-api-extract` 重命名为 `pipeline`，提取了 `registry.py`、`discovery_summary.py`、`phases/fetch.py`、`phases/convert.py`，并将 `orchestrate.py` 从 1208 行降至 457 行。但 Phase 文件本身（`phase_0/a/b/c.py`）保留了旧命名，且 `phase_b.py` 中存在死代码和跨文件反向导入。

当前 `pipeline/pipeline/` 内部依赖图（LSP 验证）：

```
orchestrate.py
  ├── .phase_0  → run_phase_0       ← 活跃 (line 183)
  ├── .phase_a  → run_phase_a       ← 活跃 (line 197)
  ├── .phase_b  → run_phase_b       ← ❌ 死导入 (imported only)
  ├── .phase_c  → run_phase_c       ← 活跃 (line 396)
  ├── .phases.fetch                 ← 活跃 (反向导入 phase_b.fetch_single_page)
  ├── .phases.convert               ← 活跃 (反向导入 phase_b.convert_single_page)
  └── .registry / .discovery_summary / lib.*

phase_b.py 内部:
  fetch_single_page    ← phases/fetch.py 引用 (活跃)
  convert_single_page  ← phases/convert.py 引用 (活跃)
  _process_html_page   ← convert_single_page 内部调用 (活跃)
  process_single_page  ← run_phase_b 内部调用 (死链)
  run_phase_b          ← 零外部调用 (死代码)
```

## Goals / Non-Goals

**Goals:**

- 将 `phase_0.py`、`phase_a.py`、`phase_c.py` 移入 `phases/` 并按功能重命名
- 将 `phase_b.py` 中活跃函数内化到 `phases/fetch.py` 和 `phases/convert.py`
- 删除 `phase_b.py` 中的死代码（`run_phase_b` + `process_single_page`）
- 删除 `phase_b.py` 本身
- 删除顶层残留旧文件
- 更新 `orchestrate.py` 的 import 路径
- 可选：`orchestrate.py` → `orchestrator.py` 命名对齐

**Non-Goals:**

- 不重命名函数名（`run_phase_0` 等保持不变）
- 不修改 `orchestrate.py` 内部逻辑
- 不涉及 CLI 层或 docs 层变更
- 不新增 spec 或修改已有 spec

## Decisions

### D1: phase_b.py 处理策略 — 内化 + 删除

**决策**：将 `fetch_single_page`、`convert_single_page`、`_process_html_page` 分别复制到 `phases/fetch.py` 和 `phases/convert.py`，然后删除 `phase_b.py`。同时删除死代码 `process_single_page` 和 `run_phase_b`。

**理由**：
- 活跃函数仅有一个外部调用方（各自的 phases 文件），内化消除反向导入
- 死代码形成闭环（`run_phase_b` → `process_single_page`），无外部引用，安全删除
- `phase_b.py` 删除后不再存在"两套提取实现"的混淆风险

**替代方案**：保留 `phase_b.py` 作为纯工具模块，仅删除死代码。被否决，因为保留了无语义的文件名。

### D2: 重命名方式 — git mv 而非新建

**决策**：对 `phase_0/a/c.py` 使用 `git mv` 移入 `phases/` 子目录，保留 git 历史追踪。

**理由**：这些文件内容完整保留，仅路径和 import 变化。

### D3: import 路径调整规则

从 `pipeline/pipeline/` 移入 `pipeline/pipeline/phases/` 后，相对导入深度增加一级：

| 原路径 | 新路径 | import 调整 |
|--------|--------|------------|
| `.homepage_parser` | `..homepage_parser` | 多加一层 `.` |
| `..client` | `...client` | 多加一层 `.` |
| `..strategies` | `...strategies` | 多加一层 `.` |

### D4: orchestrate.py → orchestrator.py（可选）

**决策**：纳入本次 change。Change 3 规划目标名称为 `orchestrator.py` 但实际保留了 `orchestrate.py`。

**影响范围**：
- `pipeline/pipeline/__init__.py` — re-export 路径更新
- `pipeline/cli.py` — import 路径更新
- 不影响任何外部调用方（`-m scripts.pipeline` 入口不变）

### D5: 不重命名函数名

**决策**：函数名（`run_phase_0`、`run_phase_a`、`run_phase_c`）保持不变。

**理由**：重命名函数会增加 diff 噪声，且本 change 的核心目标是文件名对齐。函数名可作为后续可选优化。

## Risks / Migration

| 风险 | 等级 | 缓解 |
|------|------|------|
| import 路径遗漏 | 低 | `grep -rn "from.*\.phase_0\|from.*\.phase_a\|from.*\.phase_b\|from.*\.phase_c" scripts/pipeline/` 确认零残留 |
| 内化函数签名不一致 | 低 | 逐字复制，不修改函数体 |
| `__init__.py` re-export 断裂 | 低 | LSP 确认 `__init__.py` 不 re-export phase 函数；`orchestrator` 重命名后更新 `__init__.py` 的 from 路径 |
| 顶层残留文件被外部引用 | 极低 | LSP references 确认零引用 |

**Migration**：无需迁移。所有变更对 `-m scripts.pipeline` 调用方透明。
