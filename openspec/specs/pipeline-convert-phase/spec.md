# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-convert-phase`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: handoff P-2 修复——Convert 阶段逐页增量写 .md 文件

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: incremental-page-write
The `run_convert()` function SHALL write each successfully converted page's `.md` file to the output directory immediately after conversion, rather than batching all writes to the end of the phase.

#### Scenario: page-written-immediately-after-conversion
- **WHEN** `run_convert()` converts page "The_Sad_Onion" successfully
- **THEN** the file `<output_dir>/items/the_sad_onion.md` SHALL exist on disk immediately
- **AND** subsequent pages can be converted even if the process is interrupted

#### Scenario: directory-auto-created
- **WHEN** a page's `target_directory` is `"items"` and `<output_dir>/items/` does not exist
- **THEN** the directory SHALL be created before writing the file

#### Scenario: conversion-result-still-in-memory
- **WHEN** incremental write is enabled
- **THEN** the `results` dict SHALL still be populated in memory for downstream Assembly phase consumption
- **AND** the `extraction_results.json` SHALL still be written at the end of the convert phase

### Requirement: skip-already-converted-pages
When resume is enabled and `run_convert()` encounters a page whose output `.md` file already exists at the expected path, it SHALL skip re-conversion and load the result from cache or mark it as skipped.

#### Scenario: resume-skip-converted-page
- **WHEN** resume is enabled AND `<output_dir>/items/the_sad_onion.md` already exists
- **AND** the page title is in `completed_pages` state
- **THEN** the page SHALL be skipped (no re-conversion, no re-fetch from cache)

#### Scenario: force-reconvert-without-resume
- **WHEN** resume is disabled
- **THEN** all pages SHALL be converted regardless of existing output files

### Requirement: conversion-output-format
Each incrementally written `.md` file SHALL contain the full page content including YAML frontmatter, heading, body, and card stats. The format SHALL be identical to what Assembly phase would produce for individual pages.

#### Scenario: output-content-integrity
- **WHEN** a page is incrementally written
- **THEN** the file content SHALL match exactly what `run_assemble()` would produce for that page

## ADDED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
