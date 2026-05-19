# Governance Domain: Handoff — Merged Spec

## Source Attribution

| Source Spec | Type | Notes |
|------------|------|-------|
| `handoff-emission` | new | CLI internal failure handoff document generation |
| `handoff-gate` | new | SKILL.md Handoff Gate halting workflow on handoff_path |

---

# Handoff Specification

## Purpose

Define the handoff mechanism for CLI internal failures: when the CLI generates a handoff document, how it is structured and stored, and how the workflow skill's Handoff Gate interprets and acts on it.

---

## Requirements

### Requirement: internal-failure-handoff-trigger

The CLI SHALL generate a handoff document when a routed command (fetch / explore / crawl / scrape) encounters an internal failure.

Internal failure SHALL be defined as:
- Pipeline script non-zero exit (e.g., MediaWiki API pipeline exit code >= 10)
- Strategy lookup failure (no matching strategy for target URL)
- Strategy config validation error (frontmatter field missing, invalid value, content_profile ID not in registry)
- Engine preflight failure (Scrapling CLI unavailable after install attempt, Obscura binary missing, CloakBrowser missing)
- Conversion pipeline failure (sample conversion error, self-check unrecoverable failures)

External failure SHALL NOT trigger handoff generation:
- Target site HTTP 4xx or 5xx response
- Invalid URL format
- CHROME_AGENT_REPO not set or invalid
- Network timeout or DNS resolution failure
- Rate limiting (HTTP 429) from target site

#### Scenario: pipeline-exit-code-handoff

- **WHEN** a pipeline script (e.g., `scripts/pipeline/`) exits with a non-zero status code
- **THEN** the CLI SHALL generate a handoff document
- **THEN** the handoff SHALL include the exit code and stderr output

#### Scenario: strategy-gap-handoff

- **WHEN** the strategy registry contains no matching entry for the target domain
- **AND** the deep discovery pipeline also fails to generate a viable scaffold
- **THEN** the CLI SHALL generate a handoff document
- **THEN** the handoff SHALL include the domain, probe chain results, and API discovery output

#### Scenario: engine-preflight-handoff

- **WHEN** the Scrapling preflight fails after install attempt
- **OR** the Obscura preflight fails after install attempt
- **OR** CloakBrowser is not installed
- **THEN** the CLI SHALL generate a handoff document
- **THEN** the handoff SHALL include which engine failed and the preflight error output

#### Scenario: external-failure-no-handoff

- **WHEN** the target site returns HTTP 404, 500, or any non-2xx status
- **OR** the URL is malformed
- **OR** CHROME_AGENT_REPO is not set
- **THEN** the CLI SHALL NOT generate a handoff document
- **THEN** the CLI SHALL return the error as standard failure result

### Requirement: handoff-document-format

A handoff document SHALL be a Markdown file with the following structure:
- H1 heading: `# Handoff: <command> <target>`
- Context section: command, target URL, timestamp, repo_ref, run directory, strategy path (if applicable)
- What Went Wrong section: plain-language description of the failure
- Error Details section: exit code, error message, stderr excerpt, any relevant diagnostic output
- Run Artifacts section: absolute paths to manifest.json, logs, and any other relevant files
- Next Steps section: fixed instruction to "classify issue in chrome-agent repo" with placeholder for P-line / S-line / W-line classification

#### Scenario: handoff-context-fields

- **WHEN** a handoff is generated
- **THEN** the Context section SHALL include: `command`, `target`, `timestamp` (ISO 8601), `repo_ref`, `run_directory`, `strategy` (if applicable)
- **THEN** the `run_directory` SHALL be an absolute path
- **THEN** the `strategy` field SHALL be present only when a strategy file was involved in the failed operation

#### Scenario: handoff-error-details

- **WHEN** a handoff is generated
- **THEN** the Error Details section SHALL include the process exit code (if applicable)
- **THEN** the Error Details section SHALL include the error message or stderr output, truncated to at most 2000 characters
- **THEN** the Error Details section SHALL include the CLI command that was dispatched (for reproducibility)

#### Scenario: handoff-next-steps

- **WHEN** a handoff is generated
- **THEN** the Next Steps section SHALL contain the instruction: "This issue must be resolved in the chrome-agent repository."
- **THEN** the Next Steps section SHALL list steps: review run artifacts, classify issue (P/S/W-line), create openspec change proposal, implement fix, re-run original command
- **THEN** the Next Steps section SHALL include the original CLI command line for reproduction

### Requirement: handoff-storage-path

Handoff documents SHALL be stored under `outputs/handoffs/<run-tag>/handoff.md` within the chrome-agent repository.

The `<run-tag>` SHALL follow the same naming convention as existing run directories: `<timestamp>-<command>-<slug>`.

The `outputs/handoffs/` directory SHALL inherit the same .gitignore treatment as `outputs/` (excluded from version control).

#### Scenario: handoff-with-run-dir

- **WHEN** a handoff is generated for a command that already has a run directory
- **THEN** the handoff SHALL be created under `outputs/handoffs/<run-tag>/`
- **THEN** the handoff SHALL reference the run directory path in its Context section
- **THEN** the handoff SHALL NOT duplicate files already in the run directory

#### Scenario: handoff-without-run-dir

- **WHEN** a handoff is generated for a command that exited before creating a run directory (e.g., preflight failure)
- **THEN** the handoff SHALL still be written to `outputs/handoffs/<run-tag>/`
- **THEN** the run-tag SHALL still use the standard timestamp-command-slug format

