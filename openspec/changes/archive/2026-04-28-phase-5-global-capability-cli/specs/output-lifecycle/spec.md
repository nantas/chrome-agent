# Specification Delta

## Capability 对齐（已确认）

- Capability: `output-lifecycle`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认原 Phase 5 的 output-lifecycle 仍保留，但作为新全局 CLI 的支撑能力；`clean` 是正式一级命令，默认以安全清理 transient artifacts 为主

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Artifact classes
The system SHALL classify CLI artifacts into durable and disposable classes.

The minimum classes SHALL be:
- durable reports under `reports/`
- disposable run outputs under `outputs/`

#### Scenario: Durable reporting artifact
- **WHEN** a workflow produces a reusable summary, evidence bundle, or verification-style report
- **THEN** that artifact SHALL be classified as durable
- **AND** it SHALL be stored under `reports/`

#### Scenario: Disposable run output
- **WHEN** a workflow produces transient extracted content, intermediate files, or per-run working output
- **THEN** that artifact SHALL be classified as disposable
- **AND** it SHALL be stored under `outputs/`

### Requirement: CLI artifact disclosure
The CLI SHALL return artifact metadata in its structured result contract.

Each artifact entry SHALL distinguish whether it is durable or disposable.

#### Scenario: Mixed artifact return
- **WHEN** a command generates both a durable report and disposable extracted content
- **THEN** the result `artifacts` array SHALL list both outputs
- **AND** each entry SHALL label its lifecycle class so callers know what can be cleaned safely

### Requirement: Clean command default safety
The `clean` command SHALL default to cleaning disposable artifacts only.

#### Scenario: Default clean behavior
- **WHEN** `chrome-agent clean` is run without an elevated scope flag
- **THEN** it SHALL remove disposable artifacts under `outputs/`
- **AND** it SHALL preserve durable artifacts under `reports/`

### Requirement: Explicit destructive cleanup
The system SHALL require an explicit stronger scope to delete durable reports.

#### Scenario: Durable cleanup request
- **WHEN** the caller explicitly requests report deletion
- **THEN** the `clean` command SHALL require an explicit scope or confirmation mechanism defined by the implementation
- **AND** it SHALL not delete `reports/` as part of the default cleanup path

### Requirement: Run output organization
Disposable outputs SHALL be organized in a way that supports per-run cleanup and operator inspection.

#### Scenario: Per-run output grouping
- **WHEN** the CLI executes a fetch, crawl, or explore workflow that emits disposable outputs
- **THEN** those outputs SHALL be grouped under a run-scoped location beneath `outputs/`
- **AND** the CLI SHALL be able to clean those outputs without needing to infer from unrelated durable reports

### Requirement: Clean result reporting
The `clean` command SHALL report what it removed and what it intentionally preserved.

#### Scenario: Clean command result
- **WHEN** `chrome-agent clean` completes
- **THEN** the structured result SHALL identify the deleted disposable artifacts
- **AND** it SHALL identify any preserved durable artifacts when relevant to operator safety
