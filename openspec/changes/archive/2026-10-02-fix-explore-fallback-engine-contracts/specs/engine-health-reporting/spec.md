# Specification Delta

## Capability 对齐（已确认）

- Capability: engine-health-reporting
- 来源: proposal.md；用户要求基于已讨论的 doctor 修复方案创建 change。
- 变更类型: new；不修改既有 repo-freshness 规则。

## 规范真源声明

本文件是本 change 的健康报告行为真源；design/tasks/verification 必须引用。

## ADDED Requirements

### Requirement: complete-per-engine-version-report
The version checker SHALL emit a structured result for every selected configured engine, even when one executable is missing, times out or cannot be inspected. Missing executables SHALL be classified as not_installed and SHALL NOT terminate reporting for other engines. Inspection exceptions SHALL be distinguished from an observed absent installation.

#### Scenario: one-executable-missing
- **WHEN** CloakBrowser Python is absent while other engines are inspectable
- **THEN** JSON SHALL contain its not_installed record and the other engines' results
- **AND** all_ok SHALL be false and the process SHALL indicate a non-healthy check result

#### Scenario: inspection-error
- **WHEN** one engine times out or its version cannot be parsed
- **THEN** its result SHALL identify the inspection failure without suppressing other records

### Requirement: doctor-validates-version-check-outcome
Doctor SHALL validate the checker process outcome, JSON schema and selected-engine coverage. Missing scripts, spawn errors, timeout, empty/malformed output, missing engine records and inconsistent exit/status combinations SHALL produce an explicit blocking check failure with actionable remediation. They SHALL NOT become all_ok=true with an empty engine list.

#### Scenario: broken-checker
- **WHEN** the checker is missing, crashes without JSON, times out, emits malformed JSON or omits configured engines
- **THEN** doctor SHALL report version_check_failed and SHALL NOT return success
- **AND** next_action SHALL explain the actual failed check

#### Scenario: valid-unhealthy-json
- **WHEN** the checker exits nonzero with complete valid JSON describing non-healthy engines
- **THEN** doctor SHALL retain those engine records instead of treating all nonzero exits as malformed output

### Requirement: explicit-optional-engine-readiness
Doctor SHALL distinguish optional lazy-install readiness from required prerequisites and checker failures. A missing optional fallback with a supported lazy preflight MAY be non-blocking, but SHALL remain non-healthy and explicitly carry blocking=false, readiness=needs_preflight and its remediation. Overall doctor SHALL return partial_success when any such check is non-healthy; it SHALL explicitly state dispatch is permitted only when all failed checks are non-blocking. This SHALL NOT weaken existing freshness/reload or authorization gates.

#### Scenario: optional-missing-only
- **WHEN** the only failed check is an observed missing optional CloakBrowser environment with supported lazy preflight
- **THEN** doctor SHALL return partial_success with that check non-blocking and instruct the workflow to run preflight when the fallback is selected
- **AND** it SHALL NOT claim all engines are healthy

#### Scenario: required-or-unknown-failure
- **WHEN** a required prerequisite fails or version-check execution is indeterminate
- **THEN** the failed check SHALL be blocking and normal workflow dispatch SHALL stop

#### Scenario: healthy-complete-check
- **WHEN** all selected engines and required checks are healthy and no existing gate blocks
- **THEN** doctor SHALL return success backed by complete check evidence
