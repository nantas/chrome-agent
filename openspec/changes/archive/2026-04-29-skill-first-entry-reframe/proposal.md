# Proposal

## 问题定义

当前仓库在治理层仍然强调 `workflow-driven`，并要求仓库内 workflow 负责判断 `Content Retrieval` 与 `Platform/Page Analysis`。但 Phase 5 落地后的全局 `chrome-agent` CLI 实际上直接暴露了 `fetch`、`explore`、`crawl` 等低层显式命令，使上层 agent 或调用者必须先做工作流判断，再选择具体命令。

这带来了三类实际问题：

1. **入口职责倒置**：本应由仓库工作流承担的路由决策，被迫提前暴露给外部调用者，导致“正式入口”不再体现 `workflow-driven` 设计原则。
2. **agent 场景退化**：实际调用时重新出现了 `repo-agent` 一类的外层包装需求，因为 CLI 本身缺少对意图路由、工作流指导和结果收敛的高层入口。
3. **Phase 5 假设失效**：归档 change 把“退役 global skill、CLI 成为唯一正式入口”作为核心决策，但实测表明这会让真实使用路径回退到仓外包装调用，破坏原本想收敛的入口模型。

## 范围边界

**范围内：**
- 恢复全局 `chrome-agent` skill 作为 agent-first 的正式主入口
- 明确新 skill 只负责意图路由、preflight 和结果包装，统一调用 `chrome-agent` CLI
- 保留 `chrome-agent` CLI 作为低层显式执行面与 shell/backend 入口
- 扩展 `explore` 的语义，使其成为 Platform/Page Analysis 的 CLI 后端，而不只是 strategy gap 探测
- 修改相关治理与安装规范，使 skill-first / CLI-backed 的双层入口模型成为正式契约

**排他边界：**
- 不恢复 `repo-agent` 或 `codex-agent` 作为正式运行时路径
- 不新增高层 `auto` / `run` CLI 命令
- 不修改现有 Scrapling / DevTools / CDP 引擎实现
- 不重写 `fetch` / `crawl` 的核心执行逻辑
- 不在本 change 中实现 verification / writeback 产物

## Capabilities

### New Capabilities
- `global-workflow-skill`: 定义全局 `chrome-agent` skill 的输入意图、CLI 路由规则、preflight 和结果契约

### Modified Capabilities
- `agents-governance`: 将正式入口模型改为 skill-first / CLI-backed，并重申仓库内 workflow 仍是执行权威
- `global-capability-cli`: 将 CLI 从唯一正式外部入口改为低层显式执行面，并补充 `explore` 的分析后端职责与结果字段
- `install-chain`: 将安装契约改为“CLI 是 skill 的后端前提，skill 是推荐的 agent 入口”，并移除对旧 dispatcher runtime 的依赖
- `master-plan`: 修正总体规划中 Phase 5 的入口叙事，使其反映 skill-first 的新正式模型

## Capabilities 待确认项

- [x] 能力清单已与用户确认：全局 skill 恢复为主入口；skill 包装 CLI；文档中不再提 `repo-agent`/`codex-agent`；CLI 继续保留 `fetch`/`explore`/`crawl` 低层显式命令；深度分析由扩展后的 `explore` 承接

## Impact

- **入口模型**：从 “CLI-first, skill retired” 改为 “skill-first, CLI-backed”
- **治理层**：`AGENTS.md`、README 与相关 spec 需要重新描述双层入口职责边界
- **CLI 契约**：帮助文本、结果字段和 `explore` 语义需要与新的 backend 角色保持一致
- **安装路径**：需要重新引入官方 skill 安装/升级路径，但其运行时只依赖 CLI，不再依赖旧 dispatcher agent
- **规划层**：已归档的 Phase 5 结论需要被一个新的 change 明确 supersede，而不是在实现层悄悄偏离

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标以 `binding.md` 为准
