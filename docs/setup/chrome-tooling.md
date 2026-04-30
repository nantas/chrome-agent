# Chrome Tooling Setup

This repository uses project-scoped MCP configuration for Chrome diagnostics and live-session fallback paths.

Scrapling-first setup lives in `docs/setup/scrapling-first-workflow.md`.

## Official Launcher

The shared launcher for both clients is the official recommended command from the
`chrome-devtools-mcp` README:

```bash
npx chrome-devtools-mcp@latest
```

## Project Files

`codex` reads project configuration from `.codex/config.toml`:

```toml
[mcp_servers."chrome-devtools"]
command = "npx"
args = ["chrome-devtools-mcp@latest"]
```

`opencode` reads project configuration from `opencode.json`:

```json
{
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "chrome-devtools-mcp@latest"]
    }
  }
}
```

## Client Notes

- `chrome-devtools-mcp` is the diagnostic fallback browser tooling path for this repo.
- No `package.json`, lockfile, or repo-local `node_modules` installation is required.
- `codex` only loads `.codex/config.toml` for trusted projects.
- `opencode` looks for `opencode.json` in the current project and parent directories.

## Quick Checks

From the repo root, the following commands should see the configured server:

```bash
codex -C /Users/nantasmac/projects/agentic/chrome-agent mcp get chrome-devtools
opencode mcp list
```

## Source

- `https://github.com/ChromeDevTools/chrome-devtools-mcp`
- `https://opencode.ai/docs/config/`

## Tool Roles

- `chrome-devtools-mcp` is the structured diagnostics fallback when Scrapling needs browser evidence or interaction inspection.
- `chrome-cdp-skill` is the supplemental path when the task must reuse a live Chrome session you already have open.

## Recommended Usage Split

Use `chrome-cdp-skill` specifically as a live-session handoff path:

- the user manually opens the target website first
- the agent then continues the visit from that already-open Chrome session
- this is the right fit when the current login state, open tabs, or in-progress browsing context matters

Do not treat `chrome-cdp-skill` as the default isolated automation path:

- it is not the right tool for clean reproducible runs
- it is not the right tool when a custom browser endpoint, custom debug port, or custom Chrome profile must be selected explicitly

For those cases, prefer `chrome-devtools-mcp`.

## Environment Assumptions

- Node.js `24.13.0` and npm `11.6.2` were used for the local setup.
- Local Chrome was verified at `146.0.7680.80`.
- `chrome-devtools-mcp --autoConnect` is available with Chrome `144+`, but it still requires Chrome remote debugging to be enabled in the running browser.

## Validation Notes

### `chrome-devtools-mcp`

Validated locally through the package-provided `chrome-devtools` CLI wrapper:

```bash
npm run devtools-cli -- start --isolated --no-usage-statistics
npm run devtools-cli -- new_page https://example.com --output-format json
npm run devtools-cli -- evaluate_script '() => document.title' --output-format json
npm run devtools-cli -- take_snapshot --output-format json
```

This path succeeded end-to-end against `https://example.com/` and saved a screenshot under `reports/`.

### `chrome-cdp-skill`

The pinned version works, but it has a narrower startup assumption than `chrome-devtools-mcp`:

- it does not accept a custom `--browserUrl`
- it does not accept a custom Chrome profile path
- it reads the debugging endpoint only from `~/Library/Application Support/Google/Chrome/DevToolsActivePort`

For normal use, enable remote debugging in your regular Chrome at:

`chrome://inspect/#remote-debugging`

If that toggle is on in the default Chrome profile, `npm run chrome-cdp -- list` can attach directly.

For the isolated verification run on 2026-03-16, the tool was validated against a separately launched debug Chrome, and the expected `DevToolsActivePort` file had to be written to the default location because the tool does not currently discover custom-profile debug sessions on its own.

## First Real Task

See `reports/2026-03-16-example-com-verification.md` for the exact commands, evidence, and residual blocker notes from the first public-page validation.

## Global `chrome-agent` CLI

This repository is the source of truth for the repo-backed global `chrome-agent` launcher.

### Locations

- installer: `scripts/install-chrome-agent-cli.sh`
- runtime script: `~/.agents/scripts/chrome-agent.mjs`
- user-facing shim: `~/.local/bin/chrome-agent`
- default repository locator: `CHROME_AGENT_REPO`
- explicit repo-ref locator: `--repo repo://chrome-agent`

### Runtime Contract

The launcher is intentionally thin:

- resolve the target repository
- dispatch into repository-local logic
- preserve repository-local AGENTS/spec routing authority
- return JSON-first results with artifact metadata

### Install Preflight

Before installing the launcher or writing shell configuration:

- inspect existing launcher paths
- inspect existing `CHROME_AGENT_REPO` state
- do not overwrite conflicting launcher paths or env config silently

See `docs/playbooks/chrome-agent-global-install.md` for the operator workflow and migration guidance.
