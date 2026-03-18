# Chrome Agent Global Skill Design

## Goal

Design a globally installable `chrome-agent` skill under `~/.agents/skills` that dispatches webpage extraction tasks into the local `chrome-agent` repository and returns status plus artifact paths to the calling session.

## Problem

The current repository documents the browser extraction workflow, but there is no global skill that lets a user trigger that workflow from any session through a single prompt. The missing piece is a thin global entrypoint that:

- checks for the required global dispatcher skills
- locates the local `chrome-agent` repository through an environment variable
- forwards the extraction prompt into that repository
- reports the downstream result, artifact paths, and failures back to the parent session

This should not become an installer for unrelated dependencies or a second extraction framework.

## Requirements

### Functional

- The global skill name is `chrome-agent`.
- The source of truth for the skill lives in this repository.
- The installed destination is `~/.agents/skills/chrome-agent/`.
- The skill checks whether `codex-agent` or `repo-agent` exists under `~/.agents/skills`.
- The skill uses `codex-agent` first and falls back to `repo-agent`.
- The skill reads the target repository path from `CHROME_AGENT_REPO`.
- The skill forwards webpage extraction prompts to the repository at `CHROME_AGENT_REPO`.
- The downstream repository executes according to its own `AGENTS.md`.
- The parent session receives:
  - `result`
  - `target`
  - `summary`
  - `artifacts`
  - `next_action`

### Installation

- A user should be able to start installation with a single prompt.
- Installation checks whether `~/.agents/skills/chrome-agent` already exists.
- Installation does not overwrite an existing skill silently.
- Installation checks whether `CHROME_AGENT_REPO` is already defined.
- If `CHROME_AGENT_REPO` exists and differs, the installer must ask before replacing it.
- If the user allows it, the installer may append the environment variable to the active shell config.

### Non-Goals

- Installing `codex-agent`
- Installing `repo-agent`
- Cloning the `chrome-agent` repository
- Re-implementing extraction logic inside the global skill
- Hard-coding site-specific extraction behavior into the global skill

## Recommended Architecture

Use a thin dispatcher skill. The global `chrome-agent` skill should only do preflight checks, prompt forwarding, and result normalization. Actual browser workflow decisions stay in the target repository.

### Why this approach

- It preserves a single source of workflow truth in the `chrome-agent` repository.
- It avoids splitting extraction rules between the global skill and the repo.
- It matches the repository goal of using `codex-agent` as the primary entrypoint.
- It keeps the global skill stable even if the repository workflow evolves.

## Alternatives Considered

### Option 1: `codex-agent` primary, `repo-agent` fallback

Recommended.

Pros:

- aligns with repository guidance that `codex-agent` is the primary entrypoint
- preserves a fallback when `codex-agent` is unavailable
- keeps the user-facing invocation simple

Cons:

- requires two dispatcher paths
- requires slightly more output normalization logic

### Option 2: `codex-agent` only

Pros:

- simpler implementation
- fewer parsing branches

Cons:

- loses the fallback path the user explicitly wants
- makes the global skill less portable across environments

### Option 3: force the user to choose the dispatcher each time

Pros:

- most explicit
- easiest to debug manually

Cons:

- worse prompt ergonomics
- does not match the intended one-line usage

## Installation Design

### Source Layout

Store the skill in this repository at:

- `skills/chrome-agent/SKILL.md`

Optional helper assets may live beside it, but the skill entrypoint remains `SKILL.md`.

### Install Destination

- `~/.agents/skills/chrome-agent/`

### Install Flow

1. Check whether `~/.agents/skills/chrome-agent/` already exists.
2. If it exists, report that state and require explicit confirmation before overwriting.
3. Copy the repo skill directory into the global skills directory only after confirmation when needed.
4. Check whether `CHROME_AGENT_REPO` is already defined in the current environment or shell config.
5. If undefined, offer to append the current repository path.
6. If defined and equal to the current repository path, report it as already configured.
7. If defined and different, require explicit confirmation before replacing it.

## Environment Variable Contract

Use:

- `CHROME_AGENT_REPO=/absolute/path/to/chrome-agent`

Validation rules:

- the value must be an absolute path
- the path must exist
- the path should contain `AGENTS.md`

If validation fails, installation and runtime should stop with a clear error.

## Runtime Dispatch Design

### Preflight

At invocation time, the global skill should:

1. check for `~/.agents/skills/codex-agent/`
2. if missing, check for `~/.agents/skills/repo-agent/`
3. fail if both are missing
4. resolve `CHROME_AGENT_REPO`
5. verify the path exists and looks like the target repository

### Dispatch Strategy

Use `codex-agent` when available. If not, use `repo-agent`.

The forwarded instruction should explicitly require the downstream session to:

- read the target repository `AGENTS.md`
- execute the requested webpage extraction task
- follow repository workflow routing
- report status and artifact paths back in a stable format

### Prompt Shape

The forwarded prompt should contain:

- the user request verbatim
- a requirement to follow the repository `AGENTS.md`
- a requirement to return:
  - `result`
  - `target`
  - `summary`
  - `artifacts`
  - `next_action`

## Return Format

The global skill should prefer stable human-readable text, for example:

```text
result: success
target: https://example.com/post/123
summary: Extracted the article content and saved the run output.
artifacts:
- /abs/path/to/reports/example.md
- /abs/path/to/output/article.md
next_action: none
```

If the downstream agent is ambiguous, the global skill may summarize the output, but it must not fabricate success.

## Error Handling

### Missing Dispatcher Skills

Return `failure` with a direct explanation that neither `codex-agent` nor `repo-agent` is installed globally.

### Missing or Invalid Repository Path

Return `failure` when:

- `CHROME_AGENT_REPO` is missing
- the path does not exist
- the path does not contain `AGENTS.md`

### Install Conflicts

Do not overwrite an existing global skill or conflicting environment variable without explicit user confirmation.

### Downstream Execution Failure

Return `partial_success` or `failure` using the downstream error details and recommended next step.

### Ambiguous Downstream Output

Return a clearly labeled inferred summary and mark the uncertainty.

## Testing Scope

Minimum validation scenarios:

1. Fresh install with no existing skill and no environment variable
2. Re-install with an existing global `chrome-agent` skill
3. Install with an existing conflicting `CHROME_AGENT_REPO`
4. Runtime dispatch through `codex-agent`
5. Runtime fallback through `repo-agent`
6. Runtime failure when both dispatcher skills are missing
7. Runtime failure when `CHROME_AGENT_REPO` is invalid

## Decision

Adopt a thin global dispatcher skill named `chrome-agent`, stored in this repository and installed into `~/.agents/skills/chrome-agent/`, using `CHROME_AGENT_REPO` for repository discovery, `codex-agent` as the primary dispatcher, and `repo-agent` as fallback.
