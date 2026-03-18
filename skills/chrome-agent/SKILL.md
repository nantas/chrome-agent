---
name: chrome-agent
description: Dispatch webpage extraction requests into the local chrome-agent repository through codex-agent first and repo-agent second, then report result status and artifact paths back to the parent session.
---

# Chrome Agent Global Skill

## Purpose

Use this skill when you want a globally installed entrypoint that forwards webpage extraction work into the local `chrome-agent` repository instead of re-implementing the workflow in the current session.

This skill is a thin dispatcher. It does not clone repositories, install dependencies, or embed site-specific extraction logic.

## Required Preconditions

Before runtime, verify:

- `~/.agents/skills/codex-agent/` exists, or `~/.agents/skills/repo-agent/` exists
- `CHROME_AGENT_REPO` is defined
- `CHROME_AGENT_REPO` is an absolute path to a local repository
- `CHROME_AGENT_REPO/AGENTS.md` exists

If any requirement fails, stop and report `failure` with the missing requirement.

## Dispatcher Priority

Use:

1. `codex-agent` first
2. `repo-agent` only when `codex-agent` is unavailable

Do not ask the user to choose unless they explicitly want to override this order.

## Install Notes

The repository-owned source for this skill should live at:

- `skills/chrome-agent/SKILL.md`

The global install destination should be:

- `~/.agents/skills/chrome-agent/`

Before any install or update action:

- check whether `~/.agents/skills/chrome-agent/` already exists
- check whether `CHROME_AGENT_REPO` is already set in the current environment or shell config
- do not overwrite either one silently
- if an existing skill or conflicting environment variable is found, ask for explicit confirmation before making persistent changes

## Runtime Procedure

### Step 1: Validate dispatcher skills

Check for:

- `~/.agents/skills/codex-agent/`
- `~/.agents/skills/repo-agent/`

If both are missing, return:

```text
result: failure
target: <user target or unknown>
summary: Neither codex-agent nor repo-agent is installed under ~/.agents/skills.
artifacts:
next_action: Install codex-agent or repo-agent, then run this request again.
```

### Step 2: Validate repository path

Resolve `CHROME_AGENT_REPO`.

Validation rules:

- it must be non-empty
- it must be absolute
- it must exist
- it must contain `AGENTS.md`

If validation fails, return:

```text
result: failure
target: <user target or unknown>
summary: CHROME_AGENT_REPO is missing or does not point to a valid chrome-agent repository.
artifacts:
next_action: Set CHROME_AGENT_REPO to the local chrome-agent repository path and retry.
```

### Step 3: Forward the task

Forward the user's request into `CHROME_AGENT_REPO` and require the downstream agent to:

- read the repository `AGENTS.md`
- execute the webpage extraction task according to the repository workflow
- choose `Content Retrieval` vs `Platform/Page Analysis` based on the repository rules
- return the final result in the required output shape

### Step 4: Required downstream output

Require the downstream session to return:

- `result`
- `target`
- `summary`
- `artifacts`
- `next_action`

Preferred text shape:

```text
result: success
target: https://example.com/post/123
summary: Extracted the article content and saved the output.
artifacts:
- /abs/path/to/reports/example.md
- /abs/path/to/output/article.md
next_action: none
```

### Step 5: Return to the parent session

Pass through the downstream result when it is already clear and complete.

If the downstream output is incomplete, provide a conservative summary and label any inferred statements as inference. Do not claim success without evidence from the downstream run.

## Forwarding Prompt Contract

When dispatching, include instructions equivalent to:

```text
Read AGENTS.md in the target repository and execute this webpage extraction request according to the repository workflow.

User request:
<verbatim user request>

Return the final outcome in this shape:
result: <success|partial_success|failure>
target: <url or page identifier>
summary: <brief result summary>
artifacts:
- <absolute path>
next_action: <none or recommended next step>
```

## Notes

- Prefer direct extraction requests to flow through the repository's `Content Retrieval` route.
- Do not silently widen scope into debugging or evidence-heavy analysis unless the downstream repository workflow decides that the prompt requires it.
- Preserve artifact paths exactly as returned by the downstream repository.
