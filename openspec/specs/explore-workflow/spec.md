# Specification: explore-workflow

> Capability spec. Originated from openspec change [`capability-governance`](../../changes/capability-governance/proposal.md) — integrates a capability gate into the explore freeze phase.

## Purpose

Define explore capability gating and source-aware content validation so genuine conversion failures remain distinguishable from source defects and insufficient evidence.

## Requirements

### Requirement: capability-gate-module

`scripts/explore/capability_gate.py` SHALL provide `check_requirements(strategy_scaffold, registry)` that returns a list of unmatched capability gaps. Each gap entry SHALL include `capability`, `issue`, and `detail` fields.

#### Scenario: gate-detects-unknown-cleanup-op
- **WHEN** scaffold contains `extraction.cleanup: ["unknown_op"]`
- **AND** registry has no entry for `unknown_op`
- **THEN** `check_requirements()` SHALL return a gap entry with `capability: "convert"` and `issue: "new_cleanup_op"`

#### Scenario: gate-passes-known-cleanup-op
- **WHEN** scaffold contains `extraction.cleanup: ["strip_fandom_infobox_tables"]`
- **AND** registry has an entry for `strip_fandom_infobox_tables`
- **THEN** `check_requirements()` SHALL return an empty list

### Requirement: freeze-gap-check

`scripts/explore/freeze.py` SHALL call `capability_gate.check_requirements()` before writing strategy.md. On gap detection, SHALL write `capability-gap.yaml` to the run directory and exit with a non-zero code.

#### Scenario: freeze-exits-on-gap
- **WHEN** gap is detected
- **THEN** `capability-gap.yaml` SHALL be written
- **AND** process SHALL exit with code 5 (CAPABILITY_GAP_EXIT_CODE)

#### Scenario: freeze-continues-without-gap
- **WHEN** no gaps are detected
- **THEN** freeze SHALL write strategy.md normally and exit 0

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
