# Scrapling-First Workflow Decision

## Decision

Use Scrapling as the repository default webpage grabbing path.

Keep `chrome-devtools-mcp` as the structured diagnostics fallback when Scrapling output needs DOM, network, console, screenshot, or interaction evidence.

Keep the repo-local `chrome-cdp` skill as the specialist path for immediate continuation on an already-open live Chrome tab when the current agent session is not already attached to that live browser.

Do not change the repository to auto-attach Chrome by default. Live-session attach modes for `chrome-devtools-mcp` remain opt-in.

## Evidence Summary

- Local environment verification found system Python `3.9.6`, so Scrapling had to be installed in an isolated Python `3.11.14` environment.
- `scrapling install` completed successfully in the managed cache environment and installed browser dependencies.
- Public-site smoke checks succeeded on `https://example.com` and `https://todomvc.com/examples/react/dist/`.
- Article smoke check succeeded on `https://mp.weixin.qq.com/s/kPEyL3NDPAQYp7sFl5eE4w?scene=1`, including inline image URLs in Markdown output.
- Protected-page smoke check succeeded on `https://wiki.supercombo.gg/w/Street_Fighter_6` with Cloudflare challenge solving.
- The older Chrome tooling decision remains valid as a fallback and live-session evidence record.

## Default Path

- Start with Scrapling for public-site access, repeatable content extraction, dynamic pages, protected pages, batch grabs, and approved read-only session reuse.
- Treat `chrome-devtools-mcp` as the managed browser diagnostics path, not the first grabbing path.
- If Scrapling can complete the task without browser diagnostics, stay on Scrapling.

## Specialist Path

- Use the repo-local `chrome-cdp` skill when the task must continue on an already-open live Chrome tab from the current agent session and rebinding the MCP server would add avoidable friction.
- This specialist trigger includes authenticated live tabs.
- Prefer `chrome-cdp` for targeted live-session reads, quick DOM/script manipulation, and cases where direct target discovery in the existing browser matters more than the broader MCP tool surface.
- Use `chrome-devtools-mcp` live attach mode (`--autoConnect` or `--wsEndpoint`) when starting a fresh session is acceptable and the task still benefits from MCP-native diagnostics after attaching to the real browser.

## Switching Triggers

- Start with Scrapling when the task is public, repeatable, dynamic, protected, or article-oriented.
- Switch to `chrome-devtools-mcp` when browser evidence is needed.
- Switch to `chrome-cdp` when the user explicitly approves using the current live Chrome session and the existing agent session needs to continue on that browser immediately.
- Do not switch tooling just because both tools overlap. Switch only when the task context changes operational friction, state-access needs, or diagnostic requirements.

## Remaining Gaps

- light live-session stability across `3-5` real tabs
- longer-running comparisons between `chrome-devtools-mcp --autoConnect` and `chrome-cdp` in repeated live-session work
- logged-in session reuse quality for Scrapling session-based runs
