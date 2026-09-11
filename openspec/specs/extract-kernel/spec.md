# Specification

## Capability 对齐

- Capability: `extract-kernel`
- 来源: `openspec/changes/unify-extract-fetch-kernels/proposal.md`
- 变更类型: modified
- 摘要: 删除 preprocessor B 轴分支 + 编排逻辑归入共享内核 `convert_page_full()`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件

## Requirements

### Requirement: preprocessor-always-full-cleanup

`preprocess_html(html, config)` SHALL always execute the full 6-step cleanup pipeline without accepting a `context` parameter. The function SHALL NOT have any execution-path branching.

#### Scenario: explore-path-still-cleans
- **WHEN** `sample_converter.py` calls `preprocess_html(html, extraction_rules)`
- **THEN** the full 6-step cleanup SHALL execute (infobox removal → cleanup selectors → lazyload → cleanup ops → decorative images → content selection)
- **AND** behavior SHALL be identical to pre-change behavior

#### Scenario: pipeline-path-now-cleans
- **WHEN** `pipeline/phases/convert.py` calls `preprocess_html(html, extraction_config)`
- **THEN** the full 6-step cleanup SHALL execute
- **AND** no `context=` keyword argument SHALL be passed

### Requirement: convert-page-full
`converter.py` SHALL expose `convert_page_full(html, extraction_rules)` with backward-compatible optional rendering context as the single full-page extraction orchestration entry. It SHALL extract infobox from intact input, preprocess HTML, convert body with the supplied or stateless converter, prepend nonempty infobox Markdown, and apply shared post-ops exactly once. It SHALL preserve the input for other read-only consumers such as card-stat extraction.

#### Scenario: sample-converter-delegates-to-kernel
- **WHEN** explore applies extraction rules
- **THEN** it SHALL delegate to the shared entry without its own extraction sequence.

#### Scenario: pipeline-delegates-to-kernel
- **WHEN** pipeline HTML conversion has a stateful converter
- **THEN** it SHALL supply that context to the same entry, extracting before container deletion.

#### Scenario: full-pipeline-output-intact
- **WHEN** input contains enabled infobox fields plus body text
- **THEN** structured fields and body SHALL survive, without a duplicate body rendering of the removed infobox.

#### Scenario: absent-infobox
- **WHEN** no infobox matches
- **THEN** the shared entry SHALL return the converted body without inventing an infobox section.

### Requirement: extract-infobox-via-kernel
The full-page entry SHALL call the shared `extract_infobox` implementation before cleanup. All callers SHALL use one URL-context policy and preserve supplied inline-rendering, handler and source-directory context. Equal input, rules and context SHALL produce identical extracted fields, values and links across execution paths.

#### Scenario: infobox-extraction-identical
- **WHEN** explore and pipeline convert identical HTML under matching rules/context
- **THEN** their infobox Markdown SHALL be identical, including field handlers and resolved links.

## ADDED Requirements

### Requirement: infobox-enable-and-selector-parity
Full-page extraction SHALL extract/prepend an infobox only when enabled, and preprocessing SHALL use the same selector (default `aside.portable-infobox`). Disabled or absent infobox rules SHALL leave the content to ordinary body conversion, without prepending a duplicate structured table.

#### Scenario: enabled-default-selector
- **WHEN** infobox is enabled without an explicit selector
- **THEN** extraction and removal SHALL both match the default portable infobox and fields SHALL appear once.

#### Scenario: disabled-infobox
- **WHEN** infobox configuration is absent or disabled
- **THEN** full-page conversion SHALL NOT prepend an infobox table and ordinary body conversion SHALL preserve the content.
