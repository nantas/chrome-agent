# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认仓库的正式对外入口要改成 repo-backed global CLI，但具体执行仍然在当前仓库内部进行，并继续受 AGENTS.md 工作流与 specs 约束

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 服务身份声明
The system SHALL declare chrome-agent as a cross-repo web scraping service with a repo-backed global CLI as its formal external entrypoint.

The service identity SHALL continue to state that repository-local governance remains authoritative for workflow execution.

#### Scenario: Identity declaration
- **WHEN** an operator or agent reads the Service Identity section
- **THEN** the section SHALL state that chrome-agent is a "跨仓库网页抓取服务（cross-repo web scraping service）"
- **AND** it SHALL describe the global `chrome-agent` CLI as the formal external entrypoint
- **AND** it SHALL preserve the four core principles: Scrapling-first, workflow-driven, read-only by default for authenticated runs, and evidence-driven reporting

### Requirement: 工作流路由规则
The system SHALL document that the repo-backed global CLI is only an entry layer, while repository-local workflow routing remains authoritative.

For any request arriving through the global CLI, the repository-local workflow SHALL still decide Content Retrieval versus Platform/Page Analysis according to repository governance.

#### Scenario: CLI entry with repository routing
- **WHEN** a request enters through the global `chrome-agent` CLI
- **THEN** the target repository SHALL still apply its own workflow routing rules
- **AND** the CLI SHALL not bypass or replace those routing decisions with a separate parallel policy layer

### Requirement: 引擎选择策略
The system SHALL preserve repository-local engine selection authority even when a request originates from the global CLI.

#### Scenario: Global entry, local engine selection
- **WHEN** `chrome-agent fetch` or `chrome-agent crawl` dispatches into the repository
- **THEN** the repository-local workflow SHALL continue to apply Scrapling-first selection, strategy overrides, and fallback boundaries
- **AND** the global CLI SHALL not hardcode an alternative engine selection model

### Requirement: 目录结构治理
The system SHALL treat the global CLI as an external access layer and SHALL keep `AGENTS.md` focused on repository governance rather than launcher implementation detail.

#### Scenario: AGENTS.md content boundary after CLI introduction
- **WHEN** AGENTS.md is updated for Phase 5
- **THEN** it SHALL describe the existence and role of the global CLI at the governance level
- **AND** it SHALL keep detailed launcher install and doctor procedures in setup or playbook documents rather than turning AGENTS.md into an install manual
