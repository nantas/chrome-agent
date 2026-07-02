# Specification: governance

> Capability spec for the capability-governance machinery (registry sync, derived-doc sync, doctor check). Originated from openspec change [`capability-governance`](../../changes/capability-governance/proposal.md).
>
> Related domain spec: [`governance.md`](./governance.md) — Core Governance merged spec (AGENTS.md structure, workflow routing, engine selection).

## ADDED Requirements

### Requirement: capability-registry-sync-constraint

AGENTS.md §0.5 SHALL include constraint C11: "新增能力实现文件后必须同步 `configs/capability-registry.yaml`；openspec change 归档前必须 `doctor --check capabilities` 通过。"

#### Scenario: c11-is-declarative
- **WHEN** a new cleanup op is added to `preprocessor.py`
- **THEN** the developer SHALL add a corresponding entry to `capability-registry.yaml`
- **AND** `doctor --check capabilities` SHALL pass before the change is archived

### Requirement: derived-doc-sync-principle

GOVERNANCE.md SHALL include §7 documenting that architecture docs, AGENTS.md, and openspec specs are derived from SSOT (code/config). The section SHALL list which derived doc must be updated for each type of SSOT change.

#### Scenario: governance-doc-lists-sync-rules
- **WHEN** a developer modifies `capability-registry.yaml`
- **THEN** GOVERNANCE.md §7 SHALL indicate that `AGENTS.md` §2 and `openspec/specs/` must also be checked for consistency

### Requirement: doctor-check-capabilities-command

`chrome-agent doctor --check capabilities` SHALL be a recognized sub-check that validates registry ↔ code ↔ specs ↔ AGENTS.md consistency. Non-zero exit SHALL block openspec change archive.

#### Scenario: doctor-sub-check-documented
- **WHEN** `chrome-agent doctor --help` is invoked
- **THEN** `capabilities` SHALL appear in the list of available checks
