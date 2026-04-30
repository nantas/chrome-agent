# Proposal

## 问题定义

当前 `chrome-agent` 的默认本地仓库解析链路仍然是 `--repo` override → `repo://chrome-agent` → `CHROME_AGENT_REPO` fallback。对于高频的 skill-first 使用场景，这意味着每次 workflow skill 触发 `chrome-agent doctor --format json` 或后续 workflow backend 时，runtime 都会先读取 repo-registry，再决定是否使用已经存在的 `CHROME_AGENT_REPO`。

这带来三类问题：

1. **热路径不够短**：agent-first 高频调用的默认路径没有直接利用本地已配置的环境变量，仍然先走 registry 解析。
2. **默认权威不符合使用习惯**：实际高频使用者通常已经把 `CHROME_AGENT_REPO` 配好，但当前契约仍把它定义为 fallback，而不是默认事实来源。
3. **安装与运行叙事分裂**：skill-first 入口已经成立，但运行时默认解析模型仍偏向 CLI-first / registry-first，和“本机高频调用优先快速进入目标仓”的目标不完全一致。

## 范围边界

**范围内：**
- 将默认运行时仓库解析改为 `CHROME_AGENT_REPO` 优先
- 保留显式 `--repo <path|repo://id>` override 最高优先级
- 当 `CHROME_AGENT_REPO` 缺失或无效时，默认停止执行并要求用户显式指定 `chrome-agent` 仓库路径
- 保留 `repo://...` 解析能力，但仅作为显式 `--repo repo://...` 调用路径的一部分
- 更新 skill / CLI / install / README / master-plan 对该契约的描述

**排他边界：**
- 不修改 `fetch` / `explore` / `crawl` 的核心抓取逻辑
- 不改变 workflow skill 的 doctor-first / CLI-backed 基本模型
- 不扩展新的高层 CLI 命令
- 不重做 repo-registry 工具本身
- 不把 `CHROME_AGENT_REPO` 自动写入用户 shell 配置，除非显式安装/迁移流程要求

## Capabilities

### New Capabilities

### Modified Capabilities
- `global-workflow-skill`: 调整 skill 依赖的 backend preflight 语义，使其默认建立在 env-first 仓库解析之上
- `global-capability-cli`: 将默认仓库解析顺序改成 `--repo` override → `CHROME_AGENT_REPO` → failure，并把 repo-registry 降为显式 repo-ref 路径
- `install-chain`: 将 `CHROME_AGENT_REPO` 提升为默认运行前提，调整 doctor 和安装文档的默认契约
- `master-plan`: 将 Phase 5 之后的入口/安装叙事从 repo-registry-first 改成 env-first 的 skill-first 高频使用模型

## Capabilities 待确认项

- [x] 能力清单已与用户确认：范围覆盖整个 CLI 默认解析链路；冲突时 env 胜出；env 缺失或无效时停止并要求用户显式指定仓库路径；安装契约把 env 提升为默认运行前提

## Impact

- **运行时行为**：默认调用不再自动读取 repo-registry 作为第一步，而是优先使用 `CHROME_AGENT_REPO`
- **失败语义**：当 env 缺失或无效时，默认从“透明 fallback 到 registry”改成“停止并要求显式指定路径”
- **安装契约**：`CHROME_AGENT_REPO` 从兼容 fallback 提升为默认运行前提
- **文档层**：README、playbook、项目页和相关 spec 需要统一删除或弱化 repo-registry-first 叙事

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
  - `repo://orbitos/20_项目/chrome-agent/Writeback记录.md`
