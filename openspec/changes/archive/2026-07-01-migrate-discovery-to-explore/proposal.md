# Proposal

## 问题定义

chrome-agent 的 Discover 能力当前分裂在 pipeline 和 explore 两处，违反 [00-target-architecture.md](../../../docs/architecture/00-target-architecture.md) §3.4 的目标架构——pipeline 不应有 discover 阶段，页面清单来自 explore 冻结的策略 manifest。

| # | Drift | 证据 |
|---|-------|------|
| D1 | `discovery_homepage.py` 在 pipeline 而非 explore | `scripts/pipeline/pipeline/phases/discovery_homepage.py` |
| D2 | `discovery_allpages.py` 在 pipeline 而非 explore | `scripts/pipeline/pipeline/phases/discovery_allpages.py` |
| D3 | `discovery.py` 策略接口在 pipeline 而非 explore | `scripts/pipeline/strategies/discovery.py` |
| D4 | `homepage_parser.py` 与 `page_assigner.py` 是发现的依赖项，一并移 | 被 D1 引用 |
| D5 | pipeline orchestrator 包含完整的 discover 阶段逻辑 | `orchestrator.py:128-266` |

根因：pipeline 在无 --from-manifest 时会自行发现页面。这违反了「explore 发现→freeze→pipeline 消费」的单向数据流。pipeline 唯一的页面清单来源应为 strategy 中 explore 冻结的 manifest。

## 范围边界

**包含**：
- 移动 5 个文件到 `scripts/explore/`:
  - `discovery_homepage.py`, `discovery_allpages.py` → `scripts/explore/`
  - `discovery.py` (策略接口) → `scripts/explore/`
  - `homepage_parser.py`, `page_assigner.py` → `scripts/explore/`
- 更新所有 import 路径（从 relative `..` → absolute `scripts.pipeline.*`）
- 更新测试 import
- 修改 orchestrator: 移除 discover 阶段，**强制 `--from-manifest`** 或已有 manifest 文件
- 保留 `discovery_summary.py` 在 pipeline（管线输出产物）

**不包含**：
- 修改 explore 的 probe_chain 或 scaffold 流程
- 修改 pipeline fetch/convert/assemble 阶段

## Capabilities

### Modified Capabilities

- `discover-kernel`: 将 5 个发现相关模块从 pipeline 移到 explore；pipeline orchestrator 移除 discover 阶段

## Impact

| 受影响的文件 | 变更类型 |
|-------------|---------|
| `scripts/pipeline/pipeline/phases/discovery_homepage.py` | 移动到 `scripts/explore/` |
| `scripts/pipeline/pipeline/phases/discovery_allpages.py` | 移动到 `scripts/explore/` |
| `scripts/pipeline/strategies/discovery.py` | 移动到 `scripts/explore/` |
| `scripts/pipeline/pipeline/homepage_parser.py` | 移动到 `scripts/explore/` |
| `scripts/pipeline/pipeline/page_assigner.py` | 移动到 `scripts/explore/` |
| `scripts/pipeline/pipeline/orchestrator.py` | 移除 discover 阶段（~140 行），强制 `--from-manifest` |
| `scripts/pipeline/tests/test_source_category_unique_match.py` | 更新 import |
| `scripts/pipeline/tests/test_cat_dir_fallback_and_target_conflict.py` | 更新 import |
| `docs/architecture/01-overview.md` | 更新目录结构 |
| `docs/architecture/07-explore-workflow.md` | 新增 discover 步骤 |

## 关联绑定

- 关联 binding: [binding.md](./binding.md)