### Requirement: handoff-in-result-payload

When a handoff is generated, the CLI JSON result SHALL include:

- `handoff_path`: absolute path to the generated handoff.md file (string)
- `handoff_summary`: one-line summary of the failure (string, max 200 chars)

These fields SHALL be absent when no handoff was generated.

#### Scenario: handoff-fields-present

- **WHEN** a handoff is generated
- **THEN** the CLI JSON result SHALL include `handoff_path`
- **THEN** the CLI JSON result SHALL include `handoff_summary`
- **THEN** the `result` field SHALL remain `"failure"` (not changed to a new value)
- **THEN** the `next_action` field SHALL contain: "The problem must be resolved in the chrome-agent repository. See handoff document at <handoff_path>."

#### Scenario: handoff-fields-absent

- **WHEN** no handoff is generated
- **THEN** the CLI JSON result SHALL NOT include `handoff_path` or `handoff_summary`
- **THEN** the `result` SHALL remain `"failure"` with `next_action` describing caller-side remediation

---

## Handoff Gate Requirements

### Requirement: handoff-gate-interpretation

The SKILL.md SHALL define a Handoff Gate that interprets CLI results containing a `handoff_path` field.

When the CLI result contains `handoff_path`:
1. The skill SHALL NOT proceed to any further workflow dispatch (fetch / explore / crawl / scrape)
2. The skill SHALL NOT attempt to interpret or re-route the failure as a different command
3. The skill SHALL NOT attempt to work around the problem by calling engines directly or bypassing the CLI
4. The skill SHALL present the handoff_path and handoff_summary to the user
5. The skill SHALL instruct the user to fix the issue in the chrome-agent repository before retrying

#### Scenario: handoff-gate-halts-workflow

- **WHEN** a CLI command returns a JSON result containing `handoff_path`
- **THEN** the skill SHALL recognize this as a chrome-agent-repo-bound failure
- **THEN** the skill SHALL stop all further workflow dispatch
- **THEN** the skill SHALL NOT attempt to re-run the same command with different parameters
- **THEN** the skill SHALL NOT attempt alternative fetching strategies outside the CLI backend

#### Scenario: handoff-gate-forbidden-workarounds

- **WHEN** a CLI result contains `handoff_path`
- **THEN** the skill SHALL NOT:
  - write a custom curl/wget/request script as a substitute
  - call chrome-cdp or chrome-devtools-mcp directly as a bypass
  - use the Scrapling CLI directly without going through the chrome-agent CLI
  - fabricate a strategy or workaround
- **THEN** the only allowed action is: present the handoff and stop

### Requirement: handoff-gate-presentation

The SKILL.md SHALL define a structured user-facing message when the Handoff Gate is triggered.

The message SHALL contain:
1. A halting notice: "工作流中断"
2. The failure summary from `handoff_summary`
3. The absolute path to the handoff document
4. An instruction to switch to the chrome-agent repository
5. The steps to follow in the chrome-agent repository (review handoff, classify issue, create change, fix, verify)
6. The original CLI command for reproduction

#### Scenario: handoff-presentation-format

- **WHEN** the Handoff Gate is triggered
- **THEN** the skill SHALL present the handoff to the user in a structured format
- **THEN** the preferred format SHALL be:

```
result: failure
handoff_path: <absolute path>
handoff_summary: <one-line summary>

Workflow interrupted. This problem belongs in the chrome-agent repository.

Handoff document: <handoff_path>

To fix:
1. Switch to the chrome-agent repository
2. Read the handoff document for full context
3. Classify the issue (P-line: pipeline / S-line: strategy / W-line: workflow)
4. Create an openspec change proposal
5. Implement the fix
6. Re-run the original command to verify

Original command: <CLI command that was run>
```

#### Scenario: handoff-with-additional-context

- **WHEN** the CLI result includes other fields beyond `handoff_path` and `handoff_summary` (e.g., `summary`, `artifacts`, `engine_path`)
- **THEN** the skill MAY include these in the presentation
- **THEN** the skill SHALL NOT re-order or re-interpret the fields
- **THEN** the handoff_path field SHALL always be presented prominently

### Requirement: handoff-gate-differing-failure-handling

The Handoff Gate SHALL distinguish between two types of failure results:

1. **Chrome-agent-repo-bound failures** (result contains `handoff_path`): Skill MUST halt and route to chrome-agent repo.
2. **Caller-side failures** (result = `"failure"`, no `handoff_path`): Skill MUST pass through the `next_action` field as the caller-side remediation.

#### Scenario: caller-side-failure-passthrough

- **WHEN** the CLI returns `result: "failure"` without `handoff_path`
- **THEN** the skill SHALL NOT trigger the Handoff Gate
- **THEN** the skill SHALL return the CLI result as-is (same behavior as current implementation)
- **THEN** the `next_action` field SHALL guide the caller on what to fix (e.g., set CHROME_AGENT_REPO, provide a valid URL)

#### Scenario: mixed-failure-resolution

- **WHEN** the CLI returns `result: "partial_success"` with `handoff_path`
- **THEN** the skill SHALL still trigger the Handoff Gate (any `handoff_path` presence triggers the gate)
- **THEN** the skill SHALL NOT accept partial results while chrome-agent-repo-bound issues remain unresolved
