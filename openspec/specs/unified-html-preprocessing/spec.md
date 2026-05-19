# Specification Delta

## Capability 对齐（已确认）

- Capability: `unified-html-preprocessing`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: 用户确认 4 个 capability 无需调整

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: context-driven-preprocessing
The system SHALL provide `preprocess_html()` in `lib/extraction/preprocessor.py` that accepts an `html` string, a `config` dict, and a `context` parameter (`"explore"` or `"pipeline"`).

#### Scenario: explore context full preprocessing
- **WHEN** `preprocess_html(html, config, context="explore")` is called
- **THEN** the function SHALL execute, in order: (1) remove infobox container via `config.infobox.selector`, (2) strip elements matching `config.cleanup_selectors`, (3) fix lazyload images via `config.lazyload`, (4) execute cleanup operations from `config.cleanup` list, (5) remove decorative images matching `config.image_filtering.skip_patterns`, (6) select main content via `config.selectors.content`

#### Scenario: pipeline context lightweight preprocessing
- **WHEN** `preprocess_html(html, config, context="pipeline")` is called
- **THEN** the function SHALL execute lightweight cleanup only — this is a placeholder for future use; Change 2 does not modify `clean_html()` in `html_to_markdown.py`

### Requirement: config-driven-cleanup-operations
The system SHALL interpret the `config.cleanup` list to determine which cleanup operations to execute, not hardcode operation names.

#### Scenario: strip_fandom_infobox_tables
- **WHEN** `"strip_fandom_infobox_tables"` is in the cleanup list
- **THEN** tables with classes `item-table-header`, `item-table-body`, `item-table-description`, `item-table-appearance`, `infobox-table`, `portable-infobox` SHALL be removed

#### Scenario: convert_ambox_to_text
- **WHEN** `"convert_ambox_to_text"` is in the cleanup list
- **THEN** ambox tables SHALL be replaced with a paragraph containing `⚠️` prefix

#### Scenario: unwrap_image_wrappers
- **WHEN** `"unwrap_image_wrappers"` is in the cleanup list
- **THEN** `<a>` elements wrapping only a single `<img>` SHALL be unwrapped (tag removed, children kept)

#### Scenario: strip_footer
- **WHEN** `"strip_footer"` is in the cleanup list
- **THEN** elements matching `#catlinks`, `#mw-hidden-catlinks`, `.printfooter`, `.mw-footer`, `#footer` SHALL be removed

#### Scenario: strip_edit_links
- **WHEN** `"strip_edit_links"` is in the cleanup list
- **THEN** elements matching `.mw-editsection` SHALL be removed

#### Scenario: strip_skip_links
- **WHEN** `"strip_skip_links"` is in the cleanup list
- **THEN** accessibility skip-to-content navigation links SHALL be removed

#### Scenario: strip_category_links
- **WHEN** `"strip_category_links"` is in the cleanup list
- **THEN** category link containers and "Categories:" sections SHALL be removed

#### Scenario: convert_nested_images
- **WHEN** `"convert_nested_images"` is in the cleanup list
- **THEN** `<figure>` and `<picture>` wrappers SHALL be replaced with their inner `<img>` child

### Requirement: config-driven-lazyload-fix
The system SHALL fix lazyload images based on `config.lazyload` settings.

#### Scenario: lazyload enabled with placeholder and src_attr
- **WHEN** `config.lazyload.enabled` is true, `placeholder_pattern` and `real_src_attr` are set
- **THEN** images whose `src` contains the placeholder pattern SHALL have their `src` replaced with the `data-*` attribute value

### Requirement: content-selection
The system SHALL select the main content area based on `config.selectors.content`.

#### Scenario: content selector matches
- **WHEN** `config.selectors.content` matches an element in the HTML
- **THEN** only that element's HTML SHALL be returned

#### Scenario: content selector no match
- **WHEN** `config.selectors.content` does not match
- **THEN** the full body content SHALL be returned as fallback

### Requirement: output-html-string
The system SHALL return a cleaned HTML string (not a parsed object).

#### Scenario: successful preprocessing
- **WHEN** preprocessing completes
- **THEN** the return value SHALL be a raw HTML string ready for `convert_html_to_markdown()`
