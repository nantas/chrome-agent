# Browser Tooling Workflow Decision

## Decision

This decision is historical.

The repository now uses Scrapling as the first webpage grabbing path. Keep this document as the evidence record for the Chrome fallback split:

- `chrome-devtools-mcp` remains the structured diagnostics fallback
- `chrome-cdp` remains the specialist path for immediate continuation on an already-open live Chrome tab
- live-session attach modes for `chrome-devtools-mcp` remain opt-in

## Evidence Summary

- Public-site evaluation: both tools completed the static, SPA, pagination, and form scenarios successfully. `chrome-devtools-mcp` was consistently lower-friction for user-journey style flows, while `chrome-cdp` needed more operator-directed DOM/event scripting.
- Live-session evaluation: both tools successfully read the approved Gemini live tab, preserved page state during read-only inspection, and captured screenshots from the existing browser session.
- Authenticated evaluation (AtomGit): both tools successfully read the approved authenticated page `https://atomgit.com/nantas1/game-design-patterns`, preserved authenticated state markers (`authClue: true`) across follow-up reads, and avoided page reset or navigation.
- Live-session attach nuance: `chrome-devtools-mcp --browserUrl http://127.0.0.1:9222` failed in this environment because Chrome returned `404` for `/json/version`, but `chrome-devtools-mcp` did work with `--wsEndpoint` and with `--autoConnect`.
- Practical session-level tradeoff: in an already-running agent session, `chrome-cdp` was the lower-friction way to reach the live tab immediately; once attached, `chrome-devtools-mcp` exposed the richer structured inspection surface.

## Default path

- Start with Scrapling for public-site access, repeatable content extraction, dynamic pages, protected pages, and article extraction.
- Treat `chrome-devtools-mcp` as the managed browser diagnostics path, not as the first grabbing path.
- If Scrapling can complete the task without browser diagnostics, stay on Scrapling.

## Specialist path

- Use the repo-local `chrome-cdp` skill when the task must continue on an already-open live Chrome tab from the current agent session and rebinding the MCP server would add avoidable friction.
- This specialist trigger includes authenticated live tabs; the AtomGit authenticated run confirmed `chrome-cdp` can preserve authenticated context in read-only follow-up flows.
- Prefer `chrome-cdp` for targeted live-session reads, quick DOM/script manipulation, and cases where direct target discovery in the existing browser matters more than the broader MCP tool surface.
- Use `chrome-devtools-mcp` live attach mode (`--autoConnect` or `--wsEndpoint`) when starting a fresh session is acceptable and the task still benefits from MCP-native diagnostics after attaching to the real browser.

## Switching triggers

- Start with Scrapling for public, repeatable, dynamic, protected, and article-oriented grabbing work.
- Escalate to `chrome-devtools-mcp` only when structured browser diagnostics or evidence are required.
- Switch to `chrome-cdp` when the user explicitly approves using the current live Chrome session and the existing agent session needs to continue on that browser immediately.
- If approved Scrapling session reuse fails to preserve authenticated context, stop that path and use the approved live tab fallback instead of retrying blindly.
- Stay with `chrome-devtools-mcp` if live-session access can be planned up front by launching the MCP server in an explicit live-attach mode and the task needs its structured inspection tools.
- Do not switch tooling just because both tools overlap. Switch only when the task context changes operational friction, state-access needs, or diagnostic requirements.

## Scenarios Still Undecided

- light live-session stability across `3-5` real tabs
- longer-running comparisons between `chrome-devtools-mcp --autoConnect` and `chrome-cdp` in repeated live-session work
