# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/` (现有提取能力规范)
- `project_page_ref`:
  - `docs/architecture/02-pipeline-flow.md` (管线五阶段流程)
  - `docs/architecture/05-converter-architecture.md` (两阶段转换模型)
  - `docs/architecture/03-strategy-schema.md` (策略 frontmatter 字段)
- `additional_context_refs`:
  - `scripts/lib/extraction/` (共享提取引擎代码)
  - `scripts/pipeline/pipeline/converter.py` (转换器实现)
  - `outputs/test-100-extraction-v3/modes/index.md` (问题复现场)

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: 无（本次为纯代码行为修复，不涉及架构文档变更）
- `writeback_owner`: 无
- `writeback_timing`: 无

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本次变更范围限定在提取引擎的 Category 页面处理逻辑，不改变管线整体架构

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（无需回写）
- [x] 已确认异常处理与冲突策略（Category 页面作为索引生成，不改变现有内容页处理）
