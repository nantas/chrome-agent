# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `HtmlToMarkdownConverter` 增加公共 API 入口供外部调用；修复 Basement 空标签 bug

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: public-conversion-api

`HtmlToMarkdownConverter.convert()` at module level SHALL be exposed as a convenient standalone function for external callers (including `sample_converter.py`), accepting `html: str, wiki_domain: str, extraction_config: dict` and returning `str`.

#### Scenario: public-api-standalone-call

- **WHEN** external code calls `convert_html_to_markdown(html, wiki_domain="example.com", extraction_config={...})`
- **THEN** the function SHALL return a Markdown string
- **AND** the function SHALL NOT require instantiation of `HtmlToMarkdownConverter` or `ApiClient`

#### Scenario: public-api-equivalent-to-instance

- **WHEN** `convert_html_to_markdown(html, ...)` is called
- **AND** `HtmlToMarkdownConverter(wiki_domain=..., extraction_config=...).convert_body(html)` is called with same inputs
- **THEN** both SHALL return identical Markdown strings

### Requirement: infobox-rendering-delegation

`HtmlToMarkdownConverter._render_infobox_table()` SHALL delegate infobox rendering logic to the shared module `converters/infox_renderer.py` instead of containing the logic inline.

The converter SHALL remain responsible for extracting the infobox container node from the DOM and passing it to the shared module.

#### Scenario: delegation-to-shared-module

- **WHEN** `_render_infobox_table()` is called
- **THEN** it SHALL call `from .infox_renderer import render_infobox_table`
- **AND** SHALL pass the parsed node + config to the shared function
- **AND** SHALL return the result unchanged

### Requirement: sample-converter-delegation

`sample_converter.py` SHALL delegate HTML-to-Markdown conversion to `HtmlToMarkdownConverter` via the new public API during the `convert()` function path.

The `_apply_extraction()` function SHALL retain its extraction logic (cleanup_selectors, image_handling, lazyload, etc.) but SHALL call `HtmlToMarkdownConverter.convert_body()` for the final HTML→Markdown conversion step instead of `markdownify.markdownify()`.

#### Scenario: explore-path-uses-html-to-markdown-converter

- **WHEN** `sample_converter.py::convert()` is called
- **THEN** the HTML→Markdown conversion SHALL be performed by `HtmlToMarkdownConverter`
- **AND** `markdownify.markdownify()` SHALL NOT be called
- **AND** the same `extraction_config` SHALL be passed to `HtmlToMarkdownConverter`

#### Scenario: explore-path-output-consistent

- **WHEN** `sample_converter.py::convert()` processes a page
- **AND** the same page is processed by `run_phase_b()` via `HtmlRenderedAcquisitionStrategy`
- **THEN** both outputs SHALL have identical infobox table sections
- **AND** both outputs SHALL have the same content structure (links, images, headings)

### Requirement: markdownify-dependency-cleanup

If `sample_converter.py` no longer calls `markdownify.markdownify()`, the `markdownify` import and dependency SHALL be removed from `sample_converter.py` and optionally from `scripts/explore/requirements.txt`.

`BeautifulSoup` import SHALL be retained for non-conversion purposes (HTML cleanup operations in `_apply_extraction()` that occur before conversion).

#### Scenario: markdownify-removed

- **WHEN** `sample_converter.py` is inspected
- **THEN** `markdownify.markdownify` SHALL NOT be imported or called
- **AND** `markdownify` SHALL be removed from `scripts/explore/requirements.txt` if no other module requires it

> **Note:** `converters/fandom_html_to_markdown.py` is the sole remaining consumer of `markdownify` in this repository. It is a standalone Fandom-specific converter outside the explore/pipeline paths and is not in scope for this change.
