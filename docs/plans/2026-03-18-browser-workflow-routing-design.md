# Browser Workflow Routing Design

## Goal

Split the repository workflow into two distinct browser-task paths:

1. a fast default path for content retrieval from a URL
2. a full evidence-heavy path for platform/page analysis

The repository should decide between these paths by identifying user intent from the prompt before choosing tooling depth, evidence depth, and reporting scope.

## Problem

The current workflow treats many browser tasks as if they require the same level of evidence collection and reporting. That is too expensive for the common case where the user simply provides a URL and wants the page content or an explanation of why extraction failed.

This creates avoidable latency through:

- full reporting when direct user output would suffice
- heavy screenshots and structure gathering for simple read-only tasks
- deeper process overhead even when the user has not asked for page analysis

## Design

### Workflow A: Content Retrieval

This is the default route.

Use it when the prompt is primarily asking:

- what content is on a page
- to extract正文/main text
- to fetch article content from a URL
- to report why the content cannot be obtained

Expected output:

- extracted content returned directly to the user, or
- a concise failure explanation with the blocking reason

Default operating style:

- prefer the shortest reliable browser path
- capture only lightweight evidence needed to trust the result
- avoid deep diagnostics unless the page blocks extraction
- avoid mandatory `reports/` output unless the user asks for it, the failure needs recordkeeping, or reusable knowledge is discovered

For article-style content extraction:

- preserve DOM reading order
- include real image URLs inline in the generated正文
- use Markdown image syntax instead of generic placeholders

### Workflow B: Platform/Page Analysis

This is the deep route.

Use it when the prompt is primarily asking:

- how a specific platform/page is structured
- how to analyze or debug extraction
- how to collect evidence
- how to summarize lessons for future runs
- how to inspect page behavior, structure, or capture rules

Expected output:

- a complete report with evidence
- structural findings
- failures and next actions
- reusable knowledge updates when justified

Default operating style:

- collect full screenshots and structure clues
- keep reports under `reports/`
- update `sites/` or `docs/playbooks/` if the task yields reusable platform knowledge

## Intent Routing Rules

The workflow should start by classifying the prompt.

Default to Workflow A when:

- the user gives only a URL
- the user asks to “get”, “extract”, “read”, or “fetch” page content
- the user’s desired output is page content or a concise explanation of failure

Route to Workflow B when the prompt includes signals such as:

- `分析`
- `调试`
- `证据`
- `总结经验`
- `平台`
- `结构`
- `抓取规则`
- `复现`

If both kinds of signals appear, prefer Workflow B.

## Tooling Implications

Both workflows still use the same tool-selection policy:

- default to `chrome-devtools-mcp` for public/repeatable work
- use `chrome-cdp` only when live-session continuation materially matters

The difference is not the core browser tool. The difference is:

- evidence depth
- reporting depth
- whether direct user output is enough

## Reporting Policy

### Workflow A

Direct response is the primary deliverable.

Create a `reports/` artifact only when:

- the user explicitly asks for a saved report
- the failure is worth preserving
- the task reveals reusable extraction knowledge

### Workflow B

A saved report is the default deliverable.

## Verification Policy

### Workflow A

Verify:

- final URL
- page identity
- extracted main content or explicit failure reason

Use a light screenshot only when helpful.

### Workflow B

Verify:

- page title and URL
- screenshot evidence
- structure clue such as DOM/accessibility snapshot
- interaction outcome if relevant
- any extra evidence the analysis task requires

## Expected Outcome

This split should preserve the repository’s research value while making the common “just get the page content” task much faster and less procedural.
