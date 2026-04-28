# scrapling-cli-environment Specification

## Purpose

Define the canonical environment contract for locating, installing, verifying, and optionally persisting the Scrapling CLI used by this repository.

## Requirements
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
