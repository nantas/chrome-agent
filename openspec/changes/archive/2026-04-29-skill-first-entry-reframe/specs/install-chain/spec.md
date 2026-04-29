# Specification Delta

## Capability 对齐（已确认）

- Capability: `install-chain`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认安装契约要改成“CLI 是 skill 的后端前提，skill 是推荐的 agent 入口”，并且不再提旧 dispatcher runtime

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Thin global launcher model
The system SHALL continue to distribute `chrome-agent` as a thin global launcher rather than as a standalone full runtime package.

The launcher SHALL remain the execution backend used directly by shell callers and indirectly by the global workflow skill.

#### Scenario: Launcher responsibility boundary
- **WHEN** the global launcher is installed
- **THEN** it SHALL provide command discovery and dispatch only
- **AND** it SHALL not duplicate the repository's workflow guidance, AGENTS routing model, or site-specific extraction logic

### Requirement: Doctor command coverage
The `doctor` command SHALL remain the backend readiness check used by both direct CLI callers and the global workflow skill.

At minimum, `doctor` SHALL check:
- launcher availability
- repo-registry resolution for `repo://chrome-agent`
- `CHROME_AGENT_REPO` fallback availability when needed
- repository shape (`AGENTS.md` exists)
- Scrapling CLI preflight status delegated from repository-local logic when relevant

#### Scenario: Skill uses doctor as preflight
- **WHEN** the global workflow skill prepares to dispatch user work
- **THEN** it SHALL be able to rely on `chrome-agent doctor --format json` as the authoritative backend readiness check
- **AND** the install guidance SHALL describe that dependency explicitly

### Requirement: Workflow skill installation path
The install chain SHALL document and support the global workflow skill as the recommended agent-facing installation path on top of the CLI backend.

#### Scenario: Agent-facing installation guidance
- **WHEN** Phase 5+ installation guidance is consulted for agent usage
- **THEN** the guidance SHALL describe installing or updating the global workflow skill in addition to the CLI backend
- **AND** it SHALL make clear that the skill delegates to the CLI rather than replacing it

### Requirement: No legacy dispatcher dependency
The install chain SHALL NOT require `repo-agent`, `codex-agent`, or equivalent prompt-forwarding dispatcher runtimes as part of the supported installation path.

#### Scenario: Supported dependency inventory
- **WHEN** the install contract lists runtime prerequisites
- **THEN** it SHALL include the CLI launcher, repository resolution contract, and repository-local prerequisites
- **AND** it SHALL not include `repo-agent` or `codex-agent` as required workflow dependencies

## REMOVED Requirements

### Requirement: Skill removal from install contract
**Reason**: The new entry model restores an official workflow skill as the recommended agent-facing interface, so removing skill installation from the contract is no longer correct.
**Migration**: Replace "historical skill removed" guidance with "workflow skill delegates to CLI backend" guidance while keeping the thin launcher as the required execution backend.
