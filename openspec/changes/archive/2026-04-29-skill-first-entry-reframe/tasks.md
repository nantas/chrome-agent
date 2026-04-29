# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `global-workflow-skill`、`agents-governance`、`global-capability-cli`、`install-chain`、`master-plan` 五个 capability spec 的实现范围与边界已覆盖本次入口重构
- [x] 1.2 确认迁移前提：现有 `skills/chrome-agent/SKILL.md`、`scripts/chrome-agent-runtime.mjs`、`scripts/chrome-agent-cli.mjs`、README 与安装 playbook 的现状差异

## 2. Skill-first 入口实现

- [x] 2.1 重写 `skills/chrome-agent/SKILL.md`，完成标准是 skill 明确以 `chrome-agent doctor --format json` 做 preflight，并按意图路由到 `fetch` / `explore` / `crawl`
- [x] 2.2 清除 skill 中对 `repo-agent`、`codex-agent` 或其他 prompt-forwarding runtime 的正式依赖描述，完成标准是 skill 文档只保留 CLI-backed 运行模型
- [x] 2.3 定义并验证 skill 的结果包装约束，完成标准是 skill 以 CLI JSON 为真源输出稳定的 `result`、`summary`、`artifacts` 和 remediation

## 3. CLI backend 契约调整

- [x] 3.1 更新 `scripts/chrome-agent-cli.mjs` 与相关帮助文本，完成标准是 CLI 将 `fetch` / `explore` / `crawl` 描述为低层显式 workflow backend
- [x] 3.2 扩展 `explore` 的 backend 语义，完成标准是其结果能覆盖 Platform/Page Analysis 所需的分析 artifact 与 workflow 标识，而不只是 strategy gap 探测
- [x] 3.3 扩展 CLI JSON contract，完成标准是 `fetch` / `explore` / `crawl` 至少返回 `workflow` 与 `engine_path` 字段

## 4. 治理与安装文档收敛

- [x] 4.1 更新 `AGENTS.md`、README 和相关 playbook/setup 文档，完成标准是正式入口叙事统一为 skill-first / CLI-backed
- [x] 4.2 更新安装与迁移说明，完成标准是文档明确“CLI 是 skill 的后端前提，skill 是推荐 agent 入口”，并删除旧 dispatcher runtime 的正式路径
- [x] 4.3 新增或更新一条 decision record，完成标准是明确记录为何 supersede Phase 5 的“retire skill”假设

## 5. 收敛与验证准备

- [x] 5.1 验证 skill preflight 路径，完成标准是 backend 不健康时 skill 停止执行并返回 doctor remediation
- [x] 5.2 验证三类意图路由，完成标准是内容获取 -> `fetch`，深度分析 -> `explore`，有界批量遍历 -> `crawl` 或 explore-first remediation
- [x] 5.3 验证 CLI 与 skill 的结果契约对齐，完成标准是 skill 的最终输出可以完全由 CLI JSON 结果解释

## 6. 验证与回写收敛

- [x] 6.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 6.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 6.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
