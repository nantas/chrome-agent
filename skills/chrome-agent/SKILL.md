---
name: chrome-agent
description: Agent-first workflow skill for chrome-agent. Uses `chrome-agent doctor --format json` as preflight, then routes intent to the repo-backed CLI backend.
---

# Chrome Agent Workflow Skill

Use this skill as the recommended agent-facing entry for `chrome-agent`.

The skill is intent-facing. It does not implement scraping, crawl rules, or fallback logic itself. The only supported execution backend is the repo-backed `chrome-agent` CLI.

## Backend Contract

Always run backend preflight first:

```bash
chrome-agent doctor --format json
```

Interpret the doctor result as the source of truth:

- If `result` is `success`, continue.
- If `result` is `failure`, stop.
- If `result` is `partial_success`, treat it as blocking for workflow dispatch and stop unless the doctor output clearly marks all failed checks as non-blocking.

When stopping, return the doctor-provided remediation instead of inventing a non-CLI fallback.

Required result fields to preserve from doctor:

- `result`
- `summary`
- `artifacts`
- `next_action`
- `repo_ref`
- `workflow`
- `engine_path`

## Intent Routing

After doctor succeeds, route user intent to exactly one CLI workflow backend.

### Route to `fetch`

Use:

- content retrieval
- 正文抽取
- bare URL fetch
- concise failure explanation
- read/get/extract page content

Command:

```bash
chrome-agent fetch <target> --format json
```

### Route to `explore`

Use:

- analysis
- debugging
- evidence collection
- structure investigation
- anti-crawl rule inspection
- reproduction
- strategy coverage questions

Command:

```bash
chrome-agent explore <target> --format json
```

Treat `explore` as the CLI backend for Platform/Page Analysis.

### Route to `crawl`

Use:

- bounded multi-page traversal
- list expansion
- batch gap fill
- strategy-guided multi-page collection

Command:

```bash
chrome-agent crawl <target> --format json
```

If the request is not yet clearly bounded by declared strategy coverage, prefer `explore` first and return its remediation.

## Result Packaging

For routed commands, treat the CLI JSON result as the only source of truth.

Return or re-render these fields without changing their meaning:

- `result`
- `command`
- `target`
- `repo_ref`
- `summary`
- `artifacts`
- `next_action`
- `workflow`
- `engine_path`

Packaging rules:

- Do not claim success when the CLI returned `partial_success` or `failure`.
- Do not rewrite the backend workflow, engine path, or remediation into a conflicting interpretation.
- You may summarize the result for readability, but preserve artifact paths exactly.
- If the CLI reports a strategy gap, preflight issue, or fallback recommendation, surface that as-is.

Preferred final shape:

```text
result: <success|partial_success|failure>
command: <fetch|explore|crawl|doctor>
target: <url or runtime>
repo_ref: <repo://chrome-agent|path:...|env:CHROME_AGENT_REPO>
summary: <brief backend-grounded summary>
artifacts:
- <absolute path>
next_action: <none or remediation>
workflow: <content_retrieval|platform_analysis|runtime_support>
engine_path: <backend path summary>
```

## Runtime Boundaries

- Do not depend on `repo-agent`, `codex-agent`, or any other prompt-forwarding runtime.
- Do not re-implement repository routing, engine selection, strategy matching, or fallback escalation inside the skill.
- Do not bypass `chrome-agent doctor --format json`.
- Do not treat the skill as a standalone scraper runtime; it is a CLI-backed orchestration layer only.

## Install Notes

Repository source of truth:

- `skills/chrome-agent/SKILL.md`

Recommended global install destination:

- `~/.agents/skills/chrome-agent/`

Install and update guidance must present:

- the global workflow skill as the recommended agent-facing entry
- the global `chrome-agent` CLI as the required backend prerequisite
- the skill as delegating to the CLI rather than replacing it
