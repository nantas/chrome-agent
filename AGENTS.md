# AGENTS.md

This repository is a browser-agent workspace for website access, debugging, evidence collection, and execution reporting.

## Goals

1. Use `codex-agent` as the primary entrypoint for browser-driven tasks
2. Keep workflows driven by `AGENTS.md + skills`, not by ad hoc scripts
3. Accumulate reusable reports and site-specific experience over time

## Scope

- In scope:
  - Website access and information gathering through a browser agent workflow
  - Frontend debugging, page inspection, and evidence capture
  - Reporting what was attempted, what succeeded, what failed, and what to try next
- Out of scope for v1:
  - Credential management
  - A large automation framework
  - Hard-coding detailed skill or config structures before real usage validates them

## Workflow

1. Understand the task, target site, and expected output first
2. Decide whether the task is primarily public/repeatable browsing or live-session continuation
3. Start with `chrome-devtools-mcp` for new, repeatable, or diagnostics-heavy browser work
4. Use the repo-local `chrome-cdp` skill when the current agent session must continue on an already-open live Chrome tab immediately, including authenticated live tabs
5. Only use `chrome-devtools-mcp` live-attach modes such as `--autoConnect` or `--wsEndpoint` when the task explicitly needs the real Chrome session and starting with that mode is acceptable
6. Do not switch tools just because both can complete the task; switch only when session context, state-access needs, or diagnostic needs materially change
7. Record the execution result in `reports/`
8. If the task reveals reusable site knowledge, update `sites/` or `docs/playbooks/`

## Tooling Strategy

- Default path: `chrome-devtools-mcp` in its managed browser context
- Specialist path: repo-local `chrome-cdp` for immediate continuation on an existing live Chrome tab, including authenticated read-only tabs
- Advanced live-session mode: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when a fresh live-attached MCP session is worth the setup
- Do not assume both are required for every task
- Let real tasks drive how skills, configs, and playbooks evolve

## Selection Rules

- Default to `chrome-devtools-mcp` when the task is public, repeatable, or benefits from structured diagnostics such as snapshot, network, console, or performance evidence.
- Stay on `chrome-devtools-mcp` if both tools succeed and there is no clear specialist advantage.
- Switch to `chrome-cdp` when the user explicitly approves using the current live Chrome session and the current agent session must continue on that already-open tab immediately.
- Treat authenticated live tabs as part of the same specialist trigger, but keep those runs read-only unless the user explicitly broadens scope.
- If a live-session task is known up front and still needs MCP-native diagnostics, prefer starting with `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` instead of changing tools mid-run.

## Reporting Requirements

Each completed browser task should capture at least:

- Task goal
- Target site or page
- Tooling path used
- Result: success, partial success, or failure
- Key evidence
- Next recommended action

## Minimum Verification Baseline

For public or repeatable page runs, capture at least:

- page title and URL
- one key content excerpt
- one screenshot
- one structure clue such as DOM or accessibility snapshot
- one interaction outcome if the task includes a flow

For live-session or authenticated runs, capture at least:

- explicit user-approved target page or tab
- read-only boundary by default unless the user broadens scope
- one authentication or session-state clue when relevant
- first-connection versus follow-up action notes
- confirmation that no unexpected reset, logout, redirect, or write-action risk occurred

If a task triggers unexpected logout, redirect, page reset, or write-action risk, stop and record failure rather than pushing through.

## Repository Expectations

- Keep top-level structure stable
- Avoid premature abstraction in `skills/` and `configs/`
- Prefer writing down decisions after real runs instead of guessing them up front
