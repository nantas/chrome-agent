# global-workflow-skill — Spec

## Purpose

Define the global `chrome-agent` workflow skill as the recommended agent-facing entry above the repo-backed CLI, including intent routing, doctor-based preflight, runtime boundaries, and structured result passthrough.

## Requirements

### Requirement: Agent-first primary entry

The system SHALL define a global `chrome-agent` workflow skill as the recommended primary entry for agent-driven usage.

The skill SHALL sit above the repo-backed CLI and SHALL provide workflow intent routing rather than direct site extraction logic.

#### Scenario: Agent-facing entry recommendation

- **WHEN** an operator reads the repository's installation or usage guidance for agent-driven work
- **THEN** the guidance SHALL present the global `chrome-agent` skill as the recommended primary entry
- **AND** it SHALL describe the repo-backed `chrome-agent` CLI as the backend execution surface used by the skill

### Requirement: Intent-to-command routing

The global workflow skill SHALL translate user intent into one of the repository-supported CLI workflows.

The routing contract SHALL be:
- content retrieval, 正文抽取, bare URL fetch, concise failure explanation -> `chrome-agent fetch`
- analysis, debugging, evidence collection, structure investigation, anti-crawl rule inspection, reproduction -> `chrome-agent explore`
- bounded multi-page traversal, list expansion, batch gap fill -> `chrome-agent crawl`

#### Scenario: Content retrieval routing

- **WHEN** the user asks to get, read, fetch, or extract page content
- **THEN** the skill SHALL invoke `chrome-agent fetch`
- **AND** it SHALL not require the upstream agent to decide between repository workflows first

#### Scenario: Platform analysis routing

- **WHEN** the user asks for analysis, debugging, evidence, structure, rules, or reproduction
- **THEN** the skill SHALL invoke `chrome-agent explore`
- **AND** it SHALL treat `explore` as the CLI backend for Platform/Page Analysis

#### Scenario: Crawl-or-explore routing

- **WHEN** the user asks for bounded multi-page traversal or batch completion work
- **THEN** the skill SHALL prefer `chrome-agent crawl` when the request is already shaped as a bounded traversal task
- **AND** it SHALL fall back to `chrome-agent explore` first when strategy coverage or crawl eligibility is not yet established

### Requirement: CLI-backed preflight

The global workflow skill SHALL use the repo-backed CLI as its only supported execution backend.

Before routing user work, the skill SHALL validate backend readiness through `chrome-agent doctor --format json`, using the CLI's env-first repository resolution contract.

#### Scenario: Backend ready via env default

- **WHEN** `chrome-agent doctor --format json` reports that `CHROME_AGENT_REPO` resolves to a valid repository
- **THEN** the skill SHALL continue to the routed workflow command
- **AND** it SHALL preserve the resolved repository and backend remediation details from the CLI

#### Scenario: Backend not ready due to missing or invalid env

- **WHEN** the CLI doctor result reports `failure` because `CHROME_AGENT_REPO` is missing or invalid
- **THEN** the skill SHALL stop before dispatching `fetch`, `explore`, or `crawl`
- **AND** it SHALL return the doctor-provided remediation instead of improvising a non-CLI fallback path
- **AND** it SHALL not silently depend on repo-registry as the default repository source

### Requirement: No legacy dispatcher runtime

The global workflow skill SHALL NOT rely on `repo-agent`, `codex-agent`, or any equivalent prompt-forwarding runtime as its primary execution path.

#### Scenario: Skill runtime description

- **WHEN** the skill definition, installation guidance, or governance docs describe the skill runtime
- **THEN** they SHALL describe the skill as invoking the repo-backed CLI
- **AND** they SHALL not describe `repo-agent` or `codex-agent` as required or preferred runtime dependencies

### Requirement: Structured result passthrough

The global workflow skill SHALL derive its final user-facing result from the CLI JSON contract.

#### Scenario: CLI result passthrough

- **WHEN** a routed CLI command completes
- **THEN** the skill SHALL use the CLI JSON result as the source of truth for `result`, `summary`, `artifacts`, and remediation
- **AND** it MAY re-render that result for the caller
- **AND** it SHALL not claim success if the backend CLI result does not provide evidence for it
- **AND** it SHALL preserve the CLI's env-first repository resolution semantics in any surfaced `repo_ref` or remediation text
