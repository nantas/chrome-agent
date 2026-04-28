# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认——所有工作流执行前先检查 Scrapling CLI 是否可用；若不可用则先确保安装；涉及持久化 shell 环境写入时先征求用户是否写入 `/Users/nantas-agent/.zshenv`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 工作流路由规则

The system SHALL document the two primary workflow types (Content Retrieval and Platform/Page Analysis), their routing triggers, and the mandatory Scrapling preflight that occurs before a Scrapling-first workflow begins execution.

For any workflow path that depends on Scrapling as the first engine family, the system SHALL check Scrapling CLI availability before attempting fetcher selection or content retrieval.

#### Scenario: Content Retrieval routing

- **WHEN** the user gives only a URL, asks to get/read/fetch/extract page content, or wants a concise failure explanation
- **THEN** the workflow SHALL default to Content Retrieval with Scrapling-first path and lightweight verification
- **AND** Scrapling CLI availability SHALL be checked before the first Scrapling step executes

#### Scenario: Platform/Page Analysis routing

- **WHEN** the user prompt contains signals such as 分析, 调试, 证据, 总结经验, 平台, 结构, 抓取规则, or 复现
- **THEN** the workflow SHALL route to Platform/Page Analysis with deeper evidence collection and fallback escalation
- **AND** if the chosen analysis path still starts with Scrapling, the same Scrapling CLI preflight SHALL run before execution

#### Scenario: Mixed signals

- **WHEN** both Content Retrieval and Platform/Page Analysis signals appear
- **THEN** the workflow SHALL prefer Platform/Page Analysis

#### Scenario: Preflight install assurance

- **WHEN** the workflow requires Scrapling and the Scrapling CLI is not available
- **THEN** the system SHALL first ensure the CLI is installed or restored according to the `scrapling-cli-environment` capability
- **AND** it SHALL resume the requested workflow only after CLI availability is re-verified

### Requirement: 引擎选择策略

The system SHALL define a Scrapling-first engine selection strategy with explicit fallback boundaries in AGENTS.md, and that strategy SHALL run only after Scrapling preflight has succeeded or been explicitly declared unavailable.

#### Scenario: Default Scrapling path

- **WHEN** a webpage grabbing task is initiated and Scrapling preflight succeeds
- **THEN** the workflow SHALL start with Scrapling, selecting the appropriate fetcher (`get` for static, `fetch` for SPA, `stealthy-fetch` for protected pages) unless a live-session continuity trigger is already known

#### Scenario: Stop on unresolved preflight failure

- **WHEN** Scrapling preflight cannot make the CLI available
- **THEN** the workflow SHALL stop before claiming it is executing the Scrapling-first path
- **AND** it SHALL report the installation or configuration failure instead of silently falling through to unrelated tools

#### Scenario: Diagnostic fallback to chrome-devtools-mcp

- **WHEN** Scrapling output is incomplete, blocked, visually suspect, or requires DOM/network/console/screenshot/interaction evidence after a successful preflight and Scrapling attempt
- **THEN** the workflow SHALL escalate to chrome-devtools-mcp as the diagnostic and evidence path

#### Scenario: Live-session continuity fallback to chrome-cdp

- **WHEN** the task must continue immediately on an already-open real Chrome tab, or an approved authenticated state cannot be preserved through Scrapling after a successful preflight and Scrapling attempt
- **THEN** the workflow SHALL escalate to repo-local chrome-cdp as the live-session continuity path

## ADDED Requirements

### Requirement: Persistent shell change approval

The system SHALL treat persistent shell-environment changes as user-approved actions, not as implicit workflow side effects.

#### Scenario: Request to persist Scrapling CLI path

- **WHEN** the workflow determines that adding `SCRAPLING_CLI_PATH` to `/Users/nantas-agent/.zshenv` would improve future runs
- **THEN** it SHALL ask the user for confirmation before writing
- **AND** it SHALL continue without persistent shell modification if the user declines
