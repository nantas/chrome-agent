# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` / 用户要求按已讨论的完整修复方案创建单一 change。
- 变更类型: modified（为既有能力补充本次诊断所得契约）。
- 用户确认摘要: 修复共享结构根因、来源自检和声明式标题语义，不重新抓取、不以检查全绿代替内容验证。

## 规范真源声明

本文件是本 change 的行为规范真源；design/tasks/verification SHALL 引用本文件，项目页面不替代 delta。

## ADDED Requirements

### Requirement: s6-table-data-row-classification
S6 SHALL distinguish actual Markdown table delimiter rows from data rows using table position and per-cell delimiter syntax. A row containing only punctuation or a short hyphen SHALL NOT be excluded merely because its characters resemble a delimiter. Synthetic headers and declared structural transformations SHALL be distinguished from retained source data, and the existing tolerance SHALL NOT be widened to hide this defect.

#### Scenario: inn-hyphen-data-rows
- **WHEN** Inn conversion retains its 15 hyphen-only data rows
- **THEN** S6 SHALL count them and report the matching 94 source/output structural rows rather than 94/79.

#### Scenario: delimiter-position-and-loss
- **WHEN** valid delimiters, a headerless table, escaped pipes and hyphen data coexist
- **THEN** only actual delimiter/synthetic rows SHALL be excluded; deleting sufficient real rows to exceed the existing tolerance SHALL still fail.

### Requirement: s5-source-attributed-version-anomalies
Version-like spacing checks SHALL inspect visible Markdown text, excluding code, link destinations and image destinations. They SHALL distinguish source-existing alphanumeric identifiers or source defects from conversion-introduced concatenation using original retained source evidence. Existing source occurrences SHALL produce notes without automatic repair; additional introduced occurrences SHALL still fail. Missing attribution evidence SHALL be explicit. Other S5 anomalies and finite-budget repetition checks SHALL remain independent.

#### Scenario: lair-source-identifier
- **WHEN** source and output both contain Battle Config2fc
- **THEN** S5 SHALL report source evidence as a non-failing note and SHALL NOT request space normalization.

#### Scenario: new-spacing-anomaly
- **WHEN** source contains separated visible tokens but conversion joins them into a version-like candidate
- **THEN** S5 SHALL report the introduced anomaly; a matching source identifier elsewhere SHALL NOT exempt unlimited new occurrences.

#### Scenario: source-note-and-independent-failure
- **WHEN** a source-existing identifier coexists with an independently confirmed raw-tag or escape anomaly
- **THEN** S5 SHALL retain the independent failure despite the source note.

### Requirement: s8-declared-heading-semantics
S8 SHALL compare intended headings derived from original retained source and declared heading-normalization rules, not infer expectations solely from converter-cleaned output. Configured semantic pairs SHALL contribute one expected heading with the declared source level. Ordinary bold text SHALL NOT substitute for a heading. Intentional hidden exclusions and unsupported ambiguous mappings SHALL be explained, not fabricated as complete validation.

#### Scenario: paired-groups-retained
- **WHEN** the two Enemies pages use declared semantic heading pairs
- **THEN** S8 SHALL verify all 14/3 group headings at their expected levels without duplicate expectations.

#### Scenario: bold-is-not-heading
- **WHEN** an expected group survives only as bold body text, is removed, or is emitted at the wrong level
- **THEN** S8 SHALL report the corresponding structural defect.

### Requirement: source-aware-offline-batch-audit
A tracked, tested batch audit entry SHALL accept explicit local source/output pairs with stable page identity, current extraction rules, original HTML, input scope and source URL. It SHALL build the same source context used by main/iterate, preserve pass/fail/skip and notes, and summarize coverage per check. It SHALL NOT acquire network content or overwrite source/production outputs. Unknown scope or missing input SHALL yield explicit evidence gaps/failures, not clean passes. Relative/localized link destinations SHALL be reconciled with supplied page mappings or marked ambiguous rather than misattributed as loss/leakage.

#### Scenario: full-collection-context
- **WHEN** 209 DD2 source/output pairs are audited offline
- **THEN** S1/S5/S9 SHALL receive source context and results SHALL show per-check pass/fail/skip counts, notes, source identity and reasons; zero failures with skipped checks SHALL NOT be called complete validation.

#### Scenario: reproducible-embedded-batch
- **WHEN** self-contained fixtures run through the tracked batch entry and main/iterate equivalent inputs
- **THEN** source-dependent results SHALL agree without local outputs, untracked strategies or network access.

#### Scenario: missing-source-or-page-mapping
- **WHEN** a batch input lacks its original source or a localized destination cannot be attributed reliably
- **THEN** the result SHALL identify the exact page and evidence gap instead of silently skipping the page or inventing a pass.
