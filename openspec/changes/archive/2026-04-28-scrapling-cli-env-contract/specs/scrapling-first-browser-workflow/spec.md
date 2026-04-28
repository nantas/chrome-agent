# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-first-browser-workflow`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认——Scrapling-first 相关 setup 与 MCP 配置不再依赖 git 跟踪文件中的绝对路径；执行前先检查 Scrapling CLI；若缺失则先确保安装，并在写入 `/Users/nantas-agent/.zshenv` 前征求确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件是 superseded capability 的补充 delta，用于约束仍保留的 setup / historical workflow 文档

## MODIFIED Requirements

### Requirement: Default workflow ordering

The system SHALL express the default webpage grabbing workflow as one explicit operator flow that starts with task routing, performs Scrapling CLI preflight, defaults to Scrapling, and escalates only when verified fallback triggers are present.

#### Scenario: Default content retrieval

- **WHEN** the operator reads repository workflow documentation for a normal webpage grabbing task
- **THEN** the documented flow SHALL first route between `Content Retrieval` and `Platform/Page Analysis`
- **AND** it SHALL check Scrapling CLI availability before the first Scrapling fetcher or session mode is invoked

#### Scenario: Scrapling path selection

- **WHEN** the task is already on the Scrapling path and preflight succeeds
- **THEN** the documented default flow SHALL map common cases to the matching first fetcher or mode, including `get` for static or article pages, `fetch` for SPA or dynamic pages, `stealthy-fetch` for protected pages, and bulk or session variants only when those scopes are actually needed

#### Scenario: Preflight blocks execution

- **WHEN** Scrapling CLI preflight fails and install assurance does not restore availability
- **THEN** the workflow SHALL stop before attempting Scrapling execution
- **AND** it SHALL report the unmet setup prerequisite

### Requirement: Environment contract

The system SHALL document and verify the runtime requirements needed to use Scrapling from this repository without embedding host-specific absolute paths in git-tracked files.

Setup guidance and project-scoped MCP configuration SHALL use `SCRAPLING_CLI_PATH` or an equivalent environment-variable-resolving launcher as the canonical reference to the Scrapling executable.

#### Scenario: Local setup

- **WHEN** Scrapling-first workflow is installed or verified
- **THEN** the repository SHALL document a Python `>=3.10` environment, Scrapling package installation, browser dependency installation, CLI smoke checks, and MCP server configuration
- **AND** the documented Scrapling executable reference SHALL be environment-variable-based instead of a host-specific absolute path

#### Scenario: Unsupported local Python

- **WHEN** the system Python is below Scrapling's supported version
- **THEN** the setup guidance SHALL use an isolated environment such as `uv` instead of relying on the system Python

#### Scenario: Project-scoped MCP launch configuration

- **WHEN** project-scoped MCP configuration is documented or maintained for Scrapling
- **THEN** the tracked configuration SHALL resolve the executable from `SCRAPLING_CLI_PATH` or an equivalent launcher
- **AND** it SHALL NOT require editing git-tracked files merely because the host username or home path changes

### Requirement: Documentation and site knowledge

The system SHALL keep workflow documentation, decision records, playbooks, and site notes aligned with the Scrapling-first routing model and the environment-variable-based install contract.

#### Scenario: Workflow documentation update

- **WHEN** the change is implemented
- **THEN** `AGENTS.md`, `README.md`, setup docs, and related playbooks SHALL describe Scrapling as the first path, define fallback boundaries, and explain the preflight/install-confirmation flow

#### Scenario: No stale absolute-path guidance

- **WHEN** setup docs or project-scoped config examples are updated
- **THEN** they SHALL no longer instruct operators to copy a user-specific absolute Scrapling path into tracked files
