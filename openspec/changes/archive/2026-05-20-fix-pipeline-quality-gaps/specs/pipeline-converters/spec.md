# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `html_to_markdown.py` 需修复 infobox 表格渲染、读取 `extraction.infox.*` 配置、增加空值防御

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: infobox-table-assembly

`HtmlToMarkdownConverter._render_block()` SHALL assemble all infobox fields from a `<aside class="portable-infobox">` (or configured selector) into a single valid Markdown table with a separator row.

The converter SHALL read infobox selectors from `extraction.infox` configuration (falling back to hardcoded defaults only when config is absent).

#### Scenario: portable-infobox-to-markdown-table

- **WHEN** the HTML contains `<aside class="portable-infobox">` with multiple `<div data-source="...">` children
- **THEN** the converter SHALL detect the infobox container using the configured `infobox.selector`
- **AND** SHALL collect all child fields matching `infobox.field_selector`
- **AND** SHALL render the output as:
  ```
  ## Infobox

  | Field | Value |
  | --- | --- |
  | **Pickup quote** | Pickup quote "Tears up" |
  | **Item icon** | ![](https://...) |
  | **Collectible ID** | 1 |
  ```
- **AND** the table SHALL include the `|---|---|` separator row after the header

#### Scenario: infobox-field-label-extraction

- **WHEN** processing an infobox field
- **THEN** the converter SHALL extract the label using `infobox.label_selector`
- **AND** the converter SHALL extract the value using `infobox.value_selector`
- **AND** the label SHALL be rendered in bold: `**label_text**`

#### Scenario: infobox-with-configured-selectors

- **WHEN** `extraction.infox` defines custom `selector`, `field_selector`, `label_selector`, `value_selector`
- **THEN** the converter SHALL use these configured selectors
- **AND** SHALL NOT use hardcoded CSS class names

#### Scenario: infobox-without-config

- **WHEN** `extraction.infox` is not present or `infobox.enabled` is not `true`
- **THEN** the converter SHALL fall back to its existing inline rendering behavior
- **AND** SHALL NOT attempt table assembly

#### Scenario: infobox-field-handler-application

- **WHEN** an infobox field has a registered handler in `infobox_field_handlers`
- **THEN** the converter SHALL apply the handler to the field value
- **AND** the handler SHALL modify the value cell content (e.g., `extract_cur_id` strips nav elements)
- **AND** the processed value SHALL appear in the assembled table

### Requirement: nil-safety-in-conversion

`HtmlToMarkdownConverter._render_block()` and `_render_inline_children()` SHALL handle `None` return values from selectolax node operations gracefully.

When a node's text content or attribute is `None`, the converter SHALL fall back to an empty string or skip the node, rather than raising `AttributeError: 'NoneType' object has no attribute 'replace'`.

#### Scenario: none-text-handling

- **WHEN** `node.text(deep=True, separator=" ", strip=False)` returns `None`
- **THEN** the converter SHALL treat it as an empty string `""`
- **AND** SHALL NOT call `.replace()` or `.strip()` on the `None` value

#### Scenario: homepage-with-gallery-layout

- **WHEN** the homepage HTML contains gallery sections with non-standard template structures
- **AND** some nodes in the DOM tree have no text content
- **THEN** the converter SHALL process the page without crashing
- **AND** SHALL produce whatever Markdown content it can extract (even if partial)

#### Scenario: none-attribute-handling

- **WHEN** `node.attributes.get("href")` returns `None`
- **THEN** `_normalize_href()` SHALL return `None` (existing behavior is correct)
- **AND** callers SHALL handle `None` href by rendering text-only (existing behavior is correct)
