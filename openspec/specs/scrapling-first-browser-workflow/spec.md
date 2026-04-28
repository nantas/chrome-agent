> **Status**: Superseded by [`agents-governance`](../agents-governance/spec.md) as of 2026-04-28.
> The operational routing rules originally defined here are now part of the agents-governance capability.
> This document is preserved for historical reference.

# scrapling-first-browser-workflow Specification

## Purpose

Define the repository's default webpage grabbing workflow around a Scrapling-first path, explicit fallback boundaries, authenticated read-only constraints, and the documentation and verification rules that keep the workflow auditable.

## Requirements

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

### Requirement: Verification-aligned documentation

The system SHALL keep `AGENTS.md` aligned with the verified operating results already recorded in the repository, including the current X login-state finding.

#### Scenario: Verified X behavior

- **WHEN** `AGENTS.md` describes authenticated live-session routing
- **THEN** it reflects that Scrapling-first remains the opening move, but some sites such as `x.com` can require immediate `chrome-cdp` fallback after session reuse fails to preserve the current authenticated tab state

#### Scenario: No stale default wording

- **WHEN** the workflow text is reorganized
- **THEN** the document no longer leaves any stale wording that implies `chrome-devtools-mcp` or `chrome-cdp` is the default first path for ordinary webpage grabbing
