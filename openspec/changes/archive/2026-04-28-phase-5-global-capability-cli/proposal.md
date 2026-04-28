# Proposal

## 问题定义

当前仓库已经完成 Phase 1-4 的治理基础、引擎契约冻结、策略库标准化和引擎扩展治理，但对外入口仍停留在仓库内工作流和历史 global skill 的组合上，缺少一个正式、可全局调用、又仍然以仓库内规则为执行权威的能力入口。

当前问题集中在四点：

1. **对外入口不稳定**：现有 `skills/chrome-agent` 是 thin dispatcher skill，本质是 prompt transport，不是正式的 capability contract，无法作为长期的全局调用面。
2. **repo 定位契约陈旧**：旧入口依赖 `CHROME_AGENT_REPO`，而 OrbitOS 已经具备 `repo-registry` 能力，现有约定没有切换到 `repo://chrome-agent` 优先解析。
3. **crawl 仍停留在“规划中”**：底层引擎、site-strategy 的 `entry_points / links_to / pagination` 已存在，但缺少一个正式的 crawl capability 来定义边界、失败语义和前置条件。
4. **安装链与产物闭环没有服务于统一入口**：`scrapling-cli` preflight 已存在，`reports/` 也已有大量产物，但没有一个围绕全局 CLI 的 install/doctor/clean/output lifecycle 契约。

## 范围边界

**范围内：**
- 定义一个 repo-backed 的全局 `chrome-agent` CLI，作为唯一正式外部入口
- CLI 一级能力包含 `explore`、`fetch`、`crawl`、`doctor`、`clean`
- repo 解析使用 `repo-registry` 为主，`CHROME_AGENT_REPO` 为 fallback
- `explore` / `fetch` / `crawl` 的执行权威仍留在目标仓库内部，遵循该仓库的 `AGENTS.md` 和 specs
- 将 `crawl` 正式化为 strategy-guided traversal，只允许基于已有 `site-strategy` 的受边界遍历
- 新增 install-chain 和 output-lifecycle 两个支撑能力，分别承接 launcher 安装/doctor 与 artifact/clean 契约
- 修改 `agents-governance` 和 `master-plan`，使仓库治理和阶段规划与新入口模型一致

**排他边界：**
- 不把 `fetch` / `crawl` 重写成复杂的纯脚本执行运行时
- 不实现开放式递归 spider
- 不保留 `skills/chrome-agent` 作为正式入口
- 不修改现有引擎实现
- 不在本阶段引入远程调度、运行时监控或分布式执行

## Capabilities

### New Capabilities
- `global-capability-cli`: 定义全局 `chrome-agent` CLI 的命令面、repo 解析、JSON-first 返回契约和 repo-local dispatch 规则
- `install-chain`: 定义全局薄启动器的安装、repo-registry 依赖、环境变量 fallback、runtime doctor 和失败分流
- `output-lifecycle`: 定义 CLI 产物分类、默认落盘位置、durable/disposable 区分和 `clean` 工作流
- `strategy-guided-crawl`: 定义基于 `site-strategy` 的 crawl capability、边界、停机条件和“缺少策略时先 explore”规则

### Modified Capabilities
- `agents-governance`: 将仓库的对外正式入口更新为 repo-backed global CLI，并声明仓库内 AGENTS/specs 仍是执行权威
- `master-plan`: 将 Phase 5 从“安装链与清理闭环”重写为“全局 capability CLI”，并把 install-chain/output-lifecycle 降为其支撑面

## Capabilities 待确认项

- [x] 能力清单已与用户确认：CLI 为主入口、repo-registry 优先、strategy-guided crawl 正式化、旧 skill 移除、`CHROME_AGENT_REPO` 仅保留 fallback、JSON-first 返回契约、`doctor` 与 `clean` 作为正式一级命令

## Impact

- **全局入口模型**：从 `skills/chrome-agent` 切换到全局薄启动器 + repo-backed CLI
- **规划层**：`docs/governance-and-capability-plan.md` 与 `openspec/specs/master-plan/spec.md` 的 Phase 5 定义需要同步改写
- **治理层**：`openspec/specs/agents-governance/spec.md` 需要声明全局 CLI 与仓库执行权威的关系
- **运行支撑层**：需要引入 `install-chain`、`output-lifecycle`、`strategy-guided-crawl` 的正式 specs
- **产物与清理**：`clean` 不再是松散约定，而是 CLI 的正式能力

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标以 `binding.md` 为准
