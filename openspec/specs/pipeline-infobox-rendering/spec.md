# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-infobox-rendering`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: modified
- 用户确认摘要: 用户确认 4 个 capability 无需调整

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: render-infobox-table-uses-shared-lib
`HtmlToMarkdownConverter._render_infobox_table()` SHALL import and call `lib.extraction.infobox.extract_infobox()` instead of `infox_renderer.render_infobox_table()`.

#### Scenario: infobox rendering during conversion
- **WHEN** `_render_infobox_table(node)` is called during HTML-to-Markdown conversion
- **THEN** it SHALL call `extract_infobox()` from `lib.extraction.infobox` with the same parameters: node, config, wiki_domain, field/label/value selectors, handlers, and callbacks (`render_inline_children_fn`, `apply_handler_fn`)

#### Scenario: backward compatible callback signature
- **WHEN** `extract_infobox()` is called with `render_inline_children_fn=self._render_inline_children` and `apply_handler_fn=self._apply_infobox_handler`
- **THEN** the shared module SHALL invoke these callbacks for label rendering and handler application, preserving identical output to the current `infox_renderer` behavior

### Requirement: handler-implementation-stays-in-converter
`_apply_infobox_handler()` and all handler methods (`extract_cur_id`, `count_images`, `dedup_pools`, `simplify_collection`, `extract_tags`) SHALL remain in `html_to_markdown.py` and be passed to `extract_infobox()` via callback.

#### Scenario: handler methods unchanged
- **WHEN** `extract_infobox()` calls `apply_handler_fn(handler_name, raw_html)`
- **THEN** `html_to_markdown.py._apply_infobox_handler()` SHALL execute and return the result as before

## REMOVED Requirements

### Requirement: infox-renderer-module
**Reason**: `infox_renderer.py` is deleted; its functionality is absorbed by `lib.extraction.infobox.extract_infobox()`
**Migration**: The single call site in `html_to_markdown.py:457` (`from .infox_renderer import render_infobox_table`) is replaced with `from scripts.lib.extraction.infobox import extract_infobox`
