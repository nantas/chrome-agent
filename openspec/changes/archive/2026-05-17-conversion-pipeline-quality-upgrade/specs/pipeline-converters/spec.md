# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 `HtmlToMarkdownConverter` 增加 balanced removal、tooltip merge、YouTube oEmbed 方法，并修改 `convert_images` 签名

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: balanced-element-removal-method

`HtmlToMarkdownConverter` SHALL provide `remove_balanced_element(html: str, tag: str, attr_pattern: str) -> str` and `remove_all_matching(html: str, tag: str, attr_pattern: str) -> str` methods as specified in the `balanced-element-removal` spec.

#### Scenario: import-method-available
- **WHEN** external code executes `from scripts.mediawiki_api_extract.converters import HtmlToMarkdownConverter`
- **THEN** `HtmlToMarkdownConverter.remove_balanced_element` and `HtmlToMarkdownConverter.remove_all_matching` SHALL be callable as static methods

#### Scenario: used-for-toc-removal
- **WHEN** `clean_html()` processes page content
- **THEN** it SHALL use `remove_all_matching(html, "div", r'id="toc"')` to remove the table of contents
- **THEN** the previous non-greedy regex approach SHALL be replaced

#### Scenario: used-for-edit-section-removal
- **WHEN** `clean_html()` processes page content
- **THEN** it SHALL use `remove_all_matching(html, "span", r'class="[^"]*mw-editsection"')` to remove edit section links

### Requirement: tooltip-icon-link-merge-method

`HtmlToMarkdownConverter` SHALL provide `merge_tooltip_links(html: str) -> str` as specified in the `tooltip-icon-link-merge` spec.

#### Scenario: merge-called-before-image-conversion
- **WHEN** `convert_body()` runs the conversion pipeline
- **THEN** `merge_tooltip_links()` SHALL be called BEFORE `convert_images_to_md()`

### Requirement: youtube-oembed-extraction-method

`HtmlToMarkdownConverter` SHALL provide `extract_video_links(html: str) -> list[str]` that extracts YouTube video IDs from `data-mw-iframeconfig` attributes and retrieves video titles via the YouTube oEmbed API.

#### Scenario: extract-youtube-titles
- **WHEN** `extract_video_links()` processes HTML containing `<figure ... data-mw-iframeconfig="{&quot;src&quot;:&quot;https://www.youtube-nocookie.com/embed/L_J3jvzaZto?autoplay=1&quot;}">`
- **THEN** it SHALL extract the video ID `L_J3jvzaZto`
- **THEN** it SHALL call `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=L_J3jvzaZto&format=json`
- **THEN** it SHALL return a Markdown link with the video title: `- [Binding of Isaac: Rebirth Item guide - The Sad Onion](https://www.youtube.com/watch?v=L_J3jvzaZto)`

#### Scenario: oembed-failure-fallback
- **WHEN** the oEmbed API call fails (network error, timeout, or non-200 response)
- **THEN** the method SHALL fall back to `- [YouTube Video (VIDEO_ID)](https://www.youtube.com/watch?v=VIDEO_ID)`
- **THEN** it SHALL NOT raise an exception or block the conversion

#### Scenario: no-video-embeds
- **WHEN** `extract_video_links()` processes HTML with no `data-mw-iframeconfig` attributes
- **THEN** it SHALL return an empty list `[]`

### Requirement: video-links-insert-into-body

After extracting video links, the converter SHALL insert them into the "In-game Footage" section of the Markdown body.

#### Scenario: insert-into-in-game-footage
- **WHEN** video links were extracted and the Markdown contains `## In-game Footage`
- **THEN** the video links SHALL be inserted immediately after the `## In-game Footage` heading
- **THEN** if no "In-game Footage" heading exists, the links SHALL be appended at the end of the body

## MODIFIED Requirements

### Requirement: config-driven-cleanup

`HtmlToMarkdownConverter` SHALL read cleanup selectors from `extraction_config` as currently specified, AND SHALL additionally accept:

- `skip_patterns` in `extraction_config.image_filtering` — list of regex patterns for images to exclude (passed to `convert_images_to_md()`)
- `wiki_domain` as a required constructor parameter (no hardcoding)

#### Scenario: cleanup-from-extraction-config
- **WHEN** `HtmlToMarkdownConverter` is instantiated with `extraction_config` containing `cleanup_selectors` list
- **THEN** `self._REMOVAL_SELECTORS` SHALL be set from `cleanup_selectors`
- **THEN** the default set SHALL be `(".mw-editsection", ".toc", "#toc", ".hatnote")` when none provided

#### Scenario: image-filter-from-extraction-config (modified)
- **WHEN** `extraction_config` contains `image_filtering.skip_patterns` list
- **THEN** `convert_images_to_md()` SHALL be called with these patterns as the `skip_patterns` parameter
- **THEN** if `image_filtering.skip_patterns` is absent, NO image filtering SHALL be applied

#### Scenario: wiki-domain-from-strategy (modified)
- **WHEN** `HtmlToMarkdownConverter` is instantiated
- **THEN** `wiki_domain` SHALL be read from `extraction_config.domain` or extracted from `extraction_config.api.base_url`
- **THEN** all internal link and image URL resolution SHALL use this domain
