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

## Global `chrome-agent` Skill

This repository is also the source of truth for a globally installable `chrome-agent` dispatcher skill.

### Locations

- source directory: `skills/chrome-agent/`
- global install directory: `~/.agents/skills/chrome-agent/`
- repository environment variable: `CHROME_AGENT_REPO`

### Runtime Contract

The global skill should:

- prefer `~/.agents/skills/codex-agent/`
- fall back to `~/.agents/skills/repo-agent/`
- stop if neither dispatcher skill is installed
- resolve `CHROME_AGENT_REPO` to locate this repository
- fail if `CHROME_AGENT_REPO` is missing, invalid, or does not contain `AGENTS.md`

### Install Preflight

Before copying the global skill or writing shell configuration:

- check whether `~/.agents/skills/chrome-agent/` already exists
- check whether `CHROME_AGENT_REPO` is already defined
- if the existing environment variable value differs from the current repository path, treat it as a conflict
- do not overwrite the existing skill or conflicting environment variable silently
- ask for explicit confirmation before any persistent write

### One-Line Install Entry

The intended user experience is that installation can start from a single prompt. That does not remove the conflict checks above. A one-line install still must:

- inspect existing global skill state
- inspect existing `CHROME_AGENT_REPO` state
- ask before replacing an installed skill
- ask before replacing or appending shell configuration

See `docs/playbooks/chrome-agent-global-install.md` for the operator workflow.
