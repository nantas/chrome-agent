# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-capability-cli`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 CLI 继续保留 `fetch`、`explore`、`crawl` 低层显式命令，但不再作为唯一正式外部入口；`explore` 需要承接深度分析后端职责

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Global command surface
The system SHALL expose `chrome-agent` as the repo-backed low-level explicit execution surface for this repository's external capabilities.

The CLI SHALL define these first-class commands:
- `explore`
- `fetch`
- `crawl`
- `doctor`
- `clean`

#### Scenario: Command inventory
- **WHEN** an operator invokes `chrome-agent --help`
- **THEN** the CLI SHALL present the five first-class commands above
- **AND** it SHALL describe `fetch`, `explore`, and `crawl` as explicit backend workflows rather than as the only user-facing intent layer

### Requirement: JSON-first result contract
The CLI SHALL produce a JSON-first result contract for all first-class commands.

The JSON result SHALL include at least:
- `result`
- `command`
- `target`
- `repo_ref`
- `summary`
- `artifacts`
- `next_action`
- `workflow`
- `engine_path`

#### Scenario: Structured success result
- **WHEN** a command completes successfully
- **THEN** the CLI SHALL emit a machine-readable result object with all fields above
- **AND** `workflow` SHALL identify whether the command executed `content_retrieval` or `platform_analysis`
- **AND** `engine_path` SHALL summarize the actual engine or escalation path used for execution

#### Scenario: Structured partial failure
- **WHEN** a command completes with usable output but unresolved issues
- **THEN** the CLI SHALL emit the same result envelope
- **AND** `result` SHALL be `partial_success`
- **AND** `next_action` SHALL contain an explicit remediation suggestion grounded in the attempted workflow

### Requirement: Explore command routing
The `explore` command SHALL route into the repository-local Platform/Page Analysis backend rather than only a strategy-gap probe.

The repository-local analysis backend MAY inspect page structure, anti-crawl signals, strategy gaps, fallback evidence, and diagnostic artifacts.

#### Scenario: Explore command execution
- **WHEN** `chrome-agent explore <target>` is invoked
- **THEN** the CLI SHALL dispatch to a repository-local workflow that can perform deeper evidence collection and fallback-oriented diagnostics
- **AND** the result SHALL identify `workflow: platform_analysis`
- **AND** the result SHALL return any generated or referenced reports, screenshots, structure clues, or strategy artifacts

### Requirement: Relationship to global workflow skill
The CLI SHALL coexist with the global workflow skill as the backend execution surface for agent-first usage.

#### Scenario: Skill-backed CLI usage
- **WHEN** the global workflow skill invokes the CLI
- **THEN** the CLI SHALL remain the execution backend and source of truth for machine-readable results
- **AND** it SHALL not require the skill to re-implement repository routing or engine selection logic

## REMOVED Requirements

### Requirement: Decommission old global skill as primary entry
**Reason**: Real usage showed that removing the high-level skill re-exposed workflow choice to upstream callers and pushed agents back toward out-of-repo wrappers.
**Migration**: Treat the restored global workflow skill as the recommended agent-first entry; keep the CLI as the low-level explicit backend and shell-facing command surface.
