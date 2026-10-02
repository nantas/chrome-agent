# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/07-explore-workflow.md`, `docs/architecture/08-tech-stack.md`, `docs/playbooks/chrome-agent-global-install.md`
- `additional_context_refs`: `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/GOVERNANCE.md`, `docs/adr/0002-app-engine-venv-boundary.md`, `docs/adr/0003-lazy-trigger-venv-lifecycle.md`
- 诊断证据：`outputs/handoffs/20261002T101832-explore-undefined/handoff.md`（本地忽略产物；问题摘要已记录于 proposal）。

## Source of Truth

- 本次行为规范真源：`specs/explore-workflow/spec.md` 与 `specs/governance/spec.md`。
- 已冻结行为规范：`openspec/specs/explore-workflow/spec.md`、`openspec/specs/explore/explore-deep-discovery.md`、`openspec/specs/governance/handoff.md`。
- 项目页面只承担上下文输入、治理展示与结果回写，不替代 spec delta。

## 回写目标

- `writeback_targets`:
  - `docs/architecture/07-explore-workflow.md`：入口启动约定与故障诊断结论。
  - `docs/architecture/08-tech-stack.md`：子进程入口测试与导入路径约定。
  - `openspec/specs/explore/explore-deep-discovery.md`：归档时替换 deep-discovery 完整块，保留其它要求。
  - `openspec/specs/governance/handoff.md`：归档时合并 handoff-storage-path 完整更新块，保持域内其它要求。
- `writeback_owner`: 本 change 执行者。
- `writeback_timing`: 实现完成且 verification 记录验证证据后，归档前完成。

## 同步约束

- 页面与 specs 冲突时，以 specs 为准；回写只同步结论、摘要、状态与证据链接。
- 修改 `scripts/chrome-agent-cli.mjs` 后执行 C10 / 全局安装 Case 6：同步 runtime 和 skill，并刷新 installed-hash 为当前 HEAD；CLI 自身仍由 launcher 从仓库加载，不复制为全局 runtime。
- 本次不改 shell 配置、策略注册或引擎版本。
- 回写前读取 `spec_standard_ref`；本提案阶段使用已读取的本地 schema 与治理文档。

## 待确认项

- 2026-10-02 用户回复“能力确认”，确认能力边界：`explore-workflow` 与 `governance`，均为已有能力修改。
- 2026-10-02 已通过本地 repo registry 解析 repo://orbitos 并读取 spec_standard_ref 原文；本 change 的回写目标为本仓架构文档与归档规范，不包含外部项目页。
