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

`converter.py` SHALL expose `convert_page_full(html, extraction_rules)` as the single shared orchestration entry point for the full 4-step extraction pipeline:

1. Extract infobox via `extract_infobox()`
2. Preprocess HTML via `preprocess_html()`
3. Convert to Markdown via `HtmlToMarkdownConverter.convert_body()`
4. Prepend infobox to body if extracted

#### Scenario: sample-converter-delegates-to-kernel
- **WHEN** `sample_converter.py` applies extraction rules to an HTML page
- **THEN** it SHALL call `convert_page_full(html, extraction_rules)` from `converter.py`
- **AND** SHALL NOT contain its own orchestrator logic for the 4-step pipeline

#### Scenario: full-pipeline-output-intact
- **WHEN** `convert_page_full()` is called with the same HTML and extraction rules as the current `_apply_extraction()`
- **THEN** the output SHALL be identical to pre-change behavior

### Requirement: extract-infobox-via-kernel

`convert_page_full()` SHALL call `extract_infobox()` from within the shared extraction library. The infobox extraction SHALL use the same logic regardless of which B-axis path calls it.

#### Scenario: infobox-extraction-identical
- **WHEN** explore path calls `convert_page_full()` and pipeline path calls infobox extraction manually
- **THEN** both SHALL produce identical infobox Markdown for the same HTML input
