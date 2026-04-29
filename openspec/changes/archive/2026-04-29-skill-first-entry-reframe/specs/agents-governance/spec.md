# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认正式入口模型改为 skill-first / CLI-backed；仓库内 workflow 仍保留执行权威

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 服务身份声明
The system SHALL declare chrome-agent as a cross-repo web scraping service with a skill-first, CLI-backed external entry model.

The service identity SHALL state that:
- the global `chrome-agent` workflow skill is the recommended primary entry for agent-driven usage
- the repo-backed `chrome-agent` CLI is the low-level explicit execution surface and shell/backend entry
- repository-local governance remains authoritative for workflow execution

#### Scenario: Identity declaration
- **WHEN** an operator or agent reads the Service Identity section
- **THEN** the section SHALL state that chrome-agent is a "跨仓库网页抓取服务（cross-repo web scraping service）"
- **AND** it SHALL describe the global workflow skill as the recommended agent-first entry
- **AND** it SHALL describe the repo-backed CLI as the backend execution surface rather than the only formal entry
- **AND** it SHALL preserve the four core principles: Scrapling-first, workflow-driven (AGENTS.md + skills), read-only by default for authenticated runs, and evidence-driven reporting

### Requirement: 工作流路由规则
The system SHALL document that both the global workflow skill and the repo-backed CLI are entry layers, while repository-local workflow routing remains authoritative.

For any request arriving through the skill or the CLI, the repository-local workflow SHALL still decide Content Retrieval versus Platform/Page Analysis according to repository governance.

#### Scenario: Skill entry with repository routing
- **WHEN** a request enters through the global `chrome-agent` workflow skill
- **THEN** the skill MAY route the request to `fetch`, `explore`, or `crawl`
- **AND** the repository-local workflow SHALL remain authoritative for engine selection, fallback escalation, and reporting behavior

#### Scenario: CLI entry with repository routing
- **WHEN** a request enters through the repo-backed `chrome-agent` CLI
- **THEN** the target repository SHALL still apply its own workflow routing and execution rules
- **AND** the CLI SHALL not replace those routing decisions with a parallel policy layer

### Requirement: 目录结构治理
The system SHALL treat `skills/chrome-agent/SKILL.md` as an actively governed repository artifact rather than a retired compatibility relic.

#### Scenario: Skills directory role
- **WHEN** the directory governance section describes `skills/`
- **THEN** it SHALL identify `skills/chrome-agent/` as the source of the official global workflow skill
- **AND** it SHALL require that the skill's workflow guidance stay aligned with the repository specs and playbooks

### Requirement: Reference Index
The system SHALL index both the agent-facing skill path and the CLI/playbook path in its governance references.

#### Scenario: Reference coverage
- **WHEN** AGENTS.md or README links the repository's external entry documentation
- **THEN** the references SHALL cover the global workflow skill and the repo-backed CLI/backend guidance together
- **AND** they SHALL not describe the skill as merely historical if it remains the recommended agent-first entry
