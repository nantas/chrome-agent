# Specification Delta

## Capability 对齐（已确认）

- Capability: `master-plan`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认总体规划需要从 CLI-first 叙事调整为 skill-first / CLI-backed，并保留 CLI 的低层显式命令定位

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 能力全景图
The system SHALL define the external entry model as skill-first and CLI-backed while continuing to list `explore`, `fetch`, and `crawl` as the repository's external capabilities.

The capability map SHALL show:
- the global `chrome-agent` workflow skill as the recommended agent-facing entry
- the repo-backed `chrome-agent` CLI as the low-level explicit command surface for `explore`, `fetch`, `crawl`, `doctor`, and `clean`

#### Scenario: Phase 5 capability framing
- **WHEN** the master plan describes the external capability progression
- **THEN** Phase 5 SHALL be framed around a skill-first workflow entry with a repo-backed CLI backend
- **AND** it SHALL not frame the CLI as the only formal user-facing entry

### Requirement: 阶段划分
The system SHALL redefine the Phase 5 stage goal as a two-layer entry contract: workflow skill on top, capability CLI beneath.

#### Scenario: Phase 5 summary
- **WHEN** the master plan lists Phase 5 scope, deliverables, and boundaries
- **THEN** the scope SHALL describe restoring an official workflow skill, preserving the thin CLI backend, and formalizing their contract boundary
- **AND** the deliverables SHALL include the workflow-skill capability contract in addition to the CLI and install-chain updates
- **AND** the phase boundary SHALL continue to exclude open-ended spidering, pure deterministic runtime reimplementation, runtime monitoring, and remote orchestration

### Requirement: 依赖关系
The system SHALL explain that the skill-first entry layer depends on the stable repository contracts and the CLI backend without replacing either one.

#### Scenario: Phase dependency wording
- **WHEN** the plan explains the dependency shape of Phase 5
- **THEN** it SHALL state that the workflow skill depends on the repo-backed CLI and the repository's stable engine, strategy, and governance contracts
- **AND** it SHALL explain that the skill adds intent routing and result packaging rather than a parallel execution runtime

### Requirement: README rewrite
The system SHALL rewrite `README.md` to reflect the skill-first, CLI-backed public model.

#### Scenario: README content
- **WHEN** the README is updated after this change
- **THEN** it SHALL distinguish the recommended agent-facing entry from the CLI backend command surface
- **AND** it SHALL avoid describing the workflow skill as retired if it remains the recommended agent entry
