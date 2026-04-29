# install-chain — Spec

## Purpose

Define the installation and runtime support chain for the global `chrome-agent` launcher, the workflow skill that sits above it, repo-registry-first resolution, `CHROME_AGENT_REPO` fallback compatibility, and `doctor` coverage.

## Requirements

### Requirement: Thin global launcher model

The system SHALL continue to distribute `chrome-agent` as a thin global launcher rather than as a standalone full runtime package.

The launcher SHALL remain the execution backend used directly by shell callers and indirectly by the global workflow skill.

#### Scenario: Launcher responsibility boundary

- **WHEN** the global launcher is installed
- **THEN** it SHALL provide command discovery and dispatch only
- **AND** it SHALL not duplicate the repository's workflow guidance, AGENTS routing model, or site-specific extraction logic

### Requirement: Global runtime placement

The system SHALL install the launcher using the existing OrbitOS-style global runtime pattern.

This SHALL include:
- a global runtime script under `~/.agents/scripts/`
- a user-invocable shim under a PATH-visible user bin directory

#### Scenario: Runtime script location

- **WHEN** the install chain provisions the global launcher
- **THEN** the runtime implementation SHALL be placed under `~/.agents/scripts/`
- **AND** the caller-facing executable SHALL be available from a PATH-visible location without requiring the user to `cd` into the repository

### Requirement: Registry-first installation assumptions

The install chain SHALL assume repo-registry is the primary long-term repository locator.

#### Scenario: Install without explicit repo path

- **WHEN** a caller installs or invokes the CLI without a direct repository path override
- **THEN** the install chain SHALL first attempt to resolve `repo://chrome-agent` from repo-registry
- **AND** it SHALL only consult `CHROME_AGENT_REPO` if registry resolution fails

### Requirement: Environment fallback compatibility

The install chain SHALL preserve `CHROME_AGENT_REPO` as a runtime compatibility fallback.

#### Scenario: Legacy environment fallback

- **WHEN** the caller environment still defines `CHROME_AGENT_REPO`
- **AND** repo-registry resolution fails
- **THEN** the install chain SHALL accept the environment variable as fallback
- **AND** it SHALL not promote that fallback as the primary long-term contract

### Requirement: Doctor command coverage

The `doctor` command SHALL remain the backend readiness check used by both direct CLI callers and the global workflow skill.

At minimum, `doctor` SHALL check:
- launcher availability
- repo-registry resolution for `repo://chrome-agent`
- `CHROME_AGENT_REPO` fallback availability when needed
- repository shape (`AGENTS.md` exists)
- Scrapling CLI preflight status delegated from repository-local logic when relevant

#### Scenario: Healthy doctor result

- **WHEN** all required runtime dependencies are available
- **THEN** `chrome-agent doctor` SHALL return `success`
- **AND** it SHALL identify the resolved repository path and runtime readiness state

#### Scenario: Broken doctor result

- **WHEN** a required dependency is missing or invalid
- **THEN** `chrome-agent doctor` SHALL return `failure` or `partial_success`
- **AND** it SHALL point to the failing stage and the manual remediation required

#### Scenario: Skill uses doctor as preflight

- **WHEN** the global workflow skill prepares to dispatch user work
- **THEN** it SHALL be able to rely on `chrome-agent doctor --format json` as the authoritative backend readiness check
- **AND** the install guidance SHALL describe that dependency explicitly

### Requirement: Fail before hidden dispatch

The install chain SHALL stop before hidden dispatch if launcher or repository resolution prerequisites are not satisfied.

#### Scenario: Missing repository mapping

- **WHEN** no valid repository mapping can be resolved
- **THEN** the CLI SHALL fail before attempting downstream execution
- **AND** it SHALL not improvise a current-working-directory fallback

### Requirement: Workflow skill installation path

The install chain SHALL document and support the global workflow skill as the recommended agent-facing installation path on top of the CLI backend.

#### Scenario: Agent-facing installation guidance

- **WHEN** Phase 5+ installation guidance is consulted for agent usage
- **THEN** the guidance SHALL describe installing or updating the global workflow skill in addition to the CLI backend
- **AND** it SHALL make clear that the skill delegates to the CLI rather than replacing it

### Requirement: No legacy dispatcher dependency

The install chain SHALL NOT require `repo-agent`, `codex-agent`, or equivalent prompt-forwarding dispatcher runtimes as part of the supported installation path.

#### Scenario: Supported dependency inventory

- **WHEN** the install contract lists runtime prerequisites
- **THEN** it SHALL include the CLI launcher, repository resolution contract, and repository-local prerequisites
- **AND** it SHALL not include `repo-agent` or `codex-agent` as required workflow dependencies
