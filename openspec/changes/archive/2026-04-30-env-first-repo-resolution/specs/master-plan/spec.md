# Specification Delta

## Capability 对齐（已确认）

- Capability: `master-plan`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 skill-first 入口保持不变，但其默认运行前提从 repo-registry-first 调整为 env-first；Phase 5 之后的安装与运行叙事需要据此更新

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 能力全景图
The system SHALL define the external entry model as skill-first and CLI-backed while treating `CHROME_AGENT_REPO` as the default runtime prerequisite for the backend CLI path.

The capability map SHALL continue to show:
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

### Requirement: README rewrite
The system SHALL rewrite `README.md` to reflect the env-first, skill-first / CLI-backed public model.

#### Scenario: README content
- **WHEN** the README is updated after this change
- **THEN** it SHALL distinguish the recommended agent-facing entry from the CLI backend command surface
- **AND** it SHALL explain that `CHROME_AGENT_REPO` is the default runtime prerequisite
- **AND** it SHALL reserve repo-registry references for explicit repo-ref or maintenance-oriented paths
