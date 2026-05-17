# Specification Delta

## Capability 对齐

- Capability: `explore-architecture-gate`
- 来源: `proposal.md`
- 变更类型: `added`
- 用户确认摘要: 新 Gate 插入在 sample self-check 与 user confirmation 之间，确保策略↔管线双向对齐

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: architecture-gate-position

The Architecture Gate SHALL execute AFTER Phase 1 (Sample Conversion & Self-Check) completes AND BEFORE Phase 4 (User Confirmation & Freeze) begins.

#### Scenario: gate-after-self-check
- **WHEN** sample self-check has been presented to the user (or auto-remediation cycle exhausted)
- **AND** the agent prepares to present final samples for user confirmation
- **THEN** the agent SHALL execute the Architecture Gate BEFORE the user confirmation prompt
- **THEN** if the gate returns `fail`, the agent SHALL NOT proceed to user confirmation

#### Scenario: gate-before-freeze
- **WHEN** the Architecture Gate passes
- **THEN** the agent SHALL proceed to present final samples for user confirmation
- **THEN** the user SHALL see the gate result as part of the confirmation summary

### Requirement: strategy-to-pipeline-validation

The system SHALL validate that every field in `strategy.extraction` has a corresponding consumer in the pipeline converter code.

#### Scenario: dead-config-detection
- **WHEN** strategy.extraction contains a top-level key such as `infobox`, `lazyload`, `url_conversion`, `youtube_cleanup`, `cleanup_selectors`, `image_filtering`, `text_normalization`, or `infobox_field_handlers`
- **THEN** the validator SHALL verify that the pipeline source code references this key
- **THEN** the reference SHALL be detected via pattern: `extraction_rules.get("<key>")`, `cfg.get("<key>")`, `rules["<key>"]`, or equivalent read access
- **THEN** any key with zero references in pipeline source SHALL be reported as `dead_config`

#### Scenario: cleanup-operations-validation
- **WHEN** strategy.extraction.cleanup lists operations like `["strip_fandom_infobox_tables", "convert_ambox_to_text", ...]`
- **THEN** the validator SHALL verify each operation string appears in the pipeline source
- **THEN** any operation name with zero matches SHALL be reported as `dead_config`

#### Scenario: nested-fields-validation
- **WHEN** strategy.extraction.nested_object contains sub-fields (e.g., `image_filtering.skip_patterns`, `infobox.selector`)
- **THEN** the validator SHALL verify that the pipeline source references the parent key
- **THEN** sub-field existence SHALL be validated by confirming the pipeline reads the parent key, then falls through to config-driven processing
- **THEN** sub-fields with zero-path to consumer SHALL be reported

### Requirement: pipeline-to-strategy-audit

The agent SHALL perform a manual audit verifying that the pipeline converter code contains zero site-specific hardcoded values.

#### Scenario: no-hardcoded-selectors
- **WHEN** the agent audits `sample_converter.py`
- **THEN** the agent SHALL search for hardcoded HTML selectors (CSS class names, element selectors like `"aside.portable-infobox"`)
- **THEN** the agent SHALL verify that each selector exists in the strategy config's `extraction` block
- **THEN** any selector NOT sourced from strategy SHALL be reported as a violation

#### Scenario: no-hardcoded-domain-names
- **WHEN** the agent audits pipeline code
- **THEN** the agent SHALL search for hardcoded domain names (e.g., `wiki.gg`, `fandom.com`, specific wiki hostnames)
- **THEN** any domain name NOT derived from strategy `image_handling.base_url` or `domain` SHALL be reported

#### Scenario: no-unconditional-site-operations
- **WHEN** the agent audits pipeline code
- **THEN** the agent SHALL verify that YouTube embed cleanup, URL conversion, and lazyload fix are guarded by `if cfg["enabled"]:` or equivalent config check
- **THEN** any unconditional execution of site-specific transformation SHALL be reported

### Requirement: gate-must-pass-before-confirmation

The Agent Gate rules SHALL require the Architecture Gate to pass before proceeding to user confirmation.

#### Scenario: gate-failure-blocks-confirmation
- **WHEN** the Architecture Gate returns `status: "fail"`
- **THEN** the agent SHALL fix ALL reported violations
- **THEN** violations fixes SHALL NOT count toward the 3-iteration limit for quality issues
- **THEN** after fixing violations, the agent SHALL re-run full sample conversion + S1-S12 self-check on ALL samples
- **THEN** after full retest passes, the agent SHALL re-execute the Architecture Gate

#### Scenario: gate-pass-allows-confirmation
- **WHEN** the Architecture Gate returns `status: "pass"`
- **THEN** the agent SHALL include the gate result in the final confirmation summary
- **THEN** the gate result SHALL be presented as: "✅ Architecture Gate passed — no dead config, no hardcoded selectors"

### Requirement: gate-output-format

The gate result SHALL be structured as a JSON-compatible dict with `status`, `strategy_to_pipeline`, and `pipeline_to_strategy` blocks.

#### Scenario: output-structure
- **WHEN** the gate completes
- **THEN** the output SHALL contain:
  - `status`: `"pass"` or `"fail"`
  - `strategy_to_pipeline.status`: `"pass"` or `"fail"`
  - `strategy_to_pipeline.dead_config`: list of unreferenced strategy field names
  - `pipeline_to_strategy.status`: `"pass"` or `"fail"`
  - `pipeline_to_strategy.violations`: list of `{type, detail, location, remediation}` objects
