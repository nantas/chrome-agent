# Specification Delta

## Capability 对齐（已确认）

- Capability: `handoff-emission`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: CLI 在内部失败场景自动生成 handoff.md 文档，包含完整上下文、错误详情与 run artifacts 引用路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

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

- **WHEN** a pipeline script (e.g., `mediawiki-api-extract`) exits with a non-zero status code
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
