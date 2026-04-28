# Proposal

## 问题定义

当前仓库的 Scrapling 安装链和工作流入口存在三个结构性问题：

1. **受 git 跟踪文件包含宿主机绝对路径**：`docs/setup/scrapling-first-workflow.md`、`.codex/config.toml`、`opencode.json` 等位置直接写入 `/Users/<user>/...` 路径，导致仓库在用户切换或目录迁移后立即失效。

2. **工作流缺少 Scrapling CLI 前置可用性检查**：仓库已声明 Scrapling-first，但在 Content Retrieval 和相关分析路径执行前，没有统一检查 `scrapling` CLI / MCP 启动所需环境是否可用，也没有明确的“不可用时先安装再继续”的行为契约。

3. **用户级环境变量写入缺少确认边界**：为了去掉仓库内绝对路径，需要引入环境变量表达 Scrapling 可执行文件位置；但将变量写入 `/Users/nantas-agent/.zshenv` 属于用户 shell 环境变更，当前仓库没有定义何时询问、何时停止，以及未确认时的安全默认行为。

这些问题已经在当前机器上暴露为 Scrapling MCP 启动失败：项目级配置仍指向旧用户缓存目录里的 Scrapling 可执行文件，而当前执行用户已经变化，导致原路径失效。

## 范围边界

**范围内：**
- 定义 Scrapling CLI 的环境变量契约，替代仓库受跟踪文件中的宿主机绝对路径
- 定义所有工作流执行前的 Scrapling 可用性前置检查
- 定义 Scrapling 不可用时的安装保障流程与失败分流
- 定义是否写入 `/Users/nantas-agent/.zshenv` 的用户确认步骤与默认行为
- 更新仓库治理、Scrapling-first 规范与 setup 文档，使其与上述行为一致

**排他边界：**
- 不改变 Scrapling / Chrome fallback 的职责边界
- 不引入全局凭据管理或自动化 shell profile 写入
- 不要求修改用户的全局 Codex profile
- 不新增引擎实现，只调整安装链、配置表达和工作流前置行为

## Capabilities

### New Capabilities
- `scrapling-cli-environment`: 定义 Scrapling CLI 安装位置、环境变量解析、缺失时安装保障和 `.zshenv` 确认边界的统一契约；将生成 `specs/scrapling-cli-environment/spec.md`

### Modified Capabilities
- `agents-governance`: 为所有工作流增加 Scrapling 可用性前置检查、失败时先安装后继续、以及用户 shell 环境确认边界；将生成 `specs/agents-governance/spec.md`
- `scrapling-first-browser-workflow`: 将 setup 与 MCP 配置从绝对路径迁移到环境变量表达，并定义缺少 CLI 时的恢复与验证行为；将生成 `specs/scrapling-first-browser-workflow/spec.md`

## Capabilities 待确认项

- [x] 能力清单已与用户确认（通过本轮需求补充确认：去绝对路径、改环境变量、前置检查 Scrapling CLI、不可用时先确保安装、写入 `/Users/nantas-agent/.zshenv` 前先征求用户确认）

## Impact

- `openspec/specs/` 新增 1 个 capability 目录：`scrapling-cli-environment`
- `openspec/specs/` 修改 2 个既有 spec：`agents-governance`、`scrapling-first-browser-workflow`
- 仓库内受跟踪配置与文档将从宿主机绝对路径迁移到环境变量表达，至少覆盖 `.codex/config.toml`、`opencode.json`、`docs/setup/scrapling-first-workflow.md`
- 工作流执行入口将增加 Scrapling preflight，影响 Content Retrieval 与依赖 Scrapling-first 的分析路径
- setup/playbook 文档将补充安装恢复、环境变量确认和 smoke-check 验证要求

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - `20_项目/chrome-agent/chrome-agent.md`
  - `20_项目/chrome-agent/Writeback记录.md`
