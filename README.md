# chrome-agent

`chrome-agent` is a dedicated repository for browser-agent work.

Its purpose is to provide a stable place to:

- run browser-based tasks through `codex-agent`
- connect Chrome tooling such as `chrome-devtools-mcp` and the repo-local `chrome-cdp` skill
- accumulate reports, playbooks, and site-specific experience

## Current Status

The repository now has a research-backed browser tooling workflow with project-scoped Chrome MCP configuration, a repo-local `chrome-cdp` skill, and comparison reports under `reports/`.

The current milestone is:

1. establish the repository skeleton
2. verify the default vs specialist tooling split with public-site and live-session evidence
3. document the workflow decision in `AGENTS.md`, `README.md`, and `docs/decisions/`
4. use the resulting playbooks and reports for future browser tasks

## Principles

- Entry point: `codex-agent`
- Workflow style: `AGENTS.md + skills`
- Default tooling direction: `chrome-devtools-mcp` in a managed browser context
- Specialist tooling direction: repo-local `chrome-cdp` for immediate continuation on an already-open live Chrome tab
- Advanced live-session option: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when starting a fresh live-attached MCP session is acceptable
- Credentials are intentionally out of scope for v1

Workflow labels used across the repository:

- Default path: `chrome-devtools-mcp` in a managed browser context
- Specialist path: repo-local `chrome-cdp` for immediate continuation on an already-open live Chrome tab
- Switching triggers: use `chrome-cdp` when the current session must continue on a real live tab immediately; otherwise stay on `chrome-devtools-mcp` unless a fresh live-attached MCP session is planned up front

## Top-Level Layout

- `.agents/skills/`: future workflow skills
- `.codex/`: project-scoped Codex configuration
- `configs/`: future tooling and environment configuration
- `docs/`: setup notes, decisions, and playbooks
- `opencode.json`: project-scoped OpenCode configuration
- `reports/`: execution reports
- `sites/`: reusable site-specific experience

## Working Rule

Start with the project-scoped `chrome-devtools-mcp` setup described in `docs/setup/chrome-tooling.md`.

If a task explicitly depends on the user's already-open live Chrome session and the current agent session is not already attached to it, use the repo-local `chrome-cdp` skill first.

If a live-session task is known up front and still needs MCP-native diagnostics, launch `chrome-devtools-mcp` in an explicit live-attach mode instead of changing the default repository config.

The current evidence-backed workflow decision is recorded in `docs/decisions/2026-03-17-browser-tooling-workflow.md`.
