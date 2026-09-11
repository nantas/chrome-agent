# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/GOVERNANCE.md`（本仓治理入口；上游治理 SSOT 为 `repo://orbitos`）。
- `project_page_ref`: `docs/architecture/00-target-architecture.md`、`docs/architecture/02-pipeline-flow.md`、`docs/architecture/05-converter-architecture.md`。
- `additional_context_refs`: `AGENTS.md`、`CONTEXT.md`、`CONTEXT-MAP.md`、`docs/architecture/08-tech-stack.md`、`docs/architecture/04-cli-reference.md`、`docs/playbooks/chrome-agent-global-install.md`；已归档 `openspec/changes/archive/2026-09-11-restore-mediawiki-discovery-and-strategy-contracts/`；进行中 `openspec/changes/obsidian-safe-filenames/tasks.md`。
- 诊断来源：用户提供的 `growagarden-handoff/HANDOFF.md` 与 `HANDOFF-infobox-cv4.md`，以及本会话对 HEAD `d10858d` 和工作区的离线核查。临时目录不作为实施必须存在的依赖；诊断摘要固化在 proposal/design。

## Source of Truth

- 行为规范真源：本 change 的 `specs/` delta；归档后合并入 `openspec/specs/`。
- 执行真源：当前 chrome-agent 仓库代码和配置。
- 项目页面仅承担上下文输入、治理展示和结果回写，不替代 spec delta。

## 回写目标

- `writeback_targets`: `docs/architecture/00-target-architecture.md`（共享入口）、`docs/architecture/02-pipeline-flow.md`（缓存准入和恢复）、`docs/architecture/05-converter-architecture.md`（完整转换顺序）、`docs/architecture/04-cli-reference.md`（超时参数）、`CONTEXT.md` / `CONTEXT-MAP.md`（缓存准入与模块边界）。恢复操作说明写入 `docs/playbooks/mediawiki-extraction-recovery.md`。
- `writeback_owner`: 实施本 change 的 agent。
- `writeback_timing`: 实现验证后、归档前；本轮只生成规划 artifacts。

## 同步约束

- 页面与 spec 冲突时以 `specs/` 为准；回写结论、状态、摘要和链接，不整份复制 design/tasks。
- 修改 CLI 后按 C10 同步 runtime/skill 全局副本并刷新 installed-hash；CLI 文件本身不是全局复制目标。
- 新增能力实现文件时同步 capability registry；归档前通过 `doctor --check capabilities`。
- 不修改其他仓库或外部页面；后续跨仓引用使用 `repo://<repo_id>` 格式。
- 已有未提交补丁先保留并核对差异，不覆盖 mobalytics 等无关工作。缓存命名与 `obsidian-safe-filenames` 的输出命名治理分别维护。

## 待确认项

- 无阻塞规划的未确认项。用户已授权按上一轮建议创建 change；能力 ID 按现有规范归属映射。
- 实际全站重新抓取及 my-wiki ingest 属于恢复任务，不随本 change 的创建或实施自动执行。
