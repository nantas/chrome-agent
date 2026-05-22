# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert-target-conflict-detection`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: convert 阶段 incremental write 不检测 target_path 冲突，多个页面写同一路径时静默覆盖

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: target-path-conflict-prescan

Before the main conversion loop, `run_convert()` SHALL perform a pre-scan of all manifest pages to detect target path conflicts — cases where two or more pages share the same `target_directory` + `target_filename` combination.

For each conflicting path, the system SHALL keep the first page (by manifest order) as the winner and mark all subsequent pages with the same path as `target_conflict`.

The system SHALL emit a `log.error` for each conflict, reporting the conflicting path, the winning page title, and all losing page titles.

#### Scenario: detect-and-skip-conflicting-pages

- **GIVEN** manifest pages with:
  - Page A: `target_directory: "items"`, `target_filename: "index.md"`, manifest index 318
  - Page B: `target_directory: "items"`, `target_filename: "index.md"`, manifest index 722
- **WHEN** `run_convert()` pre-scan runs
- **THEN** Page A SHALL be kept as the winner (lower manifest index)
- **AND** Page B SHALL be marked as `target_conflict`
- **AND** a `log.error` SHALL be emitted reporting the conflict

#### Scenario: conflict-page-skipped-during-conversion

- **GIVEN** a page marked as `target_conflict` during pre-scan
- **WHEN** the main conversion loop processes this page
- **THEN** the page SHALL be skipped (not converted, not written to disk)
- **AND** the result entry SHALL have `status: "target_conflict"`
- **AND** `failed_count` SHALL be incremented

#### Scenario: no-false-positives

- **GIVEN** manifest pages with unique target paths
- **WHEN** `run_convert()` pre-scan runs
- **THEN** no pages SHALL be marked as `target_conflict`
- **AND** no conflict-related logs SHALL be emitted

#### Scenario: multiple-pages-same-path

- **GIVEN** manifest pages with:
  - Page A: `target_directory: "items"`, `target_filename: "index.md"`, manifest index 100
  - Page B: `target_directory: "items"`, `target_filename: "index.md"`, manifest index 200
  - Page C: `target_directory: "items"`, `target_filename: "index.md"`, manifest index 300
- **WHEN** `run_convert()` pre-scan runs
- **THEN** Page A SHALL be the winner
- **AND** Page B and Page C SHALL both be marked as `target_conflict`
- **AND** a single `log.error` SHALL report all conflicts for that path
