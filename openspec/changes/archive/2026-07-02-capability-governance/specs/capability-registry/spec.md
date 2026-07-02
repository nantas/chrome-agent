# Specification Delta

## Capability 对齐（已确认）

- Capability: `capability-registry`
- 来源: `proposal.md` — New Capability
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- `configs/capability-registry.yaml` 是数据 SSOT

## ADDED Requirements

### Requirement: capability-registry-file

`configs/capability-registry.yaml` SHALL declare all currently implemented capabilities as structured YAML. Each entry SHALL include `name`, `implemented_in` (file path), and `strategy_field` (the strategy.md config key that activates it).

#### Scenario: registry-lists-all-cleanup-ops
- **WHEN** registry is loaded
- **THEN** every cleanup op implemented in `scripts/lib/extraction/preprocessor.py` SHALL have a corresponding entry

#### Scenario: registry-lists-all-infobox-handlers
- **WHEN** registry is loaded
- **THEN** every handler function in `scripts/lib/extraction/infobox.py` SHALL have a corresponding entry

#### Scenario: registry-lists-all-special-capabilities
- **WHEN** registry is loaded
- **THEN** every special capability (card_stats, link_fixer, etc.) SHALL have a corresponding entry with its implementation path

### Requirement: doctor-capabilities-check

`chrome-agent doctor --check capabilities` SHALL cross-validate:
1. Every `implemented_in` path in registry points to an existing file
2. Every entry has a corresponding row in `AGENTS.md` §2 Capability Framework
3. Every entry has a corresponding spec directory in `openspec/specs/`

#### Scenario: doctor-passes-when-all-synced
- **WHEN** registry, code, specs, and AGENTS.md are all consistent
- **THEN** `doctor --check capabilities` SHALL exit 0 with no warnings

#### Scenario: doctor-warns-on-missing-spec
- **WHEN** a registry entry has no corresponding `openspec/specs/<cap>/spec.md`
- **THEN** `doctor --check capabilities` SHALL output a WARNING listing the gap

#### Scenario: doctor-warns-on-stale-implemented-in
- **WHEN** a registry entry's `implemented_in` path does not exist
- **THEN** `doctor --check capabilities` SHALL output a WARNING listing the stale entry

### Requirement: capability-gate-at-freeze

`scripts/explore/freeze.py` SHALL run `capability_gate.check_requirements()` before finalizing `strategy.md`. If unknown capabilities are detected, freeze SHALL exit non-zero with a gap report at `${run_dir}/capability-gap.yaml`.

#### Scenario: freeze-blocks-on-unknown-capability
- **WHEN** the scaffold requires a cleanup op not listed in registry
- **THEN** freeze SHALL exit non-zero
- **AND** `${run_dir}/capability-gap.yaml` SHALL contain the gap details

#### Scenario: freeze-passes-when-all-covered
- **WHEN** all scaffold requirements are listed in registry
- **THEN** freeze SHALL proceed normally and write strategy.md
