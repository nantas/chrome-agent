# engine-execution-contracts

## Purpose

Define engine invocation, lazy preflight and diagnostic evidence contracts for Explore and fetch.

## Requirements

### Requirement: obscura-stdout-acquisition
The Explore adapter SHALL invoke the installed Obscura CLI using supported fetch arguments and acquire raw HTML from stdout. It SHALL keep stderr separate, preserve the process outcome, and apply shared content admission before declaring success. It SHALL NOT pass the unsupported --output option or reuse previous output after failure.

#### Scenario: normal-stdout
- **WHEN** Obscura exits zero with normal HTML on stdout
- **THEN** the adapter SHALL save that HTML and select the engine only after admission succeeds
- **AND** diagnostic stderr SHALL NOT be appended to HTML

#### Scenario: rejected-or-absent-output
- **WHEN** the engine exits nonzero, produces no HTML, or returns a challenge page
- **THEN** the attempt SHALL fail with the respective execution/output/admission reason
- **AND** fallback SHALL continue without promoting stale HTML

### Requirement: cloakbrowser-preflight-before-dispatch
Explore and fetch SHALL resolve CloakBrowser through the existing preflight protocol and invoke the returned RESOLVED_CLI_PATH. They SHALL honor CLOAKBROWSER_MANAGED_ROOT and SHALL NOT maintain independently hardcoded Python paths. Installation behavior SHALL remain governed by the existing engine-registry contract.

#### Scenario: installed-custom-root
- **WHEN** preflight reports available with a configured custom managed root
- **THEN** execution SHALL use the reported executable without reinstalling

#### Scenario: missing-engine-lazy-install
- **WHEN** CloakBrowser is selected and its environment is missing
- **THEN** the adapter SHALL invoke the existing install-capable preflight before fetch
- **AND** a repaired environment SHALL be used for the original attempt

#### Scenario: failed-or-invalid-preflight
- **WHEN** preflight fails or omits a usable resolved executable
- **THEN** no fetch SHALL run and the attempt SHALL report preflight_failed with bounded diagnostic evidence
- **AND** any later fallback SHALL respect existing authorization requirements

### Requirement: explore-attempt-evidence
Explore SHALL preserve attempted engine order, stage, process exit code when a process ran, typed failure reason and available evidence paths. Its final engine_path SHALL be non-null and artifacts SHALL reference available diagnostic files. Pending manual fallback SHALL be labeled unexecuted. The result SHALL distinguish content rejection, unavailable engines, invalid invocation, and internal check/protocol failure.

#### Scenario: mixed-failure-chain
- **WHEN** Scrapling is challenged, Obscura rejects arguments and CloakBrowser fails preflight
- **THEN** the CLI SHALL preserve all three distinct reasons, a non-null engine_path and diagnostic artifact references
- **AND** it SHALL NOT describe the chain solely as a Cloudflare block

#### Scenario: pending-is-not-executed
- **WHEN** the last fallback requires user-authorized browser work
- **THEN** it SHALL remain pending, the CLI SHALL give a concrete next action, and no browser takeover SHALL occur automatically

#### Scenario: recovery-preserves-admission
- **WHEN** an engine executes correctly but returns challenge HTML, followed by an engine returning normal HTML
- **THEN** the first SHALL remain rejected and only the admitted later HTML SHALL enter discovery
- **AND** all existing scaffold, freeze and crawl gates SHALL remain in force
