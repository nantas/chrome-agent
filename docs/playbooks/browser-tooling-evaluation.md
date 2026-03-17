# Browser Tooling Evaluation Playbook

## Purpose

Compare `chrome-devtools-mcp` and `chrome-cdp` for this repository's real browser workflows.

## Prerequisites

- `codex` can see the `chrome-devtools` MCP server
- `.agents/skills/chrome-cdp/scripts/cdp.mjs` is present
- Chrome remote debugging can be enabled when needed
- reports are saved under `reports/`

## Scoring Rubric

### Capability Completion

How fully the tool can complete the scenario goal without switching tooling.

### State Fidelity

How accurately the tool reflects the browser/session state needed for the scenario.

### Diagnostic Depth

How much useful inspection/debug evidence the tool provides during failure analysis.

### Operational Friction

How much setup, retries, and operator effort the tool requires per scenario.

## Public-Site Core Comparison Matrix

Use this matrix for public-site evaluation runs. Every archetype should cover every core scenario.

| Public-site archetype | Read title and URL | Extract key content | Capture screenshot | Inspect page structure | Complete a short interaction flow |
| --- | --- | --- | --- | --- | --- |
| static content page | required | required | required | required | required |
| modern SPA | required | required | required | required | required |
| dynamic list or pagination page | required | required | required | required | required |
| standard form page | required | required | required | required | required |

Archetype definitions (for consistent tagging):

- static content page: mostly server-rendered content with little or no client-side state change needed to read key information (for example: docs article, blog post, marketing page).
- modern SPA: client-rendered app shell where navigation or data view changes happen without full page reload (for example: dashboard-style routes in a single-page app).
- dynamic list or pagination page: list/table/search results where key content is loaded, filtered, sorted, or paged dynamically (for example: catalog, issue list, infinite-scroll feed).
- standard form page: page whose primary task is entering and submitting form fields, with basic validation or confirmation behavior.

### Per-Scenario Success Criteria

- Read title and URL
  - Expected evidence: page title and current URL captured in notes or command output.
- Extract key content
  - Expected evidence: title, URL, one main text excerpt, and one screenshot.
- Capture screenshot
  - Expected evidence: one clearly labeled screenshot tied to the scenario and page state.
- Inspect page structure
  - Expected evidence: one DOM or accessibility-tree excerpt showing relevant structure plus page URL.
- Complete a short interaction flow
  - Expected evidence: before/after state note and one screenshot or DOM/state excerpt.

## Live-Session and Light-Stability Matrix

Use this matrix when the evaluation depends on an existing browser session or short, repeated follow-up actions.

| Scenario | Why it matters | Minimum evidence |
| --- | --- | --- |
| continuing on an already-open tab | Validates whether the tool can attach to and act on an existing tab without resetting context. | tab identity note, URL, and one state-preserving action result |
| reading a logged-in page | Confirms whether authenticated content can be read from an existing signed-in session. | page URL, key content excerpt, and authentication-state note |
| preserving UI state such as expanded panels, scroll position, or unsaved input | Checks state fidelity when the page has in-progress UI context that must not be lost. | before/after state notes and one screenshot or state excerpt |
| light switching across 3-5 tabs | Measures practical overhead and reliability for short tab-hopping workflows. | tab sequence log and one successful action per tab |
| comparing first connection versus follow-up actions | Separates initial attach/setup cost from repeated operational cost in the same session. | timing or step-count notes for first connection and follow-up actions |

### Authenticated Read-Only Guidance

When evaluating authenticated pages in a real user session:

- require explicit user approval for the exact target page URL before running either tool
- default to read-only actions only (`title`, `url`, excerpt, snapshot, screenshot, timing), unless the user explicitly broadens scope
- avoid interacting with unrelated tabs; if discovery requires `list`/`list_pages`, act only on the approved target once identified
- record one authentication-state clue in evidence (for example: account handle visible, signed-in nav element present, or stable authenticated URL context)
- immediately stop and record failure if the flow triggers unexpected logout, redirect, write action risk, or scope drift

## Scenario: <name>

- Scoring (Capability Completion, State Fidelity, Diagnostic Depth, Operational Friction):
- Goal:
- Archetype (matrix row):
- Context:
- Tool:
- Steps:
- Result:
- Evidence (must satisfy Per-Scenario Success Criteria and relevant matrix minimum evidence):
- Notes:
