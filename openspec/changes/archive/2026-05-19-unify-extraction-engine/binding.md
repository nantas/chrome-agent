# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: 无现有 spec 直接覆盖本 change（属于新增能力 `lib/extraction/`）
- `project_page_ref`: `docs/plans/2026-05-19-structure-refactor-and-docs.md` (Change 2 章节)
- `additional_context_refs`:
  - `openspec/changes/fix-pipeline-quality-gaps/` (前置 change)
  - `scripts/explore/sample_converter.py` (被重构的 explore 路径)
  - `scripts/mediawiki-api-extract/converters/html_to_markdown.py` (pipeline 路径)
  - `scripts/mediawiki-api-extract/converters/infox_renderer.py` (将被删除)

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `docs/plans/2026-05-19-structure-refactor-and-docs.md` (Change 2 状态更新)
- `writeback_owner`: chrome-agent repo agent
- `writeback_timing`: Change 完成后（verification 通过）

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本 change 涉及 Python 3.9 兼容性约束（`from __future__ import annotations` 可用）
- 本 change 不改变 `html_to_markdown.py` 文件位置（推迟到 Change 3）
- 本 change 不改变 `clean_html()` 方法（保持 pipeline 路径独立）

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
