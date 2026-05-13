# Specification Delta

## Capability 对齐（已确认）

- Capability: `sample-self-check`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: 新增样本转换后的 agent 自检体系（S1-S7 + auto-remediation loop）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: self-check-s1-image-retention

The system SHALL verify that image count in converted Markdown matches the original HTML (after excluding base64 lazy-load placeholders).

#### Scenario: s1-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL count `N` = total `<img>` tags in original HTML (excluding those with `src="data:image/gif;base64"` that lack a `data-src`)
- **THEN** the system SHALL count `M` = total `![]()` occurrences in converted Markdown
- **THEN** if `M == N`, S1 SHALL be marked `pass`
- **THEN** if `M < N`, S1 SHALL be marked `fail` with diff details

### Requirement: self-check-s2-link-resolution

The system SHALL verify that internal wiki links pointing to known pages are resolved to relative `.md` links.

#### Scenario: s2-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL identify all `/wiki/X` links in original HTML where `X` is a known page
- **THEN** the system SHALL verify each such link appears as `[text](X.md)` in the Markdown
- **THEN** if any known-page link is NOT resolved, S2 SHALL be marked `fail`

### Requirement: self-check-s3-infobox-extraction

The system SHALL verify that pages with `{{Infobox ...}}` wikitext have structured data in the Markdown frontmatter or body.

#### Scenario: s3-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL check if the original page contains `{{Infobox ...}}` in wikitext
- **THEN** if infobox exists but frontmatter lacks `has_infobox: true` or no `## Infobox` section exists, S3 SHALL be marked `fail`
- **THEN** if no infobox exists, S3 SHALL be marked `skip`

### Requirement: self-check-s4-empty-content

The system SHALL verify that the Markdown body (excluding frontmatter) is non-empty and meaningful.

#### Scenario: s4-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL measure `length` of Markdown body (content after `---` frontmatter terminator)
- **THEN** if `length == 0`, S4 SHALL be marked `fail`
- **THEN** if `length > 0`, S4 SHALL be marked `pass`

### Requirement: self-check-s5-text-integrity

The system SHALL verify that the converted Markdown text has no detectable formatting anomalies.

#### Scenario: s5-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan for the following anomaly patterns:
  - Missing space around version numbers: `([a-z])(\d+(?:\.\d+)*)([a-z])`
  - Base64 placeholder residue: `data:image/gif;base64`
  - Escape artifacts: `\*\*\*`
  - Repeated link text: `(\w[\w\s]{1,15}?) +\1` where both variants reference the same target
- **THEN** if any anomaly pattern matches, S5 SHALL be marked `fail`
- **THEN** if no anomalies found, S5 SHALL be marked `pass`

### Requirement: self-check-s6-table-integrity

The system SHALL verify that list/summary pages preserve their table structure after conversion.

#### Scenario: s6-pass-fail
- **WHEN** sample conversion is complete and the original page contains data tables (>2 rows)
- **THEN** the system SHALL check if the Markdown output preserves table rows (≥3 data rows)
- **THEN** if the table is collapsed or missing, S6 SHALL be marked `fail`
- **THEN** if no data table exists in the original, S6 SHALL be marked `skip`

### Requirement: self-check-s7-image-wrapper

The system SHALL verify that images are NOT wrapped in unnecessary external links ([![alt](img)](url)) unless they serve original navigation intent.

#### Scenario: s7-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan for `[!\[alt\]\(img\)\]\(url\)` patterns
- **THEN** if any image wrapper link exists and is NOT a deliberate design choice (e.g., gallery page), S7 SHALL be marked `fail`
- **THEN** if no wrapper links exist, S7 SHALL be marked `pass`

### Requirement: auto-remediation

The system SHALL, when self-check fails on known fixable issues, attempt automatic remediation.

#### Scenario: auto-fix-loop
- **WHEN** any check (S1-S7) is marked `fail`
- **THEN** the system SHALL determine if the failure type is on the known-fixable list:
  - `fixable`: base64 residue, space normalization, link resolution, image wrapper, table class missing
  - `non-fixable`: empty content, infobox template mismatch, structural issues
- **THEN** if fixable, the system SHALL amend the extraction rules, re-convert, and re-run self-check
- **THEN** the auto-remediation SHALL run at most 2 iterations
- **THEN** if 2 iterations do not resolve all fails, the system SHALL mark as `"auto-remediation exhausted — needs human review"`
