# Chrome Tooling Setup

This repository uses project-scoped MCP configuration instead of repo-local binaries.

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

- `chrome-devtools-mcp` is the default browser tooling path for this repo.
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
