# Proposal

## 问题定义

`pipeline/pipeline/` 内的 Phase 文件使用 `phase_0.py`、`phase_a.py`、`phase_b.py`、`phase_c.py` 命名，与实际功能严重脱节：

- `phase_0.py` 实际是**首页驱动发现**，"Phase 0" 无语义
- `phase_a.py` 实际是 **Allpages 发现**，"Phase A" 无语义
- `phase_b.py` 实际是**内容提取**（fetch + convert），且 Change 3 已提取 `phases/fetch.py` 和 `phases/convert.py` 作为新路径，`phase_b.py` 中仅剩 `run_phase_b` 死代码和被新 phases 文件反向导入的工具函数
- `phase_c.py` 实际是**输出组装**

此外，`scripts/pipeline/` 顶层残留旧版 `phase_a.py`、`phase_b.py`、`phase_c.py`（Change 3 包重命名前的遗留），零外部引用但未清理。

LSP `references` 验证结果：
- `run_phase_b`（`phase_b.py:252`）：仅被 `orchestrate.py:20` import，零调用点 → **死代码**
- `process_single_page`（`phase_b.py:134`）：仅被 `run_phase_b` 内部调用 → **闭环死链**
- `fetch_single_page`（`phase_b.py:27`）：被 `phases/fetch.py` 引用 → **活跃**
- `convert_single_page`（`phase_b.py:44`）：被 `phases/convert.py` 引用 → **活跃**
- `_process_html_page`（`phase_b.py:167`）：仅被 `convert_single_page` 调用 → **活跃，随 convert 走**

## 范围边界

### 包含

- `phase_0.py` → `phases/discovery_homepage.py`（重命名 + import 路径调整）
- `phase_a.py` → `phases/discovery_allpages.py`（重命名 + import 路径调整）
- `phase_c.py` → `phases/assemble.py`（重命名 + import 路径调整）
- `phase_b.py` 拆分：活跃函数内化到 `phases/fetch.py` 和 `phases/convert.py`，死代码删除
- `orchestrate.py` import 更新
- 顶层残留 `scripts/pipeline/phase_{a,b,c}.py` 删除
- 可选：`orchestrate.py` → `orchestrator.py`（Change 3 遗留的命名对齐）

### 不包含

- 函数名重命名（`run_phase_0` → `run_discovery_homepage` 等）— 可选优化，另行处理
- `orchestrate.py` 内部逻辑重构 — 已在 Change 3 完成
- CLI 层（`chrome-agent-cli.mjs`）重构 — Change 5 范围
- `docs/architecture/` 文档 — Change D1 范围

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `pipeline-phase-naming`: 将 Phase 文件名与实际功能对齐，消除命名漂移；合并 phase_b.py 的活跃函数到对应 phases/ 文件，删除死代码

## Capabilities 待确认项

- [x] 能力清单已与用户确认（纯重构，无新增能力）

## Impact

| 影响维度 | 说明 |
|---------|------|
| 公共 API | `pipeline/__init__.py` 不 re-export 任何 phase 函数，公共 API 无变化 |
| 调用方 | `orchestrate.py` 是所有 phase 函数的唯一外部调用方，import 路径需更新 |
| phases/fetch.py | 吸收 `fetch_single_page`，消除对 `phase_b.py` 的反向导入 |
| phases/convert.py | 吸收 `convert_single_page` + `_process_html_page`，消除对 `phase_b.py` 的反向导入 |
| 测试 | `test_discovery_summary.py` 不依赖任何 phase 文件，无影响 |
| CLI | `chrome-agent-cli.mjs` 通过 `-m scripts.pipeline` 调用，不直接引用 phase 文件，无影响 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md
