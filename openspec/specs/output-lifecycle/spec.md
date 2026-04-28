# output-lifecycle — Spec

## Purpose

Define how the global `chrome-agent` CLI classifies artifacts, stores durable and disposable outputs, reports lifecycle metadata, and cleans disposable data safely by default.
## Requirements
### Requirement: Artifact classes
The system SHALL classify CLI artifacts into durable and disposable classes, and repository defaults MUST align git tracking behavior with those classes.

The minimum classes SHALL be:
- durable reports under `reports/`
- disposable run outputs under `outputs/`

Repository default tracking alignment SHALL be:
- `outputs/` ignored in `.gitignore`
- `reports/` not globally ignored by `.gitignore`

#### Scenario: Lifecycle-to-git consistency
- **WHEN** maintainers validate repository lifecycle policy
- **THEN** `outputs/` SHALL be configured as ignored disposable artifacts
- **AND** `reports/` SHALL be retained as durable artifacts eligible for version control

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

### Requirement: Repository tracking alignment

Repository defaults SHALL align artifact lifecycle classes with Git tracking behavior.

Default alignment SHALL be:
- disposable run outputs under `outputs/` are Git-ignored by default
- durable reports under `reports/` are not globally Git-ignored by default

#### Scenario: Disposable output tracking boundary

- **WHEN** a workflow emits transient run artifacts under `outputs/`
- **THEN** those artifacts SHALL remain untracked by default via repository ignore rules

#### Scenario: Durable report tracking boundary

- **WHEN** a workflow emits reusable reports or evidence under `reports/`
- **THEN** those artifacts SHALL remain eligible for version control by default

### Requirement: Clean result reporting

The `clean` command SHALL report what it removed and what it intentionally preserved.

#### Scenario: Clean command result

- **WHEN** `chrome-agent clean` completes
- **THEN** the structured result SHALL identify the deleted disposable artifacts
- **AND** it SHALL identify any preserved durable artifacts when relevant to operator safety

