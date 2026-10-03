# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` / 用户确认 P-2～P-4
- 变更类型: modified（增加既有 self_check 的来源契约）
- 用户确认摘要: 修复 S1 全页计数、S9 内容词误报、S5 源文笔误误报，与 P-1 同一 change。

## 规范真源声明

本文件为自检行为真源；design/tasks/verification SHALL 引用本文件。

## ADDED Requirements

### Requirement: self-check-source-context
Self-check SHALL distinguish original HTML, its declared input scope (full document or content fragment), strategy-selected source content, intentionally excluded content and separately retained infobox content. It SHALL preserve original evidence and SHALL NOT derive expected retention solely from already cleaned/converter-produced HTML. Main and iterate SHALL supply the same current extraction rules and source context. Legacy callers SHALL remain callable, but missing evidence SHALL be explicit and SHALL NOT fabricate a pass for an evidence-dependent check. A declared full-document selector that does not match SHALL produce an explicit scope failure rather than silently audit the whole page; explicitly identified API content fragments SHALL remain valid without an outer selector wrapper.

#### Scenario: full-page-versus-api-fragment
- **WHEN** the same body is supplied as a full document with skin or as an explicitly identified API fragment
- **THEN** content-retention checks SHALL use equivalent intended source content and exclude only evidenced intentional removals.

#### Scenario: missing-content-selector-match
- **WHEN** a full document does not contain its declared content root
- **THEN** scope validation SHALL fail explicitly rather than silently change expected content.

#### Scenario: main-iterate-agreement
- **WHEN** main and iterate audit the same source, Markdown and current extraction configuration
- **THEN** they SHALL return equivalent source-dependent verdicts.

### Requirement: s1-intended-image-retention
S1 SHALL compare Markdown images against images intended to survive from selected source content plus separately retained infobox content, without double counting overlapping regions. It SHALL honor evidenced configured exclusions, lazyload source selection and existing relative-image checks. Images outside intended scope SHALL not cause loss failures. Actual missing images SHALL still fail, including missing occurrences of duplicate images; equal counts with different image identities SHALL NOT pass. Expected evidence SHALL be independent of the renderer's output.

#### Scenario: skin-images-excluded
- **WHEN** a full page contains 11 skin images outside the selected body and all intended body images survive
- **THEN** S1 SHALL pass without a fabricated image_wrapper remediation.

#### Scenario: retained-image-loss
- **WHEN** one required body or separately retained infobox image is removed from Markdown
- **THEN** S1 SHALL fail even if a different extra image keeps the total count unchanged.

#### Scenario: intentional-filter-and-lazyload
- **WHEN** an image is excluded by configured rules and a retained image uses a lazyload source
- **THEN** S1 SHALL exclude the former and compare the latter using its resolved retained source.

### Requirement: s9-source-based-navigation-leakage
S9 SHALL use source navigation/excluded-region evidence and output correspondences rather than a global vocabulary of article topics. Topic words such as Items, Bosses and Trinkets SHALL NOT alone fail. Special/action links SHALL NOT alone fail when legitimately present in retained content. Content appearing in both retained and excluded regions SHALL not be attributed to leaked navigation without disambiguating evidence. Missing navigation provenance SHALL yield an explicit skip when no reliable verdict is possible.

#### Scenario: legitimate-related-items
- **WHEN** retained content contains consecutive Combat Items, Stagecoach Items and Inn Items links
- **THEN** S9 SHALL not report navigation leakage based on those labels.

#### Scenario: actual-skin-navigation
- **WHEN** a login/registration sequence present solely in a source skin navigation region appears in Markdown
- **THEN** S9 SHALL fail and report the matching source evidence.

#### Scenario: body-navigation-label-collision
- **WHEN** a label/target also belongs to a legitimate body link
- **THEN** S9 SHALL not fail solely because the same label/target occurs in excluded navigation.

### Requirement: s5-source-attributed-repetition
S5 SHALL compare each repeated-text occurrence in rendered Markdown text with normalized retained source text, preserving location/context or occurrence counts sufficient to distinguish source repetition from newly introduced repetition. Source-existing repetition SHALL be recorded as a non-failing note; new repetition SHALL fail. One source occurrence SHALL NOT exempt unlimited matching output occurrences. Other S5 anomaly checks SHALL continue independently. Comparison SHALL ignore link destinations and markup syntax and normalize ordinary whitespace/inline formatting without merging unrelated blocks. Missing source evidence for repetition SHALL be reported explicitly rather than inventing a conversion-error attribution.

#### Scenario: faithful-source-typo
- **WHEN** retained HTML already contains of of or over over and conversion preserves it
- **THEN** S5 SHALL record a source note without a repetition failure.

#### Scenario: converter-introduced-repetition
- **WHEN** source contains a single word but Markdown contains that word twice consecutively
- **THEN** S5 SHALL fail with an introduced-repetition finding.

#### Scenario: extra-occurrence-not-exempted
- **WHEN** source contains one duplicated phrase and Markdown contains an additional occurrence
- **THEN** S5 SHALL still report the additional repetition as a failure.

#### Scenario: source-note-with-other-anomaly
- **WHEN** a source-existing typo coexists with raw closing tags or another confirmed output anomaly
- **THEN** S5 SHALL retain the non-repetition failure despite the source note.

### Requirement: self-check-summary-and-remediation-compatibility
Check results SHALL retain pass/fail/skip statuses compatible with summarize and remediation consumers. Source notes SHALL be additional evidence, not a new unhandled status. Only confirmed conversion failures eligible for existing remediation SHALL enter automatic repair; notes and evidence-insufficient skips SHALL not become KI conversion failures. Summaries SHALL expose skipped evidence-dependent checks so absence of evidence is not presented as complete validation.

#### Scenario: source-note-does-not-trigger-repair
- **WHEN** only source-existing repetitions are found
- **THEN** no repetition failure or repair request SHALL be generated, and the note SHALL remain visible.

#### Scenario: evidence-unavailable
- **WHEN** a legacy caller provides insufficient source context for S9 or repetition attribution
- **THEN** the unavailable validation SHALL be explicitly represented without suppressing independently confirmed failures.
