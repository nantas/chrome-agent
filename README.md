# chrome-agent

`chrome-agent` is a dedicated repository for browser-agent work.

Its purpose is to provide a stable place to:

- run browser-based tasks through `codex-agent`
- run Scrapling-first webpage grabbing through the repo workflow
- connect Chrome tooling such as `chrome-devtools-mcp` and the repo-local `chrome-cdp` skill when fallback evidence or live-session continuation is needed
- accumulate reports, playbooks, and site-specific experience

## Current Status

The repository now has a research-backed browser workflow with project-scoped MCP configuration, a Scrapling-first grabbing path, a repo-local `chrome-cdp` skill, and comparison reports under `reports/`.

The current milestone is:

1. establish the repository skeleton
2. verify the Scrapling-first vs fallback tooling split with public-site, protected-page, and article evidence
3. document the workflow decision in `AGENTS.md`, `README.md`, and `docs/decisions/`
4. use the resulting playbooks and reports for future browser tasks

## Principles

- Entry point: `codex-agent`
- Workflow style: `AGENTS.md + skills`
- Default tooling direction: Scrapling in a dedicated Python `>=3.10` environment
- Diagnostic fallback: `chrome-devtools-mcp` in a managed browser context
- Specialist tooling direction: repo-local `chrome-cdp` for immediate continuation on an already-open live Chrome tab
- Advanced live-session option: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when starting a fresh live-attached MCP session is acceptable
- Credentials are intentionally out of scope for v1

Workflow labels used across the repository:

- Default path: Scrapling first
- Diagnostic fallback: `chrome-devtools-mcp` in a managed browser context
- Specialist path: repo-local `chrome-cdp` for immediate continuation on an already-open live Chrome tab
- Switching triggers: use `chrome-cdp` when the current session must continue on a real live tab immediately; otherwise stay on Scrapling unless browser diagnostics are required

## Top-Level Layout

- `.agents/skills/`: future workflow skills
- `.codex/`: project-scoped Codex configuration
- `configs/`: future tooling and environment configuration
- `docs/`: setup notes, decisions, and playbooks
- `opencode.json`: project-scoped OpenCode configuration
- `reports/`: execution reports
- `skills/`: repository-owned global skill sources
- `sites/`: reusable site-specific experience

## Workflow

Use this repository with one clear default:

- Start with Scrapling for public pages, repeatable interaction flows, dynamic pages, protected pages, and article extraction.
- Switch to `chrome-devtools-mcp` when you need structured diagnostics such as snapshots, network evidence, or performance tooling.
- Switch to the repo-local `chrome-cdp` skill only when the current agent session must immediately continue on a tab the user already has open in real Chrome.
- Treat authenticated live tabs the same way: `chrome-cdp` is the specialist path when immediate continuation matters, but the default remains Scrapling unless browser diagnostics are required.
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
- Protected page: `https://wiki.supercombo.gg/w/Street_Fighter_6`
- Article page: `https://mp.weixin.qq.com/s/kPEyL3NDPAQYp7sFl5eE4w?scene=1`

Minimum evidence for public/repeatable runs:

- page title and URL
- one key content excerpt
- Scrapling fetcher path and output mode
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

- Scrapling is the default grabbing path.
- `chrome-devtools-mcp` remains the diagnostic fallback path.
- `chrome-cdp` remains the specialist path for immediate continuation on already-open live or authenticated tabs.
- Authenticated read-only workflows remain covered by the existing live-session evidence, while Scrapling-first handling is still being expanded.

Open gaps still worth future research:

- light live-session stability across `3-5` real tabs
- longer-running comparisons between `chrome-devtools-mcp --autoConnect` and `chrome-cdp` in repeated live-session work
- login-state reuse quality for Scrapling session-based runs

## Working Rule

Start with the project-scoped Scrapling setup described in `docs/setup/scrapling-first-workflow.md`.

Use `docs/setup/chrome-tooling.md` for the Chrome diagnostics and live-session fallback paths.

If a task explicitly depends on the user's already-open live Chrome session and the current agent session is not already attached to it, use the repo-local `chrome-cdp` skill first.

If a live-session task is known up front and still needs MCP-native diagnostics, launch `chrome-devtools-mcp` in an explicit live-attach mode instead of changing the default repository config.

The current evidence-backed workflow decision is recorded in `docs/decisions/2026-04-23-scrapling-first-workflow.md`.

## Global Skill Source

This repository now also serves as the source of truth for a globally installable `chrome-agent` skill.

- source path: `skills/chrome-agent/`
- global install path: `~/.agents/skills/chrome-agent/`
- repository locator env var: `CHROME_AGENT_REPO`

The global skill is a thin dispatcher. It validates the global dispatcher skills, resolves `CHROME_AGENT_REPO`, and forwards webpage extraction requests into this repository so the repo workflow in `AGENTS.md` stays authoritative.

See `docs/setup/chrome-tooling.md` for the install contract and `docs/playbooks/chrome-agent-global-install.md` for the operator workflow.

You can start installation from a single prompt, but any persistent change still requires preflight checks and explicit confirmation when:

- `~/.agents/skills/chrome-agent/` already exists
- `CHROME_AGENT_REPO` already exists with a different value
- the install needs to append shell configuration
