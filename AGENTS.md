# AGENTS.md

This repository is a browser-agent workspace for website access, debugging, evidence collection, and execution reporting.

## Goals

1. Use `codex-agent` as the primary entrypoint for browser-driven tasks
2. Keep workflows driven by `AGENTS.md + skills`, not by ad hoc scripts
3. Accumulate reusable reports and site-specific experience over time

## Scope

- In scope:
  - Website access and information gathering through a browser agent workflow
  - Frontend debugging, page inspection, and evidence capture
  - Reporting what was attempted, what succeeded, what failed, and what to try next
- Out of scope for v1:
  - Credential management
  - A large automation framework
  - Hard-coding detailed skill or config structures before real usage validates them

## Default Web Grabbing Flow

Use one operator flow for ordinary webpage grabbing work:

1. Understand the task, target site, and expected output first.
2. Route the task into either `Content Retrieval` or `Platform/Page Analysis`.
3. Decide whether the task is normal public/repeatable grabbing or approved live-session continuity.
4. Start with Scrapling unless a live-session continuity trigger is already known up front.
5. Stop on Scrapling if the result satisfies the task.
6. Escalate to `chrome-devtools-mcp` only when diagnostic or evidence triggers are present.
7. Escalate to repo-local `chrome-cdp` only when the current agent session must continue immediately on an already-open real Chrome tab.
8. Capture evidence and write outputs at the depth required by the selected workflow.
9. If the task reveals reusable site knowledge, update `sites/` or `docs/playbooks/`.

### Route First

- `Content Retrieval`: the user mainly wants page content, article body text, or a concise failure reason.
- `Platform/Page Analysis`: the user mainly wants debugging, structure analysis, evidence collection, extraction-rule analysis, or a reusable report.

### Scrapling-First Path

- `get`: default for static pages and article-style extraction where body order and inline images matter.
- `fetch`: default for SPA pages, dynamic lists, pagination, or other rendered flows that need client-side state.
- `stealthy-fetch`: default for protected pages, challenge pages, or anti-bot-sensitive targets.
- bulk variants: use only when the task really is a batch grab across multiple URLs.
- session variants: use only when repeated related reads benefit from one Scrapling browser session, or when an authenticated task has an explicit user-approved read-only target and session reuse is worth attempting.
- If Scrapling returns content that satisfies the task, stay on Scrapling. Do not switch tools just because another browser tool could also complete the task.

### Fallback Boundaries

- `chrome-devtools-mcp`: the diagnostic and evidence path. Use it when Scrapling output is incomplete, visually suspect, blocked, or when the task needs screenshots, DOM or accessibility inspection, network evidence, console evidence, performance evidence, or interaction debugging.
- repo-local `chrome-cdp`: the live-session continuity path. Use it when the current agent session must continue immediately on an already-open real Chrome tab, including approved authenticated tabs whose current state should not be recreated elsewhere.
- `chrome-devtools-mcp --autoConnect` or `--wsEndpoint`: use these live-attach modes only when the task is known up front to need the real Chrome session and starting with MCP-native diagnostics is acceptable.
- Do not switch between fallback tools just because both are technically capable. Choose by diagnostic-evidence needs versus live-tab continuity needs.

### Authenticated Read-Only Boundary

- Authenticated or logged-in work requires an explicit user-approved target page or tab before either Scrapling session reuse or `chrome-cdp` continuation is attempted.
- Authenticated runs are read-only by default unless the user explicitly broadens scope.
- Scrapling-first still applies to approved authenticated work when session reuse is worth trying.
- If Scrapling session reuse redirects to login, resets the page, loses the approved context, or creates logout/write-action risk, stop that Scrapling path and record failure instead of pushing through.
- If an approved live tab exists after that failure, switch to repo-local `chrome-cdp` as the live-session continuity fallback.
- Treat the current `x.com` result as the verified example for this rule: Scrapling-first remains the opening move, but current-session continuity can require immediate `chrome-cdp` fallback after session reuse fails.

## Workflow Types

### Workflow A: Content Retrieval

This is the default route.

Use it when the user primarily wants:

- the content of a page
- article正文 or main text
- a direct answer about what a page says
- a concise explanation of why extraction failed

Default deliverable:

- return the page content directly, or
- return the blocking issue directly

Default operating style:

- prefer the shortest reliable extraction path, starting with Scrapling `get`, `fetch`, `stealthy-fetch`, or their bulk/session variants
- keep verification lightweight
- avoid full evidence collection unless the page blocks extraction or the user asks for it
- avoid mandatory `reports/` output unless the user requests a saved artifact, the failure is worth preserving, or reusable knowledge is discovered

### Workflow B: Platform/Page Analysis

This is the deep route.

Use it when the user primarily wants:

- page or platform structure analysis
- debugging or failure investigation
- evidence collection
- extraction-rule analysis
- reusable lessons for future runs

Default deliverable:

- a saved report with evidence, findings, failures, and next actions

Default operating style:

- collect stronger evidence, usually by escalating from Scrapling to `chrome-devtools-mcp`
- preserve structural clues
- save the run under `reports/`
- update `sites/` or `docs/playbooks/` when the task yields reusable knowledge

