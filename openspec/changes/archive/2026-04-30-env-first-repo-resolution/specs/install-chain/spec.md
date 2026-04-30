# Specification Delta

## Capability 对齐（已确认）

- Capability: `install-chain`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 `CHROME_AGENT_REPO` 应提升为默认运行前提；缺失或无效时默认停止并要求显式指定路径；repo-registry 不再作为默认热路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Environment-default installation assumptions
The install chain SHALL treat `CHROME_AGENT_REPO` as the default runtime prerequisite for the global workflow skill and the repo-backed CLI.

#### Scenario: Install without explicit repo path
- **WHEN** a caller installs or invokes the CLI without a direct repository path override
- **THEN** the install chain SHALL expect `CHROME_AGENT_REPO` to identify the local chrome-agent repository
- **AND** it SHALL not describe repo-registry as the default runtime locator for high-frequency usage

### Requirement: Doctor command coverage
The `doctor` command SHALL remain the backend readiness check used by both direct CLI callers and the global workflow skill.

At minimum, `doctor` SHALL check:
- launcher availability
- `CHROME_AGENT_REPO` default availability
- repository shape (`AGENTS.md` exists)
- Scrapling CLI preflight status delegated from repository-local logic when relevant

#### Scenario: Healthy doctor result
- **WHEN** all required runtime dependencies are available
- **THEN** `chrome-agent doctor` SHALL return `success`
- **AND** it SHALL identify the resolved repository path and runtime readiness state

#### Scenario: Broken doctor result
- **WHEN** `CHROME_AGENT_REPO` is missing or invalid and no explicit `--repo` override is provided
- **THEN** `chrome-agent doctor` SHALL return `failure`
- **AND** it SHALL point to the missing or invalid env stage and the remediation required

#### Scenario: Skill uses doctor as preflight
- **WHEN** the global workflow skill prepares to dispatch user work
- **THEN** it SHALL be able to rely on `chrome-agent doctor --format json` as the authoritative backend readiness check
- **AND** the install guidance SHALL describe that dependency explicitly

### Requirement: Workflow skill installation path
The install chain SHALL document and support the global workflow skill as the recommended agent-facing installation path on top of the CLI backend.

#### Scenario: Agent-facing installation guidance
- **WHEN** Phase 5+ installation guidance is consulted for agent usage
- **THEN** the guidance SHALL describe installing or updating the global workflow skill in addition to the CLI backend
- **AND** it SHALL make clear that `CHROME_AGENT_REPO` is the default runtime prerequisite
- **AND** it SHALL describe explicit `--repo` overrides as the non-default alternative path

## REMOVED Requirements

### Requirement: Registry-first installation assumptions
**Reason**: The new default runtime model optimizes for env-backed high-frequency usage rather than registry-backed auto-discovery.
**Migration**: Promote `CHROME_AGENT_REPO` to the default runtime contract and document repo-registry only for explicit repo-ref override scenarios.
