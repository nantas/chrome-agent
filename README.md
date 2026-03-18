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

## Workflow

Use this repository with one clear default:

- Start with `chrome-devtools-mcp` for public pages, repeatable interaction flows, and tasks that need structured diagnostics such as snapshots, network evidence, or performance tooling.
- Switch to the repo-local `chrome-cdp` skill only when the current agent session must immediately continue on a tab the user already has open in real Chrome.
- Treat authenticated live tabs the same way: `chrome-cdp` is the specialist path when immediate continuation matters, but the default remains `chrome-devtools-mcp`.
- If a live-session task is known up front and still needs MCP-native diagnostics, launch `chrome-devtools-mcp` in an explicit live-attach mode (`--autoConnect` or `--wsEndpoint`) rather than changing the repository default configuration.

## Verification Baseline

The repository now has an explicit evaluation baseline instead of ad hoc browser checks.

Scoring dimensions:

- `Capability Completion`
- `State Fidelity`
- `Diagnostic Depth`
- `Operational Friction`

Public-site baseline:

- Static page: `https://example.com`
- Modern SPA: `https://todomvc.com/examples/react/dist/`
- Dynamic list/pagination page: `https://news.ycombinator.com/news`
- Standard form page: `https://httpbin.org/forms/post`

Minimum evidence for public/repeatable runs:

- page title and URL
- one key content excerpt
- one screenshot
- one structure clue such as DOM or accessibility snapshot
- one interaction result if the task includes a flow

Live-session and authenticated baseline:

- already-open live tab continuation
- state preservation across follow-up reads
- first-connection versus follow-up friction
- read-only authenticated-page validation on `https://atomgit.com/nantas1/game-design-patterns`

Minimum evidence for live/authenticated runs:

- explicit approved target page or tab
- read-only boundary by default unless the user broadens scope
- one session or authentication-state clue
- first versus follow-up notes
- confirmation that no unexpected reset, logout, redirect, or write-action risk occurred

## Current Evidence

Completed reports:

- Public comparison: `reports/2026-03-17-browser-tooling-public-evaluation.md`
- Live-session comparison: `reports/2026-03-17-browser-tooling-live-session-evaluation.md`
- Authenticated comparison: `reports/2026-03-17-browser-tooling-authenticated-evaluation.md`

Current evidence-backed conclusion:

- `chrome-devtools-mcp` remains the default path.
- `chrome-cdp` remains the specialist path for immediate continuation on already-open live or authenticated tabs.
- Authenticated read-only workflows are now covered by evidence and are no longer an open decision.

Open gaps still worth future research:

- light live-session stability across `3-5` real tabs
- longer-running comparisons between `chrome-devtools-mcp --autoConnect` and `chrome-cdp` in repeated live-session work

## Working Rule

Start with the project-scoped `chrome-devtools-mcp` setup described in `docs/setup/chrome-tooling.md`.

If a task explicitly depends on the user's already-open live Chrome session and the current agent session is not already attached to it, use the repo-local `chrome-cdp` skill first.

If a live-session task is known up front and still needs MCP-native diagnostics, launch `chrome-devtools-mcp` in an explicit live-attach mode instead of changing the default repository config.

The current evidence-backed workflow decision is recorded in `docs/decisions/2026-03-17-browser-tooling-workflow.md`.