## Intent Routing

Choose the workflow before deciding evidence depth.

Default to `Content Retrieval` when:

- the user gives only a URL
- the user asks to get, read, fetch, or extract page content
- the user’s desired output is content or a concise failure explanation

Route to `Platform/Page Analysis` when the prompt includes signals such as:

- `分析`
- `调试`
- `证据`
- `总结经验`
- `平台`
- `结构`
- `抓取规则`
- `复现`

If both kinds of signals appear, prefer `Platform/Page Analysis`.

## Tooling Strategy

- Default path: Scrapling in a dedicated Python `>=3.10` environment
- Default route order: route the task, check live-session continuity needs, then stay Scrapling-first unless a defined fallback trigger is present
- Diagnostic fallback: `chrome-devtools-mcp` in its managed browser context
- Live-session continuity fallback: repo-local `chrome-cdp` for immediate continuation on an existing live Chrome tab, including approved authenticated read-only tabs
- Advanced live-session mode: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when a fresh live-attached MCP session is worth the setup
- Do not assume all three are required for every task
- Let real tasks drive how skills, configs, and playbooks evolve

## Selection Rules

- Default to Scrapling for public, repeatable, dynamic, protected, article, and batch grabbing tasks.
- Stay on Scrapling if the output satisfies the task without extra diagnostics.
- Switch to `chrome-devtools-mcp` when the task needs structured diagnostics such as snapshot, DOM, accessibility, network, console, screenshot, performance, or interaction evidence.
- Switch to repo-local `chrome-cdp` when the user explicitly approves using the current live Chrome session and the existing agent session must continue on that already-open tab immediately.
- Treat authenticated live tabs as part of the same live-session continuity trigger, but keep those runs read-only unless the user explicitly broadens scope.
- If approved Scrapling session reuse fails to preserve authenticated context, stop that path and use the approved live tab fallback instead of retrying blindly.
- If a live-session task is known up front and still needs MCP-native diagnostics, prefer starting with `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` instead of changing tools mid-run.

## `chrome-cdp-skill` Usage Boundary

`chrome-cdp-skill` should be treated as a live-session handoff tool, not as the default browser automation path.

Use it when:

- the user has already opened the target website in their normal Chrome session
- the task depends on the current logged-in state, open tabs, or the exact in-progress browsing context
- the goal is for the agent to take over from the user's already-open browser session and continue the visit

Do not prefer it when:

- the task needs a reproducible isolated browser session
- the task needs an explicit browser URL, explicit debug port, or explicit Chrome profile
- the task should run against a dedicated test profile or a custom `user-data-dir`

Current limitation:

- the pinned `chrome-cdp-skill` setup reads Chrome debugging state from the default Chrome profile location
- it does not currently provide a stable explicit entrypoint for custom profiles or custom browser endpoints in this repo

Working rule for this repository:

- If the user wants the agent to continue from a website they already opened manually, `chrome-cdp-skill` is the correct supplemental path.
- If the task should start cleanly, run repeatably, or be isolated from the user's everyday browser state, stay on Scrapling first and use `chrome-devtools-mcp` only when diagnostics are required.

## Reporting Requirements

Each completed browser task should capture at least:

- Task goal
- Target site or page
- Tooling path used
- Result: success, partial success, or failure
- Key evidence appropriate to the selected workflow
- Next recommended action when useful

For `Content Retrieval` tasks:

- direct user output is the default deliverable
- include the Scrapling fetcher path when used
- create a `reports/` artifact only when the user asks for it, the failure should be preserved, or the task reveals reusable knowledge

For `Platform/Page Analysis` tasks:

- a saved `reports/` artifact is the default deliverable
- evidence should be complete enough to support later review and workflow refinement

For article-style extraction tasks in either workflow, generated正文 must preserve reading order from the page body:

- Walk the article body in DOM order instead of relying on plain `innerText`
- Keep real image source URLs in the output at their original positions
- Use Markdown image syntax such as `![图片1](https://...)` for inline article images
- Do not replace article images with generic placeholders such as `图片`

## Minimum Verification Baseline

For `Content Retrieval` tasks, capture at least:

- page title and URL
- the Scrapling fetcher path or explicit fallback path
- extracted main content, or a precise failure reason
- one lightweight evidence point when needed to trust the result

For article-style retrieval, preserve DOM order and inline image URLs in the generated正文.

For `Platform/Page Analysis` tasks on public or repeatable pages, capture at least:

- page title and URL
- one key content excerpt
- one screenshot
- one structure clue such as DOM or accessibility snapshot
- one interaction outcome if the task includes a flow

For `Platform/Page Analysis` tasks on live-session or authenticated runs, capture at least:

- explicit user-approved target page or tab
- read-only boundary by default unless the user broadens scope
- one authentication or session-state clue when relevant
- first-connection versus follow-up action notes
- confirmation that no unexpected reset, logout, redirect, or write-action risk occurred

If a task triggers unexpected logout, redirect, page reset, or write-action risk, stop and record failure rather than pushing through.

## Repository Expectations

- Keep top-level structure stable
- Avoid premature abstraction in `skills/` and `configs/`
- Prefer writing down decisions after real runs instead of guessing them up front
