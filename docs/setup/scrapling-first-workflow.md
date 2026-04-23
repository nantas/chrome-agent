# Scrapling-First Workflow Setup

This repository now treats Scrapling as the first webpage grabbing path. Chrome tooling remains available as fallback:

- `chrome-devtools-mcp` for structured diagnostics and evidence capture
- `chrome-cdp` for immediate continuation on an already-open live Chrome tab

## Verified Runtime

The local machine used for this setup had:

- system Python `3.9.6`
- `uv` available
- a dedicated Scrapling environment created with Python `3.11.14`

The verified Scrapling executable path is:

```bash
/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling
```

## Install

Create an isolated Python environment and install Scrapling with MCP support:

```bash
uv venv /Users/nantasmac/.cache/chrome-agent-scrapling --python 3.11
uv pip install --python /Users/nantasmac/.cache/chrome-agent-scrapling/bin/python "scrapling[ai]"
/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling install
```

The browser dependency install step should be run after the package install. In this repository, the command completed successfully and installed Playwright browsers and dependencies.

## MCP Configuration

Use the full Scrapling executable path in project-scoped MCP config so the server starts from the verified environment instead of relying on system PATH.

`codex`:

```toml
[mcp_servers."scrapling"]
command = "/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling"
args = ["mcp"]
```

`opencode`:

```json
{
  "mcp": {
    "scrapling": {
      "type": "local",
      "command": ["/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling", "mcp"]
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

- `scrapling --help`
- `scrapling extract get https://example.com ... --ai-targeted`
- `scrapling extract fetch https://todomvc.com/examples/react/dist/ ... --ai-targeted --network-idle`
- `scrapling extract get https://mp.weixin.qq.com/s/kPEyL3NDPAQYp7sFl5eE4w?scene=1 ... --ai-targeted`
- `scrapling extract stealthy-fetch https://wiki.supercombo.gg/w/Street_Fighter_6 ... --ai-targeted --solve-cloudflare`

Observed results from those runs:

- public static and SPA pages were fetched successfully
- the WeChat article returned Markdown with inline image URLs
- the SuperCombo page solved the Cloudflare challenge and returned the article content

## Notes

- The current setup is isolated from the system Python.
- If the Scrapling executable path changes, update the project MCP config files and this document together.
