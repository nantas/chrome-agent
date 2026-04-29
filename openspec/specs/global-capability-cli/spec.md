# global-capability-cli — Spec

## Purpose

Define the low-level explicit CLI contract for `chrome-agent`, including the first-class command surface, repo-backed dispatch model, repo resolution precedence, JSON-first result envelope, and its relationship to the global workflow skill.

## Requirements

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

### Requirement: Repo-backed execution authority

The CLI SHALL treat the target repository as the execution authority for `explore`, `fetch`, and `crawl`.

The global CLI SHALL only normalize input, resolve the repository, and dispatch into the repository-local workflow. Repository-local `AGENTS.md` and `openspec/specs/` SHALL remain authoritative for workflow routing and execution behavior.

#### Scenario: Repository-local dispatch

- **WHEN** `chrome-agent fetch <target>` or `chrome-agent explore <target>` is invoked
- **THEN** the global CLI SHALL dispatch the request into the resolved `repo://chrome-agent` repository
- **AND** the downstream execution SHALL read and follow the target repository `AGENTS.md`
- **AND** the global CLI SHALL not replace repository routing logic with a separate parallel ruleset

### Requirement: Repo resolution precedence

The CLI SHALL resolve the target repository using repo-registry first and environment fallback second.

Resolution precedence SHALL be:
1. explicit CLI override, if supplied
2. `repo://chrome-agent` resolved through the global repo-registry
3. `CHROME_AGENT_REPO` environment variable as fallback
4. failure with remediation guidance

#### Scenario: Registry-first resolution

- **WHEN** `repo://chrome-agent` is registered and resolves to an existing repository
- **THEN** the CLI SHALL use that path
- **AND** it SHALL not prefer `CHROME_AGENT_REPO` over the registry result

#### Scenario: Environment fallback resolution

- **WHEN** `repo://chrome-agent` is missing or invalid in repo-registry
- **AND** `CHROME_AGENT_REPO` points to an existing repository containing `AGENTS.md`
- **THEN** the CLI SHALL use `CHROME_AGENT_REPO` as fallback
- **AND** it SHALL report that fallback mode was used

#### Scenario: Repository resolution failure

- **WHEN** neither repo-registry nor `CHROME_AGENT_REPO` yields a valid target repository
- **THEN** the CLI SHALL fail before dispatch
- **AND** it SHALL return a remediation message telling the caller to register `repo://chrome-agent` or set `CHROME_AGENT_REPO`

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
- **AND** `workflow` SHALL identify whether the command executed `content_retrieval`, `platform_analysis`, `runtime_support`, or another explicit backend workflow
- **AND** `engine_path` SHALL summarize the actual engine or escalation path used for execution

#### Scenario: Structured partial failure

- **WHEN** a command completes with usable output but unresolved issues
- **THEN** the CLI SHALL emit the same result envelope
- **AND** `result` SHALL be `partial_success`
- **AND** `next_action` SHALL contain an explicit remediation suggestion grounded in the attempted workflow

### Requirement: Text rendering as optional view

The CLI SHALL support a human-readable text rendering, but that rendering SHALL be a view over the same underlying structured result contract.

#### Scenario: Text mode output

- **WHEN** the caller asks for text output or uses the default human-readable mode
- **THEN** the CLI SHALL render the same semantic result contained in the JSON envelope
- **AND** it SHALL not change success or failure semantics between text mode and JSON mode

### Requirement: Explore command routing

The `explore` command SHALL route into the repository-local Platform/Page Analysis backend rather than only a strategy-gap probe.

The repository-local analysis backend MAY inspect page structure, anti-crawl signals, strategy gaps, fallback evidence, and diagnostic artifacts.

#### Scenario: Explore command execution

- **WHEN** `chrome-agent explore <target>` is invoked
- **THEN** the CLI SHALL dispatch to a repository-local workflow that can perform deeper evidence collection and fallback-oriented diagnostics
- **AND** the result SHALL identify `workflow: platform_analysis`
- **AND** the result SHALL return any generated or referenced reports, screenshots, structure clues, or strategy artifacts

### Requirement: Fetch command routing

The `fetch` command SHALL route into the repository-local content retrieval workflow while preserving engine and strategy authority inside the repository.

#### Scenario: Fetch command execution

- **WHEN** `chrome-agent fetch <target>` is invoked
- **THEN** the CLI SHALL dispatch to the repository-local content retrieval workflow
- **AND** the downstream workflow SHALL remain free to choose the appropriate engine family according to repository rules

### Requirement: Relationship to global workflow skill

The CLI SHALL coexist with the global workflow skill as the backend execution surface for agent-first usage.

#### Scenario: Skill-backed CLI usage

- **WHEN** the global workflow skill invokes the CLI
- **THEN** the CLI SHALL remain the execution backend and source of truth for machine-readable results
- **AND** it SHALL not require the skill to re-implement repository routing or engine selection logic
