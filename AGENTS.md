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

## Workflow

1. Understand the task, target site, and expected output first
2. Classify prompt intent before choosing workflow depth
3. Route the task into either `Content Retrieval` or `Platform/Page Analysis`
4. Decide whether the task is primarily public/repeatable browsing or live-session continuation
5. Start with `chrome-devtools-mcp` for new, repeatable, or diagnostics-heavy browser work
6. Use the repo-local `chrome-cdp` skill when the current agent session must continue on an already-open live Chrome tab immediately, including authenticated live tabs
7. Only use `chrome-devtools-mcp` live-attach modes such as `--autoConnect` or `--wsEndpoint` when the task explicitly needs the real Chrome session and starting with that mode is acceptable
8. Do not switch tools just because both can complete the task; switch only when session context, state-access needs, or diagnostic needs materially change
9. Capture evidence and write outputs at the depth required by the selected workflow
10. If the task reveals reusable site knowledge, update `sites/` or `docs/playbooks/`

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

- prefer the shortest reliable extraction path
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

- collect stronger evidence
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

- Default path: `chrome-devtools-mcp` in its managed browser context
- Specialist path: repo-local `chrome-cdp` for immediate continuation on an existing live Chrome tab, including authenticated read-only tabs
- Advanced live-session mode: `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` when a fresh live-attached MCP session is worth the setup
- Do not assume both are required for every task
- Let real tasks drive how skills, configs, and playbooks evolve

## Selection Rules

- Default to `chrome-devtools-mcp` when the task is public, repeatable, or benefits from structured diagnostics such as snapshot, network, console, or performance evidence.
- Stay on `chrome-devtools-mcp` if both tools succeed and there is no clear specialist advantage.
- Switch to `chrome-cdp` when the user explicitly approves using the current live Chrome session and the current agent session must continue on that already-open tab immediately.
- Treat authenticated live tabs as part of the same specialist trigger, but keep those runs read-only unless the user explicitly broadens scope.
- If a live-session task is known up front and still needs MCP-native diagnostics, prefer starting with `chrome-devtools-mcp --autoConnect` or `--wsEndpoint` instead of changing tools mid-run.

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
