# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-resume`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户选择三层推进方案，要求新增断点续传支持

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: state-file-persistence

The system SHALL maintain a `.pipeline_state.json` file in the output directory to track pipeline progress.

The state file SHALL contain:
- `phase`: the current pipeline phase (`homepage`, `A`, `B`, `C`)
- `completed_pages`: list of page titles that have been successfully extracted
- `total_pages`: total number of pages in the manifest
- `last_updated`: ISO 8601 timestamp of last state write
- `run_id`: unique identifier for the pipeline run

#### Scenario: state-file-created-on-start

- **WHEN** pipeline starts with `--resume` flag
- **AND** no `.pipeline_state.json` exists
- **THEN** a new state file SHALL be created
- **THEN** `completed_pages` SHALL be initialized to empty array

#### Scenario: state-file-loaded-on-resume

- **WHEN** pipeline starts with `--resume` flag
- **AND** `.pipeline_state.json` exists from a prior run
- **THEN** the state file SHALL be loaded
- **THEN** `completed_pages` SHALL be used to skip already-completed pages

### Requirement: page-level-skip-on-resume

During Phase B, the system SHALL skip pages whose titles appear in `completed_pages` of the state file.

A page SHALL be considered completed if a corresponding `.md` file exists at its target path AND its title is in `completed_pages`.

#### Scenario: skip-completed-page

- **WHEN** Phase B processes page `"Monstro"`
- **AND** `completed_pages` contains `"Monstro"`
- **AND** the output file `bosses/Monstro.md` exists
- **THEN** the page SHALL be skipped
- **THEN** no API call SHALL be made for this page
- **THEN** a log message `"Skipping Monstro (already completed)"` SHALL be emitted

#### Scenario: re-extract-stale-page

- **WHEN** Phase B processes page `"Monstro"`
- **AND** `completed_pages` contains `"Monstro"`
- **AND** the output file `bosses/Monstro.md` does NOT exist (was deleted)
- **THEN** the page SHALL be re-extracted
- **THEN** `completed_pages` SHALL be updated after successful re-extraction

### Requirement: periodic-state-flush

The system SHALL flush the state file to disk periodically during long-running operations.

The flush interval SHALL be configurable via `--resume-flush-interval` (default: 100 pages).

#### Scenario: periodic-flush

- **WHEN** Phase B has processed 100 pages since last flush
- **THEN** the state file SHALL be written to disk
- **THEN** `last_updated` SHALL reflect the current time

#### Scenario: state-flush-on-completion

- **WHEN** a pipeline phase completes
- **THEN** the state file SHALL be written to disk with final `completed_pages`

### Requirement: resume-cli-flag

The system SHALL expose `--resume` and `--no-resume` CLI flags for pipeline commands.

- `--resume`: enable checkpoint/resume behavior (default)
- `--no-resume`: disable resume, always start fresh (ignore existing state)

#### Scenario: resume-enabled-by-default

- **WHEN** `chrome-agent mediawiki pipeline` is invoked without `--resume` or `--no-resume`
- **THEN** resume behavior SHALL be enabled
- **THEN** existing `.pipeline_state.json` SHALL be loaded

#### Scenario: no-resume-fresh-start

- **WHEN** `chrome-agent mediawiki pipeline` is invoked with `--no-resume`
- **THEN** no existing state file SHALL be loaded
- **THEN** a fresh state file SHALL be created, overwriting any existing one
