# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-first-browser-workflow`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认本次 change 只修改既有 `scrapling-first-browser-workflow`，把验证后的默认抓取流程重排进 `AGENTS.md`，不新增 capability。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Default workflow ordering
The system SHALL express the default webpage grabbing workflow as one explicit operator flow that starts with task routing, defaults to Scrapling, and escalates only when verified fallback triggers are present.

#### Scenario: Default content retrieval
- **WHEN** the operator reads `AGENTS.md` for a normal webpage grabbing task
- **THEN** the documented flow first routes between `Content Retrieval` and `Platform/Page Analysis`, and then starts with Scrapling as the default grabbing path

#### Scenario: Scrapling path selection
- **WHEN** the task is already on the Scrapling path
- **THEN** the documented default flow maps common cases to the matching first fetcher or mode, including `get` for static or article pages, `fetch` for SPA or dynamic pages, `stealthy-fetch` for protected pages, and bulk or session variants only when those scopes are actually needed

#### Scenario: Stop without unnecessary escalation
- **WHEN** Scrapling produces content that satisfies the task
- **THEN** the workflow stops on Scrapling and does not escalate only because another browser tool could also complete the task

### Requirement: Fallback boundaries
The system SHALL document `chrome-devtools-mcp` and `chrome-cdp` as distinct fallback paths with different triggers, instead of describing them as interchangeable browser options.

#### Scenario: Diagnostic fallback trigger
- **WHEN** Scrapling output is incomplete, visually suspect, blocked, or requires DOM, accessibility, network, console, screenshot, or interaction evidence
- **THEN** the workflow escalates to `chrome-devtools-mcp` as the diagnostic and evidence path

#### Scenario: Live-tab continuity trigger
- **WHEN** the task must continue immediately on an already-open real Chrome tab, or approved authenticated state cannot be safely preserved through Scrapling
- **THEN** the workflow escalates to repo-local `chrome-cdp` as the live-session continuity path

#### Scenario: No interchangeable switching
- **WHEN** both fallback tools appear technically capable of completing the task
- **THEN** the workflow chooses between them only by session continuity needs versus diagnostic evidence needs, not by tool duplication alone

### Requirement: Authenticated read-only boundary
The system SHALL document authenticated and live-session runs as explicitly approved, read-only by default, and subject to immediate stop conditions when state continuity is lost.

#### Scenario: Approved authenticated target
- **WHEN** the task involves a logged-in page or authenticated tab
- **THEN** the workflow requires an explicit user-approved target page or tab before either Scrapling session reuse or `chrome-cdp` live-tab continuation is attempted

#### Scenario: Session reuse failure
- **WHEN** Scrapling session reuse redirects to a login flow, resets page state, or otherwise fails to preserve the approved authenticated context
- **THEN** the workflow records that failure, stops the Scrapling path for that session, and falls back to the approved `chrome-cdp` live tab if one exists

#### Scenario: Read-only default
- **WHEN** an authenticated run is executed
- **THEN** the workflow remains read-only unless the user explicitly broadens scope, and records any reset, redirect, logout, or write-action risk as failure rather than pushing through

### Requirement: Verification-aligned documentation
The system SHALL keep `AGENTS.md` aligned with the verified operating results already recorded in the repository, including the current X login-state finding.

#### Scenario: Verified X behavior
- **WHEN** `AGENTS.md` describes authenticated live-session routing
- **THEN** it reflects that Scrapling-first remains the opening move, but some sites such as `x.com` can require immediate `chrome-cdp` fallback after session reuse fails to preserve the current authenticated tab state

#### Scenario: No stale default wording
- **WHEN** the workflow text is reorganized
- **THEN** the document no longer leaves any stale wording that implies `chrome-devtools-mcp` or `chrome-cdp` is the default first path for ordinary webpage grabbing

## ADDED Requirements

## REMOVED Requirements

## RENAMED Requirements
