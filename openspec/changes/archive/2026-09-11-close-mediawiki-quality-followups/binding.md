# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/GOVERNANCE.md`（本仓治理入口；上游治理 SSOT 为 `repo://orbitos`）。
- `project_page_ref`: `docs/architecture/05-converter-architecture.md`、`docs/architecture/02-pipeline-flow.md`、`docs/architecture/03-strategy-schema.md`。
- `additional_context_refs`: `AGENTS.md` §0.5（C9 测试义务、C7 策略注册）、`docs/architecture/08-tech-stack.md`；已归档 `openspec/changes/archive/2026-09-11-fix-mediawiki-extraction-integrity/` 与 `openspec/changes/archive/2026-09-11-restore-mediawiki-discovery-and-strategy-contracts/`。
- 诊断来源：`growagarden-handoff/HANDOFF-output-quality-fixes.md`（第三份 handoff）及本会话对 HEAD `c9d3b76` 工作区的离线复核。临时目录不作为实施必须存在的依赖；诊断结论已固化在 proposal/design。

## Source of Truth

- 行为规范真源：本 change 的 `specs/` delta；归档后合并入 `openspec/specs/`。
- 执行真源：当前 chrome-agent 仓库代码和配置。
- 项目页面仅承担上下文输入、治理展示和结果回写，不替代 spec delta。

## 回写目标

- `writeback_targets`: `docs/architecture/05-converter-architecture.md`（infobox 单元格转义与标题判定）、`docs/architecture/02-pipeline-flow.md`（L6 图片校验的 URL 解析规则，如涉及）。
- `writeback_owner`: 实施本 change 的 agent。
- `writeback_timing`: 实现验证后、归档前。

## 同步约束

- 页面与 spec 冲突时以 `specs/` 为准；回写结论、状态、摘要和链接，不整份复制 design/tasks。
- 本 change 不修改任何 `.mjs` 文件，C10 无同步义务。
- 工作区既有未提交补丁（`infobox.py`、`convert.py`、策略四件套）是本 change 的实施对象，不覆盖 `mobalytics.gg/` 以外的无关改动。
- my-wiki 侧归档与 ingest 已在上一任务完成，不随本 change 重做。

## 待确认项

- 无阻塞规划的未确认项。`mobalytics.gg/` 收编已获用户同意纳入本 change（"剩余问题和未提交的修改都整理到一个 change 里"）。
- L6 误报修复会改变其他 Fandom 域校验输出（减少 unavailable 条目），已在 proposal 中声明为预期行为。
