# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `orbitos` (OpenSpec Standard v0.3)
- `project_page_ref`:
  - `openspec/specs/pipeline-converters/spec.md` (HtmlToMarkdownConverter 行为规范)
  - `openspec/specs/pipeline/pipeline-conversion.md` (pipeline convert phase)
- `additional_context_refs`:
  - `scripts/lib/extraction/converter.py` (`_render_infobox_table`, `_to_markdown_link`, `_render_inline_children`)
  - `scripts/lib/extraction/infobox.py` (`extract_infobox`, `_extract_selectolax`)
  - `openspec/changes/link-fallback-redirect-skip/` (前序 change，解决 fallback 和 redirect)

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/pipeline-converters/spec.md` — 新增 infobox-link-source-dir requirement
- `writeback_owner`: change author
- `writeback_timing`: verification 通过后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略 — 纯参数透传，无异常处理变更
