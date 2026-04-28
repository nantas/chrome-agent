# report-emission-gating Specification

## Purpose
TBD - created by archiving change align-output-lifecycle-gitignore. Update Purpose after archive.
## Requirements
### Requirement: Durable report emission gate
The CLI MUST gate durable report creation under `reports/` by workflow intent or explicit operator request.

Default gate policy SHALL be:
- `explore` workflow: durable report emission enabled by default
- non-`explore` workflows (including fetch and crawl): durable report emission disabled by default
- explicit report flag/parameter: enables durable report emission regardless of workflow

#### Scenario: Default simple fetch execution
- **WHEN** the operator runs a simple fetch-style command without an explicit report parameter
- **THEN** the CLI SHALL return extracted content/artifact metadata without creating a durable file under `reports/`

#### Scenario: Explore workflow execution
- **WHEN** the operator runs the `explore` workflow without overriding report behavior
- **THEN** the CLI SHALL create a durable report artifact under `reports/`

#### Scenario: Explicit report request on non-explore workflow
- **WHEN** the operator runs `fetch` or `crawl` and explicitly requests report output via CLI parameter
- **THEN** the CLI SHALL create a durable report artifact under `reports/`

