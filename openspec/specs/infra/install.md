# Infra Domain: Install — Merged Spec

## Source Attribution

| Source Spec | Type | Notes |
|------------|------|-------|
| `install-chain` | frozen | Global launcher model, runtime placement, doctor coverage, env-first resolution |
| `scrapling-cli-environment` | frozen | Scrapling CLI path contract, isolated install, shell confirmation boundary |

---

# Install Specification

## Purpose

Define the installation and runtime support chain for the global `chrome-agent` launcher, the workflow skill that sits above it, env-first repository resolution, and the canonical environment contract for the Scrapling CLI.

---

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

### Requirement: Environment-default installation assumptions

The install chain SHALL treat `CHROME_AGENT_REPO` as the default runtime prerequisite for the global workflow skill and the repo-backed CLI.

#### Scenario: Install without explicit repo path

- **WHEN** a caller installs or invokes the CLI without a direct repository path override
- **THEN** the install chain SHALL expect `CHROME_AGENT_REPO` to identify the local chrome-agent repository
- **AND** it SHALL not describe repo-registry as the default runtime locator for high-frequency usage

### Requirement: Doctor command coverage

The `doctor` command SHALL remain the backend readiness check used by both direct CLI callers and the global workflow skill.

At minimum, `doctor` SHALL check:
- launcher availability
- `CHROME_AGENT_REPO` default availability
- repository shape (`AGENTS.md` exists)
- Scrapling CLI preflight status delegated from repository-local logic when relevant

#### Scenario: Healthy doctor result

- **WHEN** all required runtime dependencies are available
- **THEN** `chrome-agent doctor` SHALL return `success`
- **AND** it SHALL identify the resolved repository path and runtime readiness state

#### Scenario: Broken doctor result

- **WHEN** `CHROME_AGENT_REPO` is missing or invalid and no explicit `--repo` override is provided
- **THEN** `chrome-agent doctor` SHALL return `failure`
- **AND** it SHALL point to the missing or invalid env stage and the remediation required

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
- **AND** it SHALL make clear that `CHROME_AGENT_REPO` is the default runtime prerequisite
- **AND** it SHALL describe explicit `--repo` overrides as the non-default alternative path

### Requirement: No legacy dispatcher dependency

The install chain SHALL NOT require `repo-agent`, `codex-agent`, or equivalent prompt-forwarding dispatcher runtimes as part of the supported installation path.

#### Scenario: Supported dependency inventory

- **WHEN** the install contract lists runtime prerequisites
- **THEN** it SHALL include the CLI launcher, repository resolution contract, and repository-local prerequisites
- **AND** it SHALL not include `repo-agent` or `codex-agent` as required workflow dependencies

---

## Scrapling CLI Environment Requirements

### Requirement: Scrapling CLI path contract

The system SHALL define `SCRAPLING_CLI_PATH` as the canonical environment variable for locating the Scrapling executable used by this repository.

Git-tracked repository files SHALL reference `SCRAPLING_CLI_PATH` or an equivalent environment-variable-based launcher, and SHALL NOT embed host-user-specific absolute Scrapling paths.

#### Scenario: Repository-tracked configuration

- **WHEN** a git-tracked configuration or setup document refers to the Scrapling executable
- **THEN** it SHALL use `SCRAPLING_CLI_PATH` or an environment-variable-resolving wrapper
- **AND** it SHALL NOT hardcode paths such as `/Users/<user>/.cache/chrome-agent-scrapling/bin/scrapling`

#### Scenario: Missing environment variable

- **WHEN** `SCRAPLING_CLI_PATH` is unset at runtime
- **THEN** the repository workflow SHALL treat the Scrapling CLI as not yet configured
- **AND** it SHALL continue to the install-assurance and confirmation flow defined by this capability

### Requirement: Default isolated install contract

The system SHALL use an isolated Scrapling installation rooted under the current user's home cache directory as the default managed installation.

The default executable location SHALL be `$HOME/.cache/chrome-agent-scrapling/bin/scrapling` unless the user intentionally chooses another path.

#### Scenario: Default install target

- **WHEN** the workflow needs to ensure Scrapling is installed and the user has not supplied an override path
- **THEN** it SHALL provision or verify an isolated environment under `$HOME/.cache/chrome-agent-scrapling`
- **AND** it SHALL treat `$HOME/.cache/chrome-agent-scrapling/bin/scrapling` as the default resolved value for `SCRAPLING_CLI_PATH`

#### Scenario: Existing managed install

- **WHEN** the default isolated install already exists and the executable is runnable
- **THEN** the workflow SHALL reuse that install
- **AND** it SHALL NOT reinstall Scrapling solely because the CLI is already present

### Requirement: Install assurance before workflow execution

The system SHALL ensure that the Scrapling CLI is available before any Scrapling-first workflow execution continues.

Availability SHALL be determined by a runnable `SCRAPLING_CLI_PATH` target or an equivalent verified managed install.

#### Scenario: CLI unavailable before task execution

- **WHEN** a workflow requires Scrapling and the resolved CLI path is missing or not executable
- **THEN** the system SHALL first attempt to ensure the CLI is installed in the managed environment
- **AND** it SHALL verify availability before returning to the original workflow

#### Scenario: Install assurance fails

- **WHEN** the system cannot make the Scrapling CLI available
- **THEN** it SHALL stop before claiming Scrapling-first execution can proceed
- **AND** it SHALL report the failure stage and the remaining manual prerequisite

### Requirement: Shell environment confirmation boundary

The system SHALL require explicit user confirmation before making persistent shell-environment writes for `SCRAPLING_CLI_PATH`.

Persistent shell writes SHALL include appending or modifying exports in `/Users/nantas-agent/.zshenv`.

#### Scenario: Environment variable missing after install

- **WHEN** Scrapling is installed or verified but `SCRAPLING_CLI_PATH` is not persistently configured
- **THEN** the workflow SHALL ask the user whether to add the environment variable to `/Users/nantas-agent/.zshenv`
- **AND** it SHALL default to no persistent write until the user explicitly confirms

#### Scenario: Environment variable already correct

- **WHEN** `/Users/nantas-agent/.zshenv` already exports `SCRAPLING_CLI_PATH` with the expected executable path
- **THEN** the workflow SHALL report that the persistent shell configuration is already correct
- **AND** it SHALL NOT rewrite the file

#### Scenario: Existing conflicting environment variable

- **WHEN** `SCRAPLING_CLI_PATH` is already defined with a different value than the managed install path
- **THEN** the workflow SHALL treat the mismatch as a conflict
- **AND** it SHALL ask for explicit confirmation before replacing or appending shell configuration
