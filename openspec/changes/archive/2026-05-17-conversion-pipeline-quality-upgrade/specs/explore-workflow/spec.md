# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 explore 工作流增加 Agent Gate 行为规范，强化样本质量自检报告先于样本展示、文件路径输出、agent 自行对比审查、全量重测等要求

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: agent-gate-self-check-before-presentation

The agent SHALL run all S1-S12 self-checks and present the pass/fail summary BEFORE showing any sample Markdown content to the user.

#### Scenario: self-check-report-first
- **WHEN** sample conversion is complete and agent prepares to present results
- **THEN** the agent SHALL output a summary table: `{check_id, status, detail}` for all S1-S12 checks across all samples
- **THEN** the agent SHALL present the overall pass rate (X/Y samples passed, Z issues total)
- **THEN** the agent SHALL NOT output raw Markdown content until the user has seen and acknowledged the self-check report
- **THEN** if all samples pass all checks, the agent SHALL state "✅ All samples passed" and present content
- **THEN** if any sample has failures, the agent SHALL categorize them as fixable/non-fixable and present the remediation plan

### Requirement: agent-gate-sample-file-paths

The agent SHALL write all converted samples to files under `outputs/<run-tag>/` and SHALL present the absolute file paths to the user.

#### Scenario: sample-files-written-to-outputs
- **WHEN** sample conversion is complete
- **THEN** each sample SHALL be written as a `.md` file under `outputs/<run-tag>/`
- **THEN** the file naming SHALL follow the pattern: `{page_type}-{page_title_slugified}.md`
- **THEN** the agent SHALL list all output file paths explicitly in the results presentation
- **THEN** the agent SHALL NOT only print Markdown content to stdout without saving to files

### Requirement: agent-gate-self-audit-before-user-review

The agent SHALL perform a self-audit comparing source HTML content against converted Markdown BEFORE asking the user to review quality.

#### Scenario: agent-self-audits
- **WHEN** sample conversion is complete and agent prepares to present to user
- **THEN** the agent SHALL run `_audit_page()` — a diagnostic function that compares:
  - Source `mw-headline` sections vs Markdown headings
  - Source infobox data-source fields vs Markdown infobox table rows
  - Source `<tr>` count vs Markdown table rows
  - Source images (excluding skip_patterns) vs Markdown `![]()` count
  - Source `<a href="/wiki/">` count vs Markdown full URL link count
- **THEN** the agent SHALL produce a structured discrepancy list before presenting to the user
- **THEN** the agent SHALL NOT delegate the QA responsibility to the user (e.g., "Please review these samples")
- **THEN** the agent SHALL present its own audit findings alongside the samples

#### Scenario: agent-detects-missing-sections
- **WHEN** the self-audit detects missing sections (≥ 1 `mw-headline` not present in Markdown)
- **THEN** the agent SHALL mark the conversion as `partial_success`
- **THEN** the agent SHALL present the exact list of missing sections
- **THEN** the agent SHALL attempt auto-remediation before re-presenting

### Requirement: agent-gate-full-retest-on-converter-change

When the converter or extraction rules are modified in response to audit findings, the agent SHALL re-convert and re-check ALL samples, not just the one that triggered the fix.

#### Scenario: retest-all-after-fix
- **WHEN** the converter code or extraction rules are modified
- **THEN** the agent SHALL re-run `convert_body()` on ALL sample pages
- **THEN** the agent SHALL re-run ALL S1-S12 checks on ALL samples
- **THEN** the agent SHALL report the updated pass/fail status for all samples
- **THEN** the agent SHALL NOT claim "fixed" based on a single sample test

#### Scenario: regression-detection
- **WHEN** a fix for page type A introduces a regression in page type B
- **THEN** the full retest SHALL detect the regression in page type B
- **THEN** the agent SHALL report the regression before proceeding

### Requirement: agent-gate-iteration-limit

The agent-agent SHALL limit the fix→retest→present cycle to at most 3 iterations before requiring explicit user direction.

#### Scenario: max-3-iterations
- **WHEN** the agent has completed 3 cycles of fix→retest→present
- **AND** failures still exist
- **THEN** the agent SHALL present the remaining issues and ask the user to decide: continue fixing / accept as-is / adjust scope
- **THEN** the agent SHALL NOT continue to a 4th iteration without user confirmation

## MODIFIED Requirements

### Requirement: sample-conversion-and-self-check

The system SHALL convert sample pages to Markdown and run self-checks before presenting results to the user.

The following is added to the existing requirement:

#### Scenario: self-check-before-presentation (追加)
- **WHEN** sample conversion is complete
- **THEN** the system SHALL run ALL S1-S12 checks (not just S1-S7) against each sample
- **THEN** the system SHALL produce a per-sample and overall summary report
- **THEN** the system SHALL present the self-check summary BEFORE any sample content
- **THEN** the agent SHALL follow the agent-gate rules defined in ADDED Requirements above
