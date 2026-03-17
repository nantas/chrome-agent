# chrome-agent

`chrome-agent` is a dedicated repository for browser-agent work.

Its purpose is to provide a stable place to:

- run browser-based tasks through `codex-agent`
- connect Chrome tooling such as `chrome-devtools-mcp` and `chrome-cdp-skill`
- accumulate reports, playbooks, and site-specific experience

## Current Status

The repository is in bootstrap stage with project-scoped Chrome MCP configuration in place.

The current milestone is:

1. establish the repository skeleton
2. define the high-level workflow in `AGENTS.md`
3. add project-scoped `chrome-devtools-mcp` config for `codex` and `opencode`
4. use that shared setup for future browser tasks and reports

## Principles

- Entry point: `codex-agent`
- Workflow style: `AGENTS.md + skills`
- Default tooling direction: `chrome-devtools-mcp`
- Supplemental tooling direction: `chrome-cdp-skill`
- Credentials are intentionally out of scope for v1

## Top-Level Layout

- `.agents/skills/`: future workflow skills
- `.codex/`: project-scoped Codex configuration
- `configs/`: future tooling and environment configuration
- `docs/`: setup notes, decisions, and playbooks
- `opencode.json`: project-scoped OpenCode configuration
- `reports/`: execution reports
- `sites/`: reusable site-specific experience

## Next Step

Use the project-scoped MCP setup described in `docs/setup/chrome-tooling.md` for future runs.

Both `codex` and `opencode` now launch `chrome-devtools-mcp` with the official recommended `npx chrome-devtools-mcp@latest` command from this repository.
