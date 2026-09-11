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

Architecture Gate SHALL validate extraction schema before checking consumers. cleanup and text_normalization SHALL be lists of supported strings; malformed containers/elements and unsupported names SHALL produce structured fail diagnostics with field path, observed type/value and expected contract. Consumers SHALL be resolved against current shared extraction modules and supported infrastructure keys; a shared consumer covers both explore and pipeline callers and SHALL NOT cause a false partial_coverage warning. Top-level and governed nested configuration without a consumer SHALL be rejected.

#### Scenario: dictionary-cleanup-is-fail
- **WHEN** cleanup contains a dictionary or a non-list value
- **THEN** Gate SHALL return fail with the offending path and SHALL NOT skip entries or raise an unhandled unhashable-type exception.

#### Scenario: shared-consumer-is-covered
- **WHEN** an operation is implemented in shared preprocessor/converter and used by both workflows
- **THEN** Gate SHALL report it supported without requiring duplicate implementation in either orchestration module.

#### Scenario: unsupported-nested-normalization
- **WHEN** text_normalization uses legacy keys such as space_fix or an unsupported operation
- **THEN** Gate SHALL report a schema/name error instead of accepting the outer key merely because it appears in source.

### Requirement: pipeline-to-strategy-audit

Architecture Gate SHALL audit active shared extraction consumers for site-specific hardcoded selectors, domains and values not supplied by configuration. Generic defaults and supported operation implementations SHALL be distinguished from site-specific hardcoding. Schema errors SHALL short-circuit unsafe audits while retaining actionable diagnostics.

#### Scenario: schema-error-before-audit
- **WHEN** extraction schema is malformed
- **THEN** Gate SHALL return the schema failure before performing set construction or selector audits on invalid values.

#### Scenario: active-consumer-site-hardcode
- **WHEN** an active shared consumer hardcodes a site domain outside supported generic defaults
- **THEN** the audit SHALL report its module/location and remediation.

### Requirement: architecture-gate-pipeline-path

Gate SHALL use the shared extraction consumer inventory, including `scripts/lib/extraction/preprocessor.py`, `converter.py`, and field-specific shared consumers such as infobox handlers, rather than removed converter paths. Cleanup names SHALL have one authoritative collection associated with actual shared implementations and cross-checked against `configs/capability-registry.yaml`; Gate SHALL NOT infer validity solely from regex over orchestration source.

#### Scenario: consumer-inventory-current
- **WHEN** Gate validates a strategy
- **THEN** it SHALL consult current shared consumers and SHALL NOT require scripts/mediawiki-api-extract files.

#### Scenario: operation-registry-drift
- **WHEN** a declared cleanup operation lacks an implementation or registry entry
- **THEN** the capability consistency check SHALL fail with the missing relationship.
