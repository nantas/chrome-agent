# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: converters-as-independent-package
`HtmlToMarkdownConverter`、`convert_wikitext_to_markdown`、`extract_card_stats`、`split_card_list_pages` SHALL 位于 `scripts/mediawiki_api_extract/converters/` 子包中，可被外部代码直接导入，无需启动管线或导入 `ApiClient`。

#### Scenario: import-html-converter-standalone
- **WHEN** 外部脚本执行 `from scripts.mediawiki_api_extract.converters import HtmlToMarkdownConverter`
- **THEN** 导入 SHALL 成功，无需安装或配置 `ApiClient`

#### Scenario: import-wikitext-converter-standalone
- **WHEN** 外部脚本执行 `from scripts.mediawiki_api_extract.converters import convert_wikitext_to_markdown`
- **THEN** 导入 SHALL 成功

### Requirement: backward-compatible-reexports
`strategies/__init__.py` SHALL 重新导出所有策略类和转换器，使 `from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter` 等原有导入路径继续可用。

#### Scenario: legacy-import-path
- **WHEN** 既有代码执行 `from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter`
- **THEN** 导入 SHALL 成功，返回与 converters 子包中相同的类

### Requirement: no-behavior-change
拆分后所有既有管线的输出 SHALL 与拆分前完全一致（相同输入产生相同 .md 文件）。

#### Scenario: full-pipeline-output-unchanged
- **WHEN** 对相同站点策略运行全量管线（Phase A→B→C）
- **THEN** 输出 .md 文件内容 SHALL 与拆分前逐字节一致

### Requirement: domain-parameterization

`HtmlToMarkdownConverter.__init__` SHALL accept `wiki_domain` as a required parameter and SHALL NOT default to any specific domain name.

#### Scenario: domain-required
- **WHEN** `HtmlToMarkdownConverter` is instantiated without a `wiki_domain` argument
- **THEN** the constructor SHALL raise a `TypeError`
- **THEN** no default value SHALL be applied

#### Scenario: domain-explicit
- **WHEN** `HtmlToMarkdownConverter(wiki_domain="example.wiki.gg")` is instantiated
- **THEN** `self.wiki_domain` SHALL be `"example.wiki.gg"`
- **THEN** all link normalization SHALL use the provided domain

#### Scenario: domain-from-strategy
- **WHEN** the converter is instantiated by pipeline code (Phase B/C) or standalone extraction
- **THEN** `wiki_domain` SHALL be read from the strategy's `api.base_url` (extracted hostname) or `domain` field
- **THEN** the pipeline SHALL pass `wiki_domain` to the converter constructor explicitly

### Requirement: config-driven-cleanup

`HtmlToMarkdownConverter` SHALL read cleanup selectors and image filter patterns from an `extraction_config` dictionary passed at construction time, rather than from hardcoded selector strings.

#### Scenario: cleanup-from-extraction-config
- **WHEN** `HtmlToMarkdownConverter` is instantiated with `extraction_config` containing `cleanup_selectors` list
- **THEN** `self._REMOVAL_SELECTORS` SHALL be set from `cleanup_selectors`
- **THEN** if `cleanup_selectors` is absent or empty, a default set SHALL be used: `(".mw-editsection", ".toc", "#toc", ".hatnote")`

#### Scenario: image-filter-from-extraction-config
- **WHEN** `extraction_config` contains `image_filtering.skip_patterns` list
- **THEN** `clean_html()` SHALL remove `<img>` elements whose `src` attribute matches any pattern in the list
- **THEN** if `image_filtering.skip_patterns` is absent or empty, no image filtering SHALL be applied

#### Scenario: strategy-passes-extraction-config
- **WHEN** a strategy file defines `extraction.cleanup_selectors` and `extraction.image_filtering.skip_patterns`
- **THEN** the pipeline SHALL pass these values to `HtmlToMarkdownConverter` at instantiation
- **THEN** the converter SHALL apply the configured cleanup without any site-specific hardcoded overrides

### Requirement: balanced-element-removal-method

`HtmlToMarkdownConverter` SHALL provide `remove_balanced_element(html: str, tag: str, attr_pattern: str) -> str` and `remove_all_matching(html: str, tag: str, attr_pattern: str) -> str` methods as static methods.

The `attr_pattern` parameter is a regex fragment for matching opening-tag attributes. Callers MUST ensure this is a safe regex fragment.

