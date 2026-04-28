# Design

## Context

当前仓库的 Scrapling 安装链在文档和项目级 MCP 配置里直接写入了宿主机绝对路径，已经导致跨用户失效：旧路径指向 `nantasmac`，当前机器实际运行用户是 `nantas-agent`。同时，Scrapling-first 工作流虽然是默认路径，但执行前没有统一的 CLI preflight，也没有把“安装保障”和“是否写入 shell 环境变量”定义为标准流程。

仓库里已有可复用模式：`docs/setup/chrome-tooling.md` 与 `docs/playbooks/chrome-agent-global-install.md` 已经建立了“环境变量 + 先检查冲突 + 持久化写入前显式确认”的治理方式。本 change 复用这套模式到 Scrapling CLI。

## Goals / Non-Goals

**Goals:**

- 去掉受 git 跟踪文件里的 Scrapling 宿主机绝对路径
- 统一 Scrapling CLI 的环境变量契约为 `SCRAPLING_CLI_PATH`
- 在所有依赖 Scrapling-first 的工作流执行前增加 CLI preflight
- 当 CLI 不可用时，先确保默认隔离环境安装完成，再继续原始工作流
- 将是否写入 `/Users/nantas-agent/.zshenv` 变成显式确认动作

**Non-Goals:**

- 不重新设计 Scrapling 与 `chrome-devtools-mcp` / `chrome-cdp` 的 fallback 边界
- 不扩展到全局 Codex profile 或用户机器上的其他仓库
- 不引入新的凭据、代理或会话管理机制

## Decisions

1. **环境变量命名固定为 `SCRAPLING_CLI_PATH`**
   只定义一个可执行文件级别的变量，不再引入额外的 `SCRAPLING_ENV_DIR` 一类变量，避免配置面扩散。默认受管安装位置仍是 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`。

2. **项目级 MCP 配置通过 shell launcher 解析环境变量**
   由于 `.codex/config.toml` 和 `opencode.json` 是否原生支持变量展开不应成为前提，实现采用 `sh -lc` 这类包装命令来解析 `SCRAPLING_CLI_PATH`。这样仓库跟踪的是环境变量引用而不是绝对路径，同时不依赖 MCP 配置格式的特殊能力。

3. **preflight 放在“工作流执行前”，不是“fallback 之后”**
   Content Retrieval 和以 Scrapling 为起点的分析路径在真正调用 fetcher 前，先检查 `SCRAPLING_CLI_PATH` 指向的可执行文件是否可运行；如果不可运行，则进入安装保障流程。只有 preflight 成功后，才进入正常的 fetcher 选择逻辑。

4. **安装保障采用复用优先、重装次之**
   preflight 首先检查现有 `SCRAPLING_CLI_PATH`，其次检查默认受管路径；只有两者都不可用时，才执行 `uv venv` + `uv pip install` + `scrapling install`。这样避免每次工作流都重复安装。

5. **`.zshenv` 写入属于持久化用户环境变更，必须确认**
   工作流可以在当前进程内临时使用已解析的 Scrapling 路径，但如果要把 `export SCRAPLING_CLI_PATH=...` 写入 `/Users/nantas-agent/.zshenv`，必须先检查已有值，再征求用户确认。已有正确值则不重写；已有冲突值则明确报冲突，不静默覆盖。

## Risks / Migration

- **配置包装层风险**：改为 `sh -lc` 后，MCP 启动依赖 shell 可用。当前环境是 zsh/macOS，风险可接受；验证时需要覆盖 `codex mcp list` 和实际 session 启动。
- **历史文档残留风险**：仓库里可能还有旧的 `/Users/nantasmac/...` 示例，实施时需要全仓搜索并统一替换，否则用户仍可能照抄旧路径。
- **用户环境冲突风险**：如果用户已有 `SCRAPLING_CLI_PATH` 指向别的安装，必须把它当成冲突而不是自动纠正。迁移策略是先报告现状，再由用户决定是否替换 `.zshenv`。
- **工作流阻断风险**：增加 preflight 后，原本“先试再说”的路径会更早失败。这是有意行为，目的是避免在 MCP 启动阶段以不透明方式失败。
