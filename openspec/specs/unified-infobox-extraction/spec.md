# Specification Delta

## Capability 对齐（已确认）

- Capability: `unified-infobox-extraction`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: 用户确认 4 个 capability 无需调整

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: dual-parser-infobox-extraction
The system SHALL provide `extract_infobox()` in `lib/extraction/infobox.py` that accepts both raw HTML strings (BeautifulSoup parsing) and pre-parsed selectolax Node objects.

#### Scenario: BS4 mode from explore path
- **WHEN** `extract_infobox()` is called with a raw HTML string and `parser="auto"` or `parser="bs4"`
- **THEN** the function SHALL parse the HTML with BeautifulSoup, locate the infobox container via `config.infobox.selector`, and return a Markdown table string

#### Scenario: Selectolax mode from pipeline path
- **WHEN** `extract_infobox()` is called with a selectolax Node object and `parser="auto"`
- **THEN** the function SHALL use the node directly (no re-parsing), locate the infobox container via the same selectors, and return a Markdown table string

### Requirement: config-driven-selectors
The system SHALL read all infobox selectors from the `extraction.infobox` config dict: `selector`, `field_selector`, `label_selector`, `value_selector`.

#### Scenario: default selector values
- **WHEN** `field_selector` is not specified in config
- **THEN** the default SHALL be `"div.pi-data"` (wiki.gg standard), NOT `"tr"` (legacy sample_converter default)

### Requirement: dual-handler-lookup
The system SHALL support two handler lookup strategies, tried in order: (1) label text match, (2) `data-source` attribute match with `ds(key)` alias.

#### Scenario: handler found by label text
- **WHEN** `field_handlers` contains a key matching the label text of a field
- **THEN** the handler SHALL be applied to that field's value

#### Scenario: handler found by data-source alias
- **WHEN** `field_handlers` does not contain the label text, but the field has a `data-source` attribute and `field_handlers` contains `ds(key)` format
- **THEN** the handler SHALL be applied via the alias match

### Requirement: nav-strip-config-driven
The system SHALL support config-driven nav element stripping via `nav_strip_selectors` in the infobox config.

#### Scenario: nav strip selectors configured
- **WHEN** `config.infobox.nav_strip_selectors` contains selectors like `[".infobox-nav-prev", ".infobox-nav-next"]`
- **THEN** matching elements SHALL be removed from value cells before rendering

#### Scenario: nav strip selectors not configured
- **WHEN** `nav_strip_selectors` is absent from config
- **THEN** no nav stripping SHALL occur (no hardcoded fallback)

### Requirement: callback-based-handler-execution
The system SHALL accept optional callback functions `render_inline_children_fn` and `apply_handler_fn` for rendering inline content and applying named handlers.

#### Scenario: callbacks provided (pipeline path)
- **WHEN** both callbacks are provided
- **THEN** the function SHALL use them for label rendering and handler application, matching current `infox_renderer.render_infobox_table()` behavior

#### Scenario: no callbacks (explore path)
- **WHEN** callbacks are not provided
- **THEN** the function SHALL use built-in fallback text extraction (plain text from nodes)

### Requirement: empty-label-skip
The system SHALL skip infobox fields with empty labels.

#### Scenario: label node contains only images
- **WHEN** a field's label node renders to an empty string after text extraction
- **THEN** the field SHALL be excluded from the output table

### Requirement: markdown-table-output
The system SHALL output infobox as a Markdown table prefixed with `## Infobox`.

#### Scenario: fields found
- **WHEN** one or more fields are successfully extracted
- **THEN** output SHALL be `## Infobox\n\n| Field | Value |\n| --- | --- |\n| **label** | value |` format

#### Scenario: no fields found
- **WHEN** no fields are extracted (empty labels, no matching selectors)
- **THEN** output SHALL be an empty string