#### Scenario: import-method-available
- **WHEN** external code imports `HtmlToMarkdownConverter`
- **THEN** `HtmlToMarkdownConverter.remove_balanced_element` and `HtmlToMarkdownConverter.remove_all_matching` SHALL be callable as static methods

#### Scenario: used-for-toc-removal
- **WHEN** `clean_html()` processes page content
- **THEN** it SHALL perform balanced/nested-aware element removal for TOC elements (via DOM-native CSS selector decomposition or equivalent)
- **THEN** the previous non-greedy regex approach SHALL be replaced

#### Scenario: used-for-edit-section-removal
- **WHEN** `clean_html()` processes page content
- **THEN** it SHALL perform balanced/nested-aware element removal for edit section elements (via DOM-native CSS selector decomposition or equivalent)

### Requirement: tooltip-icon-link-merge-method

`HtmlToMarkdownConverter` SHALL provide `merge_tooltip_links(html: str) -> str` as a static method.

#### Scenario: merge-called-before-image-conversion
- **WHEN** `convert_body()` runs the conversion pipeline
- **THEN** `merge_tooltip_links()` SHALL be called BEFORE `convert()`

### Requirement: youtube-oembed-extraction-method

`HtmlToMarkdownConverter` SHALL provide `extract_video_links(html: str) -> list[str]` that extracts YouTube video IDs from `data-mw-iframeconfig` attributes and retrieves video titles via the YouTube oEmbed API.

#### Scenario: extract-youtube-titles
- **WHEN** `extract_video_links()` processes HTML containing `data-mw-iframeconfig` with a YouTube embed URL
- **THEN** it SHALL extract the video ID and call the YouTube oEmbed API
- **THEN** it SHALL return a Markdown link with the video title

#### Scenario: oembed-failure-fallback
- **WHEN** the oEmbed API call fails (network error, timeout, or non-200 response)
- **THEN** the method SHALL fall back to `- [YouTube Video (VIDEO_ID)](https://www.youtube.com/watch?v=VIDEO_ID)`
- **THEN** it SHALL NOT raise an exception or block the conversion

### Requirement: video-links-insert-into-body

After extracting video links, the converter SHALL insert them into the "In-game Footage" section of the Markdown body.

#### Scenario: insert-into-in-game-footage
- **WHEN** video links were extracted and the Markdown contains `## In-game Footage`
- **THEN** the video links SHALL be inserted immediately after the heading
- **THEN** if no "In-game Footage" heading exists, the links SHALL be appended at the end of the body

### Requirement: convert-body-pipeline-method

`HtmlToMarkdownConverter` SHALL provide `convert_body(html: str, source_dir: str = "") -> str` as the primary full-pipeline entry point.

#### Scenario: convert-body-ordering
- **WHEN** `convert_body()` is called
- **THEN** it SHALL execute: `merge_tooltip_links()` → `extract_video_links()` → `clean_html()` → `convert()` → insert video links

#### Scenario: pipeline-uses-convert-body
- **WHEN** the MediaWiki API pipeline processes HTML-rendered pages
- **THEN** `phase_b.py` and `standalone.py` SHALL call `convert_body()` instead of `clean_html() + convert()` separately

### Requirement: infobox-field-handlers

`HtmlToMarkdownConverter` SHALL read `infobox_field_handlers` from `extraction_config` and apply handlers during infobox field rendering.

#### Scenario: handler-applied-during-render
- **WHEN** the converter encounters a `<div data-source="field_name">` element in a portable infobox
- **AND** `infobox_field_handlers` contains a handler for `field_name`
- **THEN** the converter SHALL apply the specified handler to the field's raw HTML value
- **THEN** fields not listed in the map SHALL use the default `text` handler

#### Scenario: handler-map-absent
- **WHEN** `extraction_config` does not contain `infobox_field_handlers`
- **THEN** all infobox fields SHALL use the default `text` handler
- **THEN** no error SHALL be raised

### Requirement: hard-dependency-selectolax

The converter SHALL require `selectolax` as a hard dependency. Import failure SHALL cause an immediate `ModuleNotFoundError` at module load time, NOT a silent fallback.

#### Scenario: selectolax-import-fail
- **WHEN** `selectolax` is not installed
- **THEN** `from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter` SHALL raise `ModuleNotFoundError`
- **THEN** no regex fallback SHALL be attempted
