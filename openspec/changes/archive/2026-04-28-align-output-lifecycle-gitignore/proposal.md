# Proposal

## 问题定义

当前仓库的 `.gitignore` 与治理定义不一致：治理文档将 `outputs/` 定义为 disposable run artifacts、`reports/` 定义为 durable evidence；但实际忽略规则却忽略了 `reports/`，且未忽略 `outputs/`。这会导致证据资产难以稳定纳入版本管理，同时临时运行产物可能被误提交。

## 范围边界

本 change 仅覆盖 artifact lifecycle 与版本控制边界一致性：
- 修正 `.gitignore` 的目录级策略，使其与治理约定一致
- 在 `output-lifecycle` spec 中补充版本控制要求，明确 durable/disposable 与 git ignore 的对应关系
- 增加 reports 产出门控，避免默认简单任务持续产生可跟踪报告文件

不包含：
- `clean` 子命令实现改造
- 报告自动归档与 retention policy
- 跨仓库 writeback 机制改动

## Capabilities

### New Capabilities
- `output-lifecycle-git-governance`: 为 artifact lifecycle 增加 git ignore 边界规则，约束 disposable 与 durable 的版本管理默认行为
- `report-emission-gating`: 对 durable reports 的产出进行工作流和参数门控，默认仅在 explore 或显式请求时产出

### Modified Capabilities
- `output-lifecycle`: 明确 `outputs/` 与 `reports/` 的版本控制一致性要求，防止治理与仓库配置偏离

## Capabilities 待确认项

- [x] 能力清单已与用户确认（执行“修改并补充 spec”请求）

## Impact

- 降低临时文件误提交风险
- 恢复报告资产可追溯性（durable evidence 可纳入版本管理）
- 为后续 `clean`/artifact contract 实现提供可验证基线

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 `binding.md`
