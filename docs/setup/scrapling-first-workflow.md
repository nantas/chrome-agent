# Scrapling-First Workflow Setup

This repository now treats Scrapling as the first webpage grabbing path. Chrome tooling remains available as fallback:

- `chrome-devtools-mcp` for structured diagnostics and evidence capture
- `chrome-cdp` for immediate continuation on an already-open live Chrome tab

## Runtime Contract

- Canonical environment variable: `SCRAPLING_CLI_PATH`
- Default managed install root: `$HOME/.cache/chrome-agent-scrapling`
- Default managed executable: `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- Preflight helper: `./scripts/scrapling-cli.sh`
- Persistent shell file for optional confirmation flow: `/Users/nantas-agent/.zshenv`

The verified baseline for this repository used:

- system Python `3.9.6`
- `uv` available
- a dedicated Scrapling environment created with Python `3.11.14`

## Preflight Before Fetchers or MCP

```bash
./scripts/scrapling-cli.sh preflight
```

The preflight contract is:

1. check `SCRAPLING_CLI_PATH`
2. check `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
3. if neither is runnable, run the managed install flow
4. only after the CLI is available, continue to fetcher selection or MCP launch

If preflight fails, stop and report the missing prerequisite instead of letting MCP fail later with `os error 2`.

## Install / Repair

Create an isolated Python environment and install Scrapling with MCP support:

```bash
uv venv "$HOME/.cache/chrome-agent-scrapling" --python 3.11
uv pip install --python "$HOME/.cache/chrome-agent-scrapling/bin/python" "scrapling[ai]"
"$HOME/.cache/chrome-agent-scrapling/bin/scrapling" install
```

The browser dependency install step should be run after the package install. In this repository, the command completed successfully and installed Playwright browsers and dependencies.

If you only want the export line for the current shell:

```bash
eval "$(./scripts/scrapling-cli.sh shellenv)"
```

If you want to persist `SCRAPLING_CLI_PATH` after explicit approval:

```bash
./scripts/scrapling-cli.sh persist-zshenv
```

If `.zshenv` already has a different value, treat that as a conflict and confirm before running:

```bash
./scripts/scrapling-cli.sh persist-zshenv --replace-conflict
```

## MCP Configuration

Use a shell launcher that resolves the repo helper. Do not edit tracked files to insert a user-specific absolute Scrapling path.

`codex`:

```toml
[mcp_servers."scrapling"]
command = "/bin/sh"
args = ["-lc", "repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); launcher=\"$repo_root/scripts/scrapling-cli.sh\"; if [ ! -x \"$launcher\" ]; then echo \"scrapling MCP launcher missing: $launcher\" >&2; exit 1; fi; exec \"$launcher\" mcp"]
```

`opencode`:

```json
{
  "mcp": {
    "scrapling": {
      "type": "local",
      "command": [
        "/bin/sh",
        "-lc",
        "repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); launcher=\"$repo_root/scripts/scrapling-cli.sh\"; if [ ! -x \"$launcher\" ]; then echo \"scrapling MCP launcher missing: $launcher\" >&2; exit 1; fi; exec \"$launcher\" mcp"
      ]
    }
  }
}
```

Keep the existing `chrome-devtools` config in place. Scrapling-first does not remove Chrome diagnostics; it changes the first path.

## Operational Split

- Use Scrapling `get` for straightforward public content retrieval.
- Use Scrapling `fetch` for JavaScript-rendered pages.
- Use Scrapling `stealthy-fetch` for protected pages or anti-bot challenges.
- Use `chrome-devtools-mcp` when Scrapling output is incomplete and browser evidence is needed.
- Use `chrome-cdp` only when the task must continue immediately in an already-open live Chrome tab.

## Verified Smoke Checks

The following checks were run successfully in this repository:

- `./scripts/scrapling-cli.sh preflight`
- `"$HOME/.cache/chrome-agent-scrapling/bin/scrapling" --help`
- `"$HOME/.cache/chrome-agent-scrapling/bin/scrapling" extract get https://example.com outputs/example.md`
- `codex -C /Users/nantas-agent/projects/chrome-agent mcp list`

## Notes

- The current setup is isolated from the system Python.
- The tracked MCP config no longer stores a host-user-specific Scrapling path.
- Preflight is mandatory before selecting `get`, `fetch`, `stealthy-fetch`, or starting the Scrapling MCP server.
