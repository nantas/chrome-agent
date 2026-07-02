# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`

## ADDED Requirements

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
