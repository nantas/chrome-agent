# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-first-browser-workflow`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认按一个聚合能力推进，覆盖 Scrapling 优先路由、环境接入、验证和 fallback 边界。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Scrapling-first routing

The system SHALL treat Scrapling as the first tool path for webpage grabbing tasks, including public content retrieval, JavaScript-rendered pages, protected-page attempts, batch URL grabs, and read-only logged-in/session experiments when the user has approved the target scope.

#### Scenario: Public content request

- **WHEN** the user asks to get, read, fetch, or extract content from a public URL
- **THEN** the workflow starts with Scrapling before `chrome-devtools-mcp` or `chrome-cdp`

#### Scenario: Dynamic or protected page request

- **WHEN** a page needs JavaScript rendering, stealth handling, session continuity, or bot-blocking mitigation
- **THEN** the workflow selects the matching Scrapling fetcher or session mode before escalating to browser diagnostics

#### Scenario: Approved logged-in read-only request

- **WHEN** the user approves a specific logged-in target page and the task is read-only
- **THEN** the workflow attempts a Scrapling session-based path first and records whether session reuse succeeds, fails, or requires live-tab fallback

#### Scenario: Logged-in verification precondition

- **WHEN** no user-approved logged-in target page is available for the current change
- **THEN** the workflow documents the approval precondition and leaves the logged-in experiment as deferred follow-up evidence instead of claiming it was exercised

### Requirement: Fallback boundaries

The system SHALL use `chrome-devtools-mcp` and `chrome-cdp` as fallback or evidence paths instead of default first paths.

#### Scenario: Diagnostic fallback

- **WHEN** Scrapling output is incomplete, visually suspect, blocked, or requires DOM, network, console, screenshot, or interaction evidence
- **THEN** the workflow escalates to `chrome-devtools-mcp` for structured diagnostics and evidence capture

#### Scenario: Live-tab fallback

- **WHEN** the task must continue immediately in an already-open real Chrome tab, or Scrapling cannot safely preserve an approved authenticated/session state
- **THEN** the workflow escalates to repo-local `chrome-cdp` under the existing read-only live-session boundary unless the user explicitly broadens scope

### Requirement: Environment contract

The system SHALL document and verify the runtime requirements needed to use Scrapling from this repository.

#### Scenario: Local setup

- **WHEN** Scrapling-first workflow is installed or verified
- **THEN** the repository documents a Python `>=3.10` environment, Scrapling package installation, browser dependency installation, CLI smoke checks, and MCP server configuration

#### Scenario: Unsupported local Python

- **WHEN** the system Python is below Scrapling's supported version
- **THEN** the setup guidance uses an isolated environment such as `uv` instead of relying on the system Python

### Requirement: Verification baseline

The system SHALL extend the browser-task verification baseline to measure Scrapling-first success and fallback need.

#### Scenario: Baseline run

- **WHEN** the Scrapling-first workflow is evaluated
- **THEN** verification covers at least a static public page, a dynamic page, an article extraction page with inline image URLs, and a protected-page attempt

#### Scenario: Deferred logged-in evidence

- **WHEN** a logged-in read-only target has not been explicitly approved for the current verification run
- **THEN** verification records that the logged-in experiment remains deferred and does not mark it as exercised evidence

#### Scenario: Content retrieval output

- **WHEN** Scrapling successfully extracts article-style content
- **THEN** the result preserves title, final URL, main body reading order, and inline image URLs when present

#### Scenario: Failure output

- **WHEN** Scrapling cannot obtain usable content
- **THEN** the result records the fetcher/session path used, final URL or failure stage, blocking reason, and the next fallback path

### Requirement: Documentation and site knowledge

The system SHALL keep workflow documentation, decision records, playbooks, and site notes aligned with the Scrapling-first routing model.

#### Scenario: Workflow documentation update

- **WHEN** the change is implemented
- **THEN** `AGENTS.md`, `README.md`, setup docs, decision docs, and evaluation playbooks describe Scrapling as the first path and define fallback boundaries

#### Scenario: Reusable site learning

- **WHEN** a Scrapling run validates or changes reusable knowledge for a site
- **THEN** the workflow records that learning under `sites/` or a report according to the existing Content Retrieval vs Platform/Page Analysis reporting rules
