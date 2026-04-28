# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `scrapling-cli-environment` spec 覆盖：`SCRAPLING_CLI_PATH` 命名、默认受管安装路径 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`、工作流前安装保障、以及 `/Users/nantas-agent/.zshenv` 持久化确认边界
- [x] 1.2 确认 `agents-governance` MODIFIED spec 覆盖：Content Retrieval 和以 Scrapling 为起点的分析路径在执行前都必须经过 Scrapling CLI preflight，且 preflight 失败时不得伪装成已进入 Scrapling-first 工作流
- [x] 1.3 确认 `scrapling-first-browser-workflow` MODIFIED spec 覆盖：setup 文档、项目级 MCP 配置和历史工作流说明都改为环境变量表达，不再要求在受跟踪文件中手填绝对路径

## 2. 核心实现任务

- [x] 2.1 全仓搜索并列出所有受 git 跟踪文件中的 Scrapling 宿主机绝对路径引用，至少覆盖 `.codex/config.toml`、`opencode.json`、`docs/setup/scrapling-first-workflow.md`，并确认是否还有其他遗留路径需要迁移
- [x] 2.2 将项目级 Codex MCP 配置改为通过 shell launcher 解析 `SCRAPLING_CLI_PATH` 启动 `scrapling mcp`，完成标准是 `.codex/config.toml` 不再包含用户专属绝对路径且在变量缺失时返回清晰失败
- [x] 2.3 将项目级 Opencode MCP 配置改为通过 shell launcher 解析 `SCRAPLING_CLI_PATH` 启动 `scrapling mcp`，完成标准是 `opencode.json` 不再包含用户专属绝对路径且与 Codex 行为一致
- [x] 2.4 更新 `docs/setup/scrapling-first-workflow.md`，把安装与 MCP 配置说明改为 `SCRAPLING_CLI_PATH` 契约，明确默认受管安装路径、`uv` 安装命令、以及不再编辑受跟踪文件来适配用户名
- [x] 2.5 在仓库工作流入口文档中加入 Scrapling preflight 规则，至少覆盖 `AGENTS.md` 和必要的 playbook/setup 文档；完成标准是文档明确写出“先检查 CLI，可用后再选 fetcher，不可用则先安装保障”
- [x] 2.6 实现或补充一个可复用的 Scrapling preflight/install 流程，检查顺序为：当前 `SCRAPLING_CLI_PATH` → 默认受管路径 → 缺失时执行 `uv venv`、`uv pip install`、`scrapling install`；完成标准是流程可区分“已可用 / 已修复 / 修复失败”三种结果
- [x] 2.7 在 preflight 流程中加入 `.zshenv` 确认逻辑：仅当 CLI 已可用但 `SCRAPLING_CLI_PATH` 未持久化或存在冲突时，询问用户是否写入 `/Users/nantas-agent/.zshenv`；完成标准是“已有正确值不重写、冲突值不静默覆盖、用户拒绝时不写入”
- [x] 2.8 更新 `README.md` 和相关 setup 入口文档，确保 Quick Start 与仓库环境说明不再暗示 `uv run scrapling` 是唯一前提，而是引用受管安装与 `SCRAPLING_CLI_PATH` 契约

## 3. 收敛与验证准备

- [x] 3.1 验证仓库受 git 跟踪文件中不再存在 `/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling` 或其他用户专属 Scrapling 绝对路径
- [x] 3.2 验证 `SCRAPLING_CLI_PATH` 缺失场景：preflight 能识别未配置状态并进入安装保障，而不是直接在 MCP 启动时报 `os error 2`
- [x] 3.3 验证 `SCRAPLING_CLI_PATH` 已正确配置场景：Scrapling CLI 检查通过，且不会触发重复安装或重复写入 `.zshenv`
- [x] 3.4 验证冲突场景：当 `/Users/nantas-agent/.zshenv` 已有不同的 `SCRAPLING_CLI_PATH` 值时，流程会报告冲突并要求显式确认
- [x] 3.5 运行 smoke checks，至少覆盖：`scrapling --help`、一个 `extract get` 场景、以及 `codex -C /Users/nantas-agent/projects/chrome-agent mcp list` 对 Scrapling 注册项的检查

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
