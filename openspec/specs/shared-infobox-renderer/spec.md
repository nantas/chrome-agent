# Specification Delta

## Capability 对齐（已确认）

- Capability: `shared-infobox-renderer`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: explore 阶段已确认将 infobox 渲染逻辑提取为两个 converter 共享的独立模块

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: shared-infobox-module

The system SHALL provide a shared module `scripts/mediawiki-api-extract/converters/infox_renderer.py` containing the portable infobox→Markdown table logic, importable by both `HtmlToMarkdownConverter` and `sample_converter.py`.

The module SHALL expose a single function with signature:
```python
def render_infobox_table(infobox_html_node, extraction_config: dict, wiki_domain: str) -> str
```

Where `infobox_html_node` is a parsed HTML element node (compatible with either selectolax or BeautifulSoup APIs depending on caller context).

#### Scenario: shared-module-exists

- **WHEN** the repository is inspected
- **THEN** a file `scripts/mediawiki-api-extract/converters/infox_renderer.py` SHALL exist
- **AND** it SHALL be importable from both `scripts/mediawiki-api-extract/converters/html_to_markdown.py` and `scripts/explore/sample_converter.py`
- **AND** it SHALL NOT import from either converter file (no circular dependency)

#### Scenario: infobox-table-output-identical

- **WHEN** the same `<aside class="portable-infobox">` HTML node is passed to `render_infobox_table()` through both callers
- **THEN** the output Markdown table SHALL be identical regardless of which caller invoked it
- **AND** the output SHALL include `## Infobox\n\n| Field | Value |\n| --- | --- |\n...` format

#### Scenario: empty-label-handling

- **WHEN** an infobox field's label node (`<h3>`) has no text content (e.g., contains only images or empty)
- **THEN** the renderer SHALL skip that field (produce no row for it)
- **AND** SHALL NOT render `| **<empty>** | value |` or `| **** | value |`

### Requirement: basename-empty-label-fix

The `****` empty label bug (observed on Basement page, Stage's starting room field) SHALL be fixed in the shared module.

#### Scenario: empty-label-not-rendered

- **WHEN** an infobox field's `<h3 class="pi-data-label">` contains only an `<img>` tag with no text
- **THEN** the field SHALL be skipped
- **AND** the rendered table SHALL NOT contain a row for that field

#### Scenario: labeled-field-with-image

- **WHEN** an infobox field's `<h3 class="pi-data-label">` contains text AND images
- **THEN** the label SHALL be the text content only (images in the label node SHALL be ignored)
- **AND** the field SHALL be rendered as a normal row
