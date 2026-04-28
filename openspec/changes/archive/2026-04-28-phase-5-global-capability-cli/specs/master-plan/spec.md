# Specification Delta

## Capability 对齐（已确认）

- Capability: `master-plan`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认需要把 Phase 5 从“安装链与清理闭环”重写为“全局 capability CLI”，其中 install-chain 与 output-lifecycle 保留但降级为支撑能力

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 能力全景图
The system SHALL define Phase 5 as the stage that formalizes the global entry contract for the repository's external capabilities.

The capability map SHALL continue to list `explore`, `fetch`, and `crawl` as external capabilities, but Phase 5 SHALL be the stage that gives them a formal global CLI surface.

#### Scenario: Phase 5 capability framing
- **WHEN** the master plan describes the external capability progression
- **THEN** Phase 5 SHALL be framed around a repo-backed global CLI for `explore`, `fetch`, `crawl`, `doctor`, and `clean`
- **AND** it SHALL not be framed only as an installation and cleanup closure stage

### Requirement: 阶段划分
The system SHALL redefine the Phase 5 stage goal to "全局 capability CLI" while keeping install-chain and output-lifecycle as support planes.

#### Scenario: Phase 5 summary
- **WHEN** the master plan lists Phase 5 scope, deliverables, and boundaries
- **THEN** the scope SHALL describe global CLI formalization, repo-registry-first repository resolution, strategy-guided crawl formalization, and supporting install/output capabilities
- **AND** the deliverables SHALL include a CLI capability contract in addition to install-chain and output-lifecycle specs
- **AND** the phase boundary SHALL exclude open-ended spidering, pure deterministic runtime reimplementation, runtime monitoring, and remote orchestration

### Requirement: 依赖关系
The system SHALL keep Phase 5 dependent on the stable outputs of Phase 4 while clarifying the new dependency purpose.

#### Scenario: Phase dependency wording
- **WHEN** the plan explains `Phase 5 ← Phase 4`
- **THEN** it SHALL state that the global CLI depends on stable engine, strategy, and extension governance contracts inside the repository
- **AND** it SHALL explain that Phase 5 uses those contracts as the repo-local execution authority rather than replacing them
