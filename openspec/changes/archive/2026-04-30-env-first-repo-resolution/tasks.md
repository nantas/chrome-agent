# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `global-workflow-skill`、`global-capability-cli`、`install-chain`、`master-plan` 四个 capability spec 已完整覆盖 env-first 默认解析契约
- [x] 1.2 确认迁移前提：现有 `skills/chrome-agent/SKILL.md`、`scripts/chrome-agent-runtime.mjs`、README、安装 playbook 与项目页中仍保留的 repo-registry-first 描述

## 2. 核心实现任务

- [x] 2.1 修改 `scripts/chrome-agent-runtime.mjs` 的默认仓库解析顺序，完成标准是默认路径变为 `--repo` override → `CHROME_AGENT_REPO` → failure，且 repo-registry 仅在显式 `repo://...` override 时使用
- [x] 2.2 调整 runtime failure / remediation 文案与 machine-readable 语义，完成标准是 env 缺失或无效时明确要求“设置 `CHROME_AGENT_REPO` 或显式传 `--repo`”
- [x] 2.3 调整 CLI 结果字段中的 resolution naming，完成标准是默认 env 路径不再使用 `env_fallback` 一类旧语义
- [x] 2.4 更新 `skills/chrome-agent/SKILL.md`，完成标准是 skill 文档明确其 doctor-first preflight 依赖的是 env-first backend 解析契约
- [x] 2.5 更新 README、安装 playbook 与相关项目叙事，完成标准是默认运行前提统一改为 `CHROME_AGENT_REPO`，repo-registry 只保留给显式 repo-ref 路径

## 3. 收敛与验证准备

- [x] 3.1 验证 env-first 默认成功路径，完成标准是设置有效 `CHROME_AGENT_REPO` 后，`doctor` / `fetch` / `explore` / `crawl` 在未传 `--repo` 时均可成功解析目标仓
- [x] 3.2 验证默认失败路径与显式 override 路径，完成标准是 env 缺失或无效时默认失败，但 `--repo /abs/path` 与 `--repo repo://chrome-agent` 仍可显式工作
- [x] 3.3 验证 CLI 与 skill 的结果契约对齐，完成标准是 skill 暴露的 `repo_ref`、`summary`、`next_action` 可完全由新的 CLI JSON 结果解释

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
