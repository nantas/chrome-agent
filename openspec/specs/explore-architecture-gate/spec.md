# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-architecture-gate`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: Architecture Gate 当前仅校验 `sample_converter.py`，需扩展到同时校验 `html_to_markdown.py`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: strategy-to-pipeline-validation

The system SHALL validate that every field in `strategy.extraction` has a corresponding consumer in BOTH pipeline converter files:
- `scripts/explore/sample_converter.py` (explore path)
- `scripts/mediawiki-api-extract/converters/html_to_markdown.py` (crawl path)

A field is considered "consumed" if either file references it. Dead config detection SHALL flag fields consumed by neither file.

#### Scenario: dual-pipeline-validation

- **WHEN** the Architecture Gate validates `strategy.extraction` fields
- **THEN** the validator SHALL check both `sample_converter.py` AND `html_to_markdown.py`
- **AND** a field is considered `dead_config` only if NEITHER file references it
- **AND** fields consumed by only one file SHALL be reported as `partial_coverage` (warning, not error)

#### Scenario: infobox-config-coverage

- **WHEN** `strategy.extraction.infox` is defined
- **AND** `sample_converter.py` references `infobox` but `html_to_markdown.py` does not
- **THEN** the validator SHALL report `infobox` as `partial_coverage` with severity `warning`
- **AND** SHALL suggest adding `infobox` support to `html_to_markdown.py`

#### Scenario: full-coverage-pass

- **WHEN** `strategy.extraction.infox` is defined
- **AND** both `sample_converter.py` AND `html_to_markdown.py` reference `infobox`
- **THEN** the validator SHALL report `infobox` as `covered`
- **AND** SHALL NOT flag it as dead_config or partial_coverage

### Requirement: pipeline-to-strategy-audit

The agent SHALL perform a manual audit verifying that pipeline converter code contains zero site-specific hardcoded values in BOTH converter files.

#### Scenario: no-hardcoded-selectors-in-both-files

- **WHEN** the agent audits `sample_converter.py` AND `html_to_markdown.py`
- **THEN** the agent SHALL search both files for hardcoded HTML selectors
- **AND** any hardcoded selector not driven by `strategy.extraction` SHALL be reported as a violation

### Requirement: architecture-gate-pipeline-path

The Architecture Gate's internal pipeline path reference SHALL be updated from a single hardcoded path to a list of pipeline files to validate.

#### Scenario: pipeline-paths-configuration

- **WHEN** the Architecture Gate initializes
- **THEN** it SHALL read `_PIPELINE_FILES` as a list of relative paths
- **AND** the list SHALL include both `scripts/explore/sample_converter.py` and `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
- **AND** validation SHALL run against each file in the list
