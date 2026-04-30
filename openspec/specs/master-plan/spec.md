# master-plan — Spec

## Purpose

Define the repository-wide planning document, public README framing, and phase boundaries for the chrome-agent service roadmap.

## Requirements

### Requirement: Master planning document

The system SHALL produce a master planning document at `docs/governance-and-capability-plan.md` that defines the full project landscape without diving into per-capability implementation details.

#### Scenario: Document structure

- **WHEN** the document is generated
- **THEN** it SHALL contain the following sections:
  - 项目目标与服务身份声明（仓库作为"跨仓库网页抓取服务"）
  - 当前状态摘要（已验证的能力、现有结构）
  - 能力全景图（对外: explore/fetch/crawl；对内: site-strategy/anti-crawl-strategy/engine-registry/output-lifecycle）
  - 阶段划分与交付边界（Phase 1–5 描述+各阶段输出物）
  - 依赖关系（哪个阶段前置哪个）
  - 技术栈与工具链说明（当前引擎 + 扩展方向）
  - 治理约束（repo:// 语义、binding 引用、决策记录索引）

#### Scenario: Phase boundary definition

- **WHEN** each phase is described
- **THEN** the phase entry SHALL include: phase name, scope, deliverables, required specs/contracts to create, and a clear exclusion boundary

### Requirement: 能力全景图

The system SHALL define the external entry model as skill-first and CLI-backed while treating `CHROME_AGENT_REPO` as the default runtime prerequisite for the backend CLI path.

The capability map SHALL show:
- the global `chrome-agent` workflow skill as the recommended agent-facing entry
- the repo-backed `chrome-agent` CLI as the low-level explicit command surface for `explore`, `fetch`, `crawl`, `doctor`, and `clean`

#### Scenario: Phase 5 capability framing

- **WHEN** the master plan describes the external capability progression
- **THEN** Phase 5+ SHALL be framed around a skill-first workflow entry with an env-first backend runtime path
- **AND** it SHALL not frame repo-registry as the default repository lookup path for high-frequency usage

### Requirement: 阶段划分

The system SHALL describe the post-Phase-5 runtime contract as a two-layer entry model whose default local repository source is `CHROME_AGENT_REPO`.

#### Scenario: Phase 5 summary

- **WHEN** the master plan lists Phase 5 scope, deliverables, and boundaries
- **THEN** the scope SHALL describe workflow skill + CLI layering, env-first repository resolution, and explicit override support
- **AND** it SHALL not describe repo-registry-first auto-discovery as the primary runtime assumption

### Requirement: 依赖关系

The system SHALL explain that the skill-first entry layer depends on the stable repository contracts and the CLI backend without replacing either one.

#### Scenario: Phase dependency wording

- **WHEN** the plan explains the dependency shape of Phase 5
- **THEN** it SHALL state that the workflow skill depends on the repo-backed CLI and the repository's stable engine, strategy, and governance contracts
- **AND** it SHALL explain that the skill adds intent routing and result packaging rather than a parallel execution runtime

### Requirement: README rewrite

The system SHALL rewrite `README.md` to reflect the env-first, skill-first / CLI-backed public model.

#### Scenario: README content

- **WHEN** the README is updated after this change
- **THEN** it SHALL distinguish the recommended agent-facing entry from the CLI backend command surface
- **AND** it SHALL explain that `CHROME_AGENT_REPO` is the default runtime prerequisite
- **AND** it SHALL reserve repo-registry references for explicit repo-ref or maintenance-oriented paths
