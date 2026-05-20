# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-resume`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: handoff P-2 修复——Convert 阶段逐页更新 state 支持增量恢复

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: incremental-state-update-during-convert
The pipeline state SHALL be updated after each successfully converted page during the Convert phase, not only at the end of the phase.

#### Scenario: state-updated-per-page
- **WHEN** page "The_Sad_Onion" is successfully converted and written to disk
- **THEN** `mark_completed(output_dir, "The_Sad_Onion")` SHALL be called immediately
- **AND** `.pipeline_state.json` SHALL contain `"The_Sad_Onion"` in `completed_pages`

#### Scenario: state-persistence-on-interrupt
- **WHEN** the process is interrupted after converting 800 of 1756 pages
- **THEN** `.pipeline_state.json` SHALL contain all 800 completed page titles
- **AND** the corresponding 800 `.md` files SHALL exist on disk

### Requirement: convert-resume-skip-completed
When resuming, `run_convert()` SHALL skip pages whose titles are in `completed_pages` AND whose output files exist. This check SHALL use the existing `is_page_completed()` function.

#### Scenario: resume-convert-partial
- **WHEN** resume is enabled AND state shows 800 completed pages
- **AND** 800 `.md` files exist at expected paths
- **THEN** `run_convert()` SHALL only convert the remaining 956 pages
- **AND** the skipped pages SHALL be loaded from `extraction_results.json` (if assemble follows) or marked as `status: "skipped"`

#### Scenario: resume-file-missing-reconvert
- **WHEN** a page title is in `completed_pages` but its `.md` file is missing
- **THEN** the page SHALL be re-converted from cache (existing behavior from `is_page_completed()`)

### Requirement: state-flush-interval
The Convert phase SHALL flush state to disk at least every N pages (configurable, default N=50) to balance I/O overhead with recovery granularity.

#### Scenario: periodic-flush
- **WHEN** Convert phase has processed 50 pages since last state flush
- **THEN** `save_state()` SHALL be called with updated `completed_pages`
- **AND** the flush counter SHALL reset

## ADDED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
