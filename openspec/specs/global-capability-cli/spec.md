# global-capability-cli — Spec

## Purpose

Define the formal external CLI contract for `chrome-agent`, including the first-class command surface, repo-backed dispatch model, repo resolution precedence, JSON-first result envelope, and retirement of the historical global skill as the primary entry path.

## Requirements

### Requirement: Global command surface

The system SHALL expose `chrome-agent` as the formal global CLI entrypoint for this repository's external capabilities.

The CLI SHALL define these first-class commands:
- `explore`
- `fetch`
- `crawl`
- `doctor`
- `clean`

#### Scenario: Command inventory

- **WHEN** an operator or agent invokes `chrome-agent --help`
- **THEN** the CLI SHALL present the five first-class commands above
- **AND** it SHALL not require the caller to invoke the removed `skills/chrome-agent` dispatcher as the primary path

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

#### Scenario: Structured success result

- **WHEN** a command completes successfully
- **THEN** the CLI SHALL emit a machine-readable result object with all fields above
- **AND** `result` SHALL be `success`
- **AND** `repo_ref` SHALL identify the resolved repository reference used for execution

#### Scenario: Structured partial failure

- **WHEN** a command completes with usable output but unresolved issues
- **THEN** the CLI SHALL emit the same result envelope
- **AND** `result` SHALL be `partial_success`
- **AND** `next_action` SHALL contain an explicit remediation suggestion

### Requirement: Text rendering as optional view

The CLI SHALL support a human-readable text rendering, but that rendering SHALL be a view over the same underlying structured result contract.

#### Scenario: Text mode output

- **WHEN** the caller asks for text output or uses the default human-readable mode
- **THEN** the CLI SHALL render the same semantic result contained in the JSON envelope
- **AND** it SHALL not change success or failure semantics between text mode and JSON mode

### Requirement: Explore command routing

The `explore` command SHALL route into a repository-local exploratory workflow rather than a deterministic fetch-only path.

#### Scenario: Explore command execution

- **WHEN** `chrome-agent explore <target>` is invoked
- **THEN** the CLI SHALL dispatch to a repository-local workflow that may inspect page structure, anti-crawl signals, and strategy gaps
- **AND** the result SHALL return any generated or referenced reports or strategy artifacts

### Requirement: Fetch command routing

The `fetch` command SHALL route into the repository-local content retrieval workflow while preserving engine and strategy authority inside the repository.

#### Scenario: Fetch command execution

- **WHEN** `chrome-agent fetch <target>` is invoked
- **THEN** the CLI SHALL dispatch to the repository-local content retrieval workflow
- **AND** the downstream workflow SHALL remain free to choose the appropriate engine family according to repository rules

### Requirement: Decommission old global skill as primary entry

The system SHALL retire `skills/chrome-agent` as a formal primary entrypoint once the global CLI is introduced.

#### Scenario: Primary entry migration

- **WHEN** Phase 5 is implemented
- **THEN** the documented primary external entry SHALL be the global `chrome-agent` CLI
- **AND** any historical skill-based path SHALL be treated as removed or superseded rather than co-equal
