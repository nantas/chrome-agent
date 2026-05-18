# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-architecture-gate`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `_PIPELINE_FILES` 缩减为单一文件，不再需要 partial_coverage 跟踪

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: single-pipeline-validation

The Architecture Gate SHALL validate against a single pipeline converter file (`scripts/mediawiki-api-extract/converters/html_to_markdown.py`) after the converter unification is complete.

`_PIPELINE_FILES` SHALL be reduced from 2 entries back to 1.

#### Scenario: single-file-architecture-gate

- **WHEN** the Architecture Gate initializes
- **THEN** `_PIPELINE_FILES` SHALL contain exactly one entry: the unified `HtmlToMarkdownConverter` path
- **AND** `_PIPELINE_FILES` SHALL NOT include `scripts/explore/sample_converter.py`
- **AND** the gate SHALL validate against only this single file

### Requirement: partial-coverage-removal

The partial_coverage tracking system SHALL be removed from the Architecture Gate, as it is no longer necessary when only one converter file is validated.

A field is either `covered` (referenced in the single pipeline file) or `dead_config` (not referenced). There is no in-between state.

#### Scenario: no-partial-coverage

- **WHEN** the Architecture Gate runs validation
- **THEN** the `strategy_to_pipeline` result SHALL NOT contain a `partial_coverage` key
- **AND** a field is either `covered` or `dead_config`

### Requirement: dead-config-detection-simplified

The dead config detection logic SHALL be simplified back to single-file scanning, removing the dual-file aggregation logic (`_detect_dead_config_dual()`).

The original `_detect_dead_config()` function (single file) SHALL be restored as the primary detection mechanism.

#### Scenario: dead-config-single-file

- **WHEN** `_detect_dead_config()` is called with a pipeline path
- **THEN** it SHALL scan only that one file for config field references
- **AND** the return type SHALL be `list[str]` (no more tuple with partial_coverage)
