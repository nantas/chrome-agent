# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `pipeline-converters`
  - `mediawiki-api-extraction-pipeline`
  - `homepage-driven-discovery`
- `project_page_ref`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` (结构优化重构总体规划)
  - `openspec/changes/fix-pipeline-quality-gaps/` (前置 change，本 change 依赖其能力定义)
- `additional_context_refs`:
  - `openspec/changes/fix-pipeline-quality-gaps/specs/pipeline-converters/`
  - `openspec/changes/fix-pipeline-quality-gaps/specs/mediawiki-api-extraction-pipeline/`
  - `openspec/changes/fix-pipeline-quality-gaps/specs/homepage-driven-discovery/`

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` — 更新 Change 3/4 完成状态
  - `openspec/changes/fix-pipeline-quality-gaps/` — 更新关联绑定中的能力引用
- `writeback_owner`: chrome-agent maintainer
- `writeback_timing`: 本 change 验证完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（三个能力域已在 `fix-pipeline-quality-gaps` change 中定义，delta spec 位于 change 目录）
- [x] 已确认项目页引用（`docs/plans/2026-05-19-structure-refactor-and-docs.md` 第 2.5 节）
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
