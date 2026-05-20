# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: 无 — 本 change 为纯文档改进，不涉及行为规范变更。文档本身受 AGENTS.md §9 (Reference Index) 治理。
- `project_page_ref`:
  - `docs/architecture/03-strategy-schema.md` (主要改进目标：增加结构图与流程图)
  - `docs/architecture/04-cli-reference.md` (次要改进目标：增加命令路由决策树)
  - `docs/architecture/08-tech-stack.md` (次要改进目标：增加组件依赖关系图)
  - `docs/architecture/02-pipeline-flow.md` (次要改进目标：更新 Phase 命名)
  - `docs/architecture/05-converter-architecture.md` (次要改进目标：更新文件路径引用)
  - `AGENTS.md` (治理文档，§9 定义 docs/architecture/ 用途)
- `additional_context_refs`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` (文档结构规划，§2.2 Layer 1)

## Source of Truth

- 行为规范真源：不适用（纯文档改进，无 spec delta）
- 项目页面角色：上下文输入 / 治理展示 / 人类可读真源
- 非真源说明：`docs/architecture/` 是架构理解的权威入口，但以实际代码为准（本文档约定在 `08-tech-stack.md` 中已声明）

## 回写目标

- `writeback_targets`:
  - `docs/architecture/03-strategy-schema.md` — 增加结构图、字段层级树、content_profile 策略路由图
  - `docs/architecture/04-cli-reference.md` — 增加命令路由决策树、管线阶段流程图
  - `docs/architecture/08-tech-stack.md` — 增加组件依赖关系图、安装脚本链流程图
  - `docs/architecture/02-pipeline-flow.md` — 更新 Phase 0/A/C 命名为 homepage/allpages/assembly
  - `docs/architecture/05-converter-architecture.md` — 更新 `html_to_markdown.py` 路径为 `scripts/lib/extraction/converter.py`
- `writeback_owner`: chrome-agent maintainer
- `writeback_timing`: 本 change 执行结束时

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准（不适用：本 change 无 spec delta）
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 文档更新后，AGENTS.md §9 中引用的文档路径不变

## 待确认项

- [x] 已确认标准页引用（无 spec delta，受 AGENTS.md §9 治理）
- [x] 已确认项目页引用（3 个主要改进目标 + 2 个次要改进目标）
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
