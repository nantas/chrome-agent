# Browser Tooling Evaluation Playbook

## Purpose

Compare the Scrapling-first grabbing path with the Chrome fallback paths used by this repository:

- Scrapling for primary webpage grabbing
- `chrome-devtools-mcp` for structured diagnostics and evidence capture
- `chrome-cdp` for immediate continuation on an already-open live Chrome tab

## Prerequisites

- Scrapling is installed in a dedicated Python `>=3.10` environment
- the Scrapling executable path is known
- `chrome-devtools` is available to `codex`
- `.agents/skills/chrome-cdp/scripts/cdp.mjs` is present
- Chrome remote debugging can be enabled when needed
- reports are saved under `reports/`

## Scoring Rubric

### Capability Completion

How fully the path can complete the scenario goal without switching tooling.

### State Fidelity

How accurately the path reflects the browser/session state needed for the scenario.

### Diagnostic Depth

How much useful inspection/debug evidence the fallback path provides during failure analysis.

### Operational Friction

How much setup, retries, and operator effort the path requires per scenario.

## Scrapling-First Comparison Matrix

Use this matrix for primary grabbing runs. Every archetype should cover the Scrapling path first and note any fallback triggers.

| Public-site archetype | Primary Scrapling path | Read title and URL | Extract key content | Preserve inline images | Fallback trigger |
| --- | --- | --- | --- | --- | --- |
| static content page | `get` | required | required | required when present | missing content, redirect, or block |
| modern SPA | `fetch` | required | required | required when present | stale shell or incomplete rendered content |
| dynamic list or pagination page | `fetch` | required | required | optional | pagination or lazy-load ambiguity |
| protected page | `stealthy-fetch` | required | required if accessible | required when present | challenge, redirect, or anti-bot block |
| article page | `get` or `fetch` | required | required | required | missing body, missing images, or cleanup ambiguity |

Archetype definitions:

- static content page: mostly server-rendered content with little or no client-side state change needed to read key information.
- modern SPA: client-rendered app shell where navigation or data view changes happen without full page reload.
- dynamic list or pagination page: list/table/search results where key content is loaded, filtered, sorted, or paged dynamically.
- protected page: page that can require stealth or challenge handling before content becomes visible.
- article page: content page where ordered body text and inline images matter.

### Per-Scenario Success Criteria

- Read title and URL
  - Expected evidence: page title, final URL, and Scrapling path captured in notes or command output.
- Extract key content
  - Expected evidence: title, URL, one main text excerpt, and a saved output file.
- Preserve inline images
  - Expected evidence: image URLs preserved in Markdown or HTML order when the article contains images.
- Capture screenshot fallback
  - Expected evidence: one screenshot tied to the scenario and page state when Scrapling is insufficient.
- Inspect page structure fallback
  - Expected evidence: one DOM or accessibility-tree excerpt plus page URL when Chrome diagnostics are needed.
- Complete a short interaction flow fallback
  - Expected evidence: before/after state note and one screenshot or DOM/state excerpt when browser interaction is needed.

## Live-Session and Light-Stability Matrix

Use this matrix when the evaluation depends on an existing browser session or short, repeated follow-up actions.

| Scenario | Why it matters | Minimum evidence |
| --- | --- | --- |
| continuing on an already-open tab | Validates whether the fallback path can attach to and act on an existing tab without resetting context. | tab identity note, URL, and one state-preserving action result |
| reading a logged-in page | Confirms whether authenticated content can be read from an existing signed-in session. | page URL, key content excerpt, and authentication-state note |
| preserving UI state such as expanded panels, scroll position, or unsaved input | Checks state fidelity when the page has in-progress UI context that must not be lost. | before/after state notes and one screenshot or state excerpt |
| light switching across 3-5 tabs | Measures practical overhead and reliability for short tab-hopping workflows. | tab sequence log and one successful action per tab |
| comparing first connection versus follow-up actions | Separates initial attach/setup cost from repeated operational cost in the same session. | timing or step-count notes for first connection and follow-up actions |

### Authenticated Read-Only Guidance

When evaluating authenticated pages in a real user session:

- require explicit user approval for the exact target page URL before running either tool
- default to read-only actions only (`title`, `url`, excerpt, snapshot, screenshot, timing), unless the user explicitly broadens scope
- avoid interacting with unrelated tabs; if discovery requires `list`/`list_pages`, act only on the approved target once identified
- record one authentication-state clue in evidence, for example account handle visible, signed-in nav element present, or stable authenticated URL context
- immediately stop and record failure if the flow triggers unexpected logout, redirect, write action risk, or scope drift

## Fallback Evidence Requirements

When Scrapling cannot complete the task alone, record:

- the Scrapling path used
- the exact failure stage or block reason
- the fallback tool used
- the minimal Chrome evidence required to explain the failure

For `chrome-devtools-mcp` fallback, include at least:

- page title and URL
- one key content excerpt
- one screenshot
- one structure clue such as DOM or accessibility snapshot
- one interaction outcome if the task includes a flow

For `chrome-cdp` fallback, include at least:

- explicit approved target page or tab
- read-only boundary by default unless the user broadens scope
- one authentication or session-state clue when relevant
- first-connection versus follow-up action notes
- confirmation that no unexpected reset, logout, redirect, or write-action risk occurred

## Scenario: <name>

- Scoring (Capability Completion, State Fidelity, Diagnostic Depth, Operational Friction):
- Goal:
- Archetype (matrix row):
- Context:
- Primary path:
- Fallback path:
- Steps:
- Result:
- Evidence (must satisfy Per-Scenario Success Criteria and relevant fallback evidence requirements):
- Notes:
