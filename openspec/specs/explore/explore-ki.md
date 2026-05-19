# Explore Domain: KI Lifecycle — Merged Spec

> **Merged from**: `explore-ki-lifecycle`
> **Purpose**: Defines the Known Issue lifecycle within the explore workflow: classification by owner domain, priority assignment (P0-P3), fix ordering, status tracking, KI table in strategy files, and separation from Architecture Gate.

---

## Source: `explore-ki-lifecycle`

### Requirement: ki-classification-by-owner

Every Known Issue identified during self-check SHALL be classified by its repair owner domain: `strategy`, `pipeline`, or `self_check`.

#### Scenario: classify-pipeline-bug
- **WHEN** a self-check failure is caused by incorrect data extraction or transformation in the pipeline converter
- **THEN** the KI SHALL be classified as owner=`pipeline`
- **THEN** the fix SHALL be in `sample_converter.py` or `_extract_infobox()` (must remain generic, config-driven)

#### Scenario: classify-self-check-false-positive
- **WHEN** a self-check failure is caused by a methodology issue in the check itself
- **THEN** the KI SHALL be classified as owner=`self_check`
- **THEN** the fix SHALL be in `self_check.py`

#### Scenario: classify-strategy-gap
- **WHEN** a self-check failure is caused by missing or incorrect extraction configuration in the strategy file
- **THEN** the KI SHALL be classified as owner=`strategy`
- **THEN** the fix SHALL be in `sites/strategies/<domain>/strategy.md`

#### Scenario: classify-systemic-limitation
- **WHEN** a failure cannot be fixed at any of the three owner levels
- **THEN** the KI SHALL be classified as owner=`self_check` with status=`open_systemic`
- **THEN** the resolution SHALL document the exact systemic limitation

### Requirement: ki-priority-assignment

Every KI SHALL be assigned a priority level P0-P3 based on its impact on output quality.

#### Scenario: assign-p0-data-corruption
- **WHEN** a KI causes infobox field values to be incorrect or links/images to be broken
- **THEN** the KI SHALL be assigned P0

#### Scenario: assign-p1-quality-impact
- **WHEN** a KI causes readability reduction or minor data pollution
- **THEN** the KI SHALL be assigned P1

#### Scenario: assign-p2-check-methodology
- **WHEN** a KI is a self-check scope or precision issue that does not affect actual output quality
- **THEN** the KI SHALL be assigned P2

#### Scenario: assign-p3-skip-or-cosmetic
- **WHEN** a KI is already in `skip` status or has negligible visual impact
- **THEN** the KI SHALL be assigned P3

### Requirement: ki-fix-priority-order

KI fixes SHALL be applied in priority order: P0 first, then P1, then P2, then P3.

#### Scenario: batch-fix-by-priority
- **WHEN** multiple KIs of different priorities exist
- **THEN** the agent SHALL fix all P0 KIs as a batch before any P1 fixes
- **THEN** after each priority batch, a full retest of ALL samples SHALL be run
- **THEN** each priority batch SHALL count as 1 iteration toward the 3-iteration limit

#### Scenario: skip-fix-on-iteration-exhaustion
- **WHEN** 3 iterations have been completed and KIs still remain unresolved
- **THEN** the agent SHALL present remaining KIs to the user for decision

### Requirement: ki-status-tracking

Every KI SHALL have a status tracked through its lifecycle: `open` → `in_progress` → (`resolved` | `wontfix` | `open_systemic`).

#### Scenario: status-transition-on-fix
- **WHEN** a KI fix is applied and verified via full retest
- **THEN** the KI status SHALL transition from `in_progress` to `resolved`
- **THEN** the resolution SHALL be documented in the strategy.md KI table

#### Scenario: status-open-systemic
- **WHEN** investigation confirms a KI cannot be fixed at strategy, pipeline, or self_check level
- **THEN** the KI status SHALL be set to `open_systemic`
- **THEN** the resolution SHALL document the systemic limitation and any workaround

### Requirement: ki-table-in-strategy

All KIs SHALL be documented in the strategy file's `## Known Issues (Post-Validation)` section as a Markdown table.

#### Scenario: ki-table-schema
- **WHEN** the strategy file is created or updated
- **THEN** the KI table SHALL contain columns: `ID`, `Issue`, `Status`, `Priority`, `Owner`, `Impact`, `Resolution`
- **THEN** each KI SHALL have a unique `KI-N` identifier scoped to the site

#### Scenario: ki-table-update-after-fix
- **WHEN** a KI is resolved
- **THEN** the agent SHALL update the KI table in `strategy.md`
- **THEN** the agent SHALL NOT only track KI status in memory or session context

### Requirement: ki-separation-from-architecture-gate

KI classification and prioritization SHALL occur AFTER the Architecture Gate passes, not before.

#### Scenario: gate-before-ki
- **WHEN** self-check failures exist AND Architecture Gate violations also exist
- **THEN** the agent SHALL fix Architecture Gate violations first
- **THEN** the agent SHALL classify remaining failures as KIs ONLY after the gate passes
