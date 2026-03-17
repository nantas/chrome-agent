# Browser Tooling Research Design

## Goal

Define the core workflow for this repository when using `chrome-devtools-mcp` and `chrome-cdp` together, then design research test cases that can validate when each tool should be the default choice, when each should be a specialist path, and when both are interchangeable.

## Current Repository Context

The repository already states a default/supplemental split:

- Default path: `chrome-devtools-mcp`
- Supplemental path: `chrome-cdp-skill`

That split is directionally useful, but still too vague for future browser tasks. The repository needs a workflow that answers:

- Which tool should be used first for a new task?
- What evidence should trigger switching tools?
- Which scenarios justify keeping both tools instead of consolidating on one?

## External Capability Assumptions

These assumptions are the starting point for the research, not the final conclusion.

### `chrome-devtools-mcp`

Official documentation presents it as a general DevTools-backed MCP server for:

- reliable automation
- screenshots and browser inspection
- network and console debugging
- performance analysis

It also supports connecting to a running Chrome instance through `--autoConnect` or `--browser-url`, so it is not limited to isolated browser launches.

### `chrome-cdp`

Official documentation presents it as a lightweight direct-CDP tool optimized for:

- reusing the tabs the user already has open
- preserving logged-in/live-session state
- avoiding repeated "Allow debugging" prompts by keeping per-tab daemons alive
- working reliably across many open tabs

## Working Hypothesis

The split should not be defined by command overlap alone. Both tools cover enough shared actions that comparing only `click`, `eval`, `nav`, or `screenshot` would be misleading.

The more meaningful boundary is expected to be:

1. Browser context source
   - isolated or explicitly attached debugging context
   - user’s current live Chrome state
2. Task goal
   - content extraction and routine automation
   - DevTools-grade diagnostics and performance debugging
3. Connection behavior
   - one-off or short flows
   - multi-step continuation on the same existing tab with minimal reconnect friction

Initial hypothesis:

- `chrome-devtools-mcp` should remain the default path for most browser tasks, especially when diagnostics, structured automation, or repeatable debugging matter.
- `chrome-cdp` should remain available as a specialist path for live-session continuation, logged-in workflows, and cases where reconnect friction or tab scale noticeably hurts the task.
- If both tools complete a task equally well, the repository should bias toward `chrome-devtools-mcp` to preserve one clear default.

## Research Scope

### In Scope

- public websites as the main test surface
- a smaller set of live-session tests against already-open Chrome tabs
- tool overlap in content parsing, page interaction, and navigation
- tool differences in state continuity, diagnostics, and connection friction
- lightweight stability coverage for repeated access and light tab switching

### Out of Scope

- high-volume load testing
- credential management
- large automation frameworks
- claiming one tool should replace the other before evidence exists

## Test Matrix Structure

The test program should be divided into three layers.

### 1. Core Comparison Set

Purpose: measure the overlapping area on public sites.

Test classes:

- read page title, URL, main text, and key DOM fragments
- capture screenshot evidence
- extract structural signals such as headings or accessibility tree output
- navigate to a target URL
- perform simple interaction such as click, input, submit, or reveal-more
- complete a short 3-5 step browser flow on the same page

Public site archetypes:

- static content page
- modern single-page application
- dynamic list or paginated content page
- standard form flow

### 2. Specialist Comparison Set

Purpose: measure the likely boundaries where the workflow should branch.

#### Live-session scenarios

- continue work on a tab the user already opened manually
- read content from a logged-in page
- preserve current UI state such as expanded sections, scroll position, or unsaved input
- continue across multiple existing tabs in the same user session

#### DevTools-diagnostics scenarios

- inspect console messages
- inspect network requests
- capture performance traces or insights
- compare the amount and quality of debugging evidence available

### 3. Lightweight Stability Set

Purpose: validate practical friction without turning this into a benchmark suite.

Test classes:

- re-enter the same tab for repeated actions
- light switching across 3-5 tabs
- compare first-connection behavior versus follow-up interactions
- note repeated permission prompts, reconnect pain, or target-discovery issues

## Evaluation Dimensions

Each test case should record four judgments.

### Capability Completion

Did the tool actually complete the requested task with correct output?

### State Fidelity

Did the tool preserve and operate on the real page state the user cared about, rather than a reset or simplified state?

### Diagnostic Depth

How much useful debugging evidence did the tool expose for this scenario?

### Operational Friction

How much setup, reconnect cost, permission churn, or manual cleanup was required?

## Evidence Requirements

Each run should capture:

- task goal
- target site archetype or concrete page
- tool path used
- whether the browser context was isolated, attached, or live-session reuse
- exact high-level steps attempted
- outcome: success, partial success, or failure
- key evidence such as screenshot, extracted output, console/network/perf artifacts, or notes on state preservation
- next recommended action

## Decision Rules

The final repository workflow should be derived from evidence using these rules:

1. If a scenario depends on DevTools-grade diagnostics and `chrome-devtools-mcp` clearly provides better evidence, that scenario belongs to the default `chrome-devtools-mcp` workflow.
2. If a scenario depends on continuing an already-open live Chrome tab and `chrome-cdp` clearly lowers friction or preserves state better, that scenario belongs to the specialist `chrome-cdp` workflow.
3. If both tools succeed and no specialist advantage is demonstrated, prefer `chrome-devtools-mcp` as the repository default.
4. Only promote `chrome-cdp` to a first-choice path for a scenario when the research produces specific, repeatable evidence that it is materially better.

## Planned Repository Outputs

This design should lead to three concrete assets:

1. A reusable evaluation playbook in `docs/playbooks/`
2. A research automation plan in `docs/plans/`
3. A final workflow decision record in `docs/decisions/`

## Risks

- Public-site coverage may hide the true value of live-session workflows if the live-session set is too small.
- Live-session tests can be hard to compare unless the evidence template is strict.
- Official claims about connection friction or multi-tab reliability may not hold equally in this repository’s actual environment and must be validated rather than copied into policy.

## References

- Chrome DevTools MCP README: https://github.com/ChromeDevTools/chrome-devtools-mcp
- chrome-cdp README: https://github.com/pasky/chrome-cdp-skill
