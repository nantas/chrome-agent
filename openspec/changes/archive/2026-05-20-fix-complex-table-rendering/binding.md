# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/pipeline-converters/spec.md`
- `project_page_ref`: `scripts/lib/extraction/converter.py` (HtmlToMarkdownConverter)
- `additional_context_refs`:
  - `openspec/specs/strategy/strategy-schema.md` (strategy `extraction` block schema)
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md` (pipeline convert phase)
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` (BOI wiki strategy — config target)
  - `outputs/test-100-fixed/characters/index.md` (样本异常输出 — 问题证据)

## Source of Truth

- 行为规范真源：`specs/pipeline-converters/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `scripts/lib/extraction/converter.py` — 新增 `_build_table_grid()`、`_render_grid_as_table()`、`_transpose_grid()`，重构 `_render_table()`
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 新增 `extraction.table_options` 配置块
- `writeback_owner`: chrome-agent pipeline converter 维护者
- `writeback_timing`: 实现完成后立即回写，验证通过后确认

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- converter 中的 `_is_simple_markdown_table()` 方法将被删除，由新网格解析逻辑替代；此变更需在 converter.py 回写中体现
- strategy.md 的 `extraction` 块新增字段需符合 `strategy-schema.md` 中定义的 extraction schema 约束

## 待确认项

- [x] 已确认标准页引用 (`pipeline-converters/spec.md`)
- [x] 已确认项目页引用 (`converter.py`, `strategy.md`)
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略 (回退策略：若网格解析失败，保留空 grid 不输出，不 fallback 到旧摊平逻辑)
