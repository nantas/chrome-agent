# chrome-agent

`chrome-agent` is a dedicated repository for browser-agent work.

Its purpose is to provide a stable place to:

- run browser-based tasks through `codex-agent`
- connect Chrome tooling such as `chrome-devtools-mcp` and `chrome-cdp-skill`
- accumulate reports, playbooks, and site-specific experience

## Current Status

The repository is in bootstrap stage with a minimal local Node toolchain in place.

The current milestone is:

1. establish the repository skeleton
2. define the high-level workflow in `AGENTS.md`
3. install repo-local Chrome tooling
4. validate the first real browser task

## Principles

- Entry point: `codex-agent`
- Workflow style: `AGENTS.md + skills`
- Default tooling direction: `chrome-devtools-mcp`
- Supplemental tooling direction: `chrome-cdp-skill`
- Credentials are intentionally out of scope for v1

## Top-Level Layout

- `.agents/skills/`: future workflow skills
- `configs/`: future tooling and environment configuration
- `docs/`: setup notes, decisions, and playbooks
- `reports/`: execution reports
- `sites/`: reusable site-specific experience

## Next Step

Use the repo-local commands in `package.json` and the setup note in `docs/setup/chrome-tooling.md` for future runs:

- `npm run devtools-cli -- start --isolated --no-usage-statistics`
- `npm run chrome-cdp -- list`

The first real validation report is recorded in `reports/2026-03-16-example-com-verification.md`.
