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
2. Decide whether the task is primarily access/collection or debugging/inspection
3. Start with `chrome-devtools-mcp` for new, repeatable, or diagnostics-heavy browser work
4. Use the repo-local `chrome-cdp` skill when the current agent session must continue on an already-open live Chrome tab immediately
5. Only use `chrome-devtools-mcp` live-attach modes such as `--autoConnect` or `--wsEndpoint` when the task explicitly needs the real Chrome session and starting with that mode is acceptable
6. Record the execution result in `reports/`
7. If the task reveals reusable site knowledge, update `sites/` or `docs/playbooks/`

## Tooling Strategy

- Default path: `chrome-devtools-mcp` in its managed browser context
- Specialist path: repo-local `chrome-cdp` for immediate continuation on an existing live Chrome tab
- Advanced live-session mode: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when a fresh live-attached MCP session is worth the setup
- Do not assume both are required for every task
- Let real tasks drive how skills, configs, and playbooks evolve

## Reporting Requirements

Each completed browser task should capture at least:

- Task goal
- Target site or page
- Tooling path used
- Result: success, partial success, or failure
- Key evidence
- Next recommended action

## Repository Expectations

- Keep top-level structure stable
- Avoid premature abstraction in `skills/` and `configs/`
- Prefer writing down decisions after real runs instead of guessing them up front
