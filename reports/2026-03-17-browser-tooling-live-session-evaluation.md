# Browser Tooling Live-Session Evaluation (2026-03-17)

## Scope

This report compares `chrome-devtools-mcp` and `chrome-cdp` against one already-open live Chrome tab approved by the user:

- Target tab: `https://gemini.google.com/share/65807830eb9c`
- Browser context: user's existing stable Chrome session with remote debugging enabled
- Interaction policy: read-only inspection only; no navigation away from the page and no destructive actions

Scoring dimensions used throughout:

- `Capability Completion`
- `State Fidelity`
- `Diagnostic Depth`
- `Operational Friction`

Scoring scale: `1` (weak) to `5` (strong).

## Setup Assumptions And Limits

- The approved live target was a public Gemini share page inside the user's signed-in browser session, not an authenticated-only destination page.
- No additional live tabs were opened for this run, so the `3-5 tabs` light-stability scenario was not executed.
- The current Codex session's built-in `chrome-devtools` tool was still attached to the earlier public-site browser context, so live-session MCP checks were run through a temporary local MCP client instead of the already-bound tool session.
- `chrome-devtools-mcp --browserUrl http://127.0.0.1:9222` failed in this environment because `http://127.0.0.1:9222/json/version` returned `404 Not Found`.
- `chrome-devtools-mcp` did attach successfully to the real Chrome session when started with the browser WebSocket from `DevToolsActivePort`, and `--autoConnect` also listed the same live pages successfully.

Coverage status for the live-session matrix:

- continuing on an already-open tab: covered
- preserving UI state such as current viewport and existing page content: covered
- comparing first connection versus follow-up actions: covered
- reading a logged-in page: not covered
- light switching across `3-5 tabs`: not covered

## Scenario Findings

### 1) Continuing On An Already-Open Tab (`https://gemini.google.com/share/65807830eb9c`)

**Outcome**
- `chrome-devtools-mcp`: Success after explicit live-session attach setup
- `chrome-cdp`: Success

**Evidence**
- DevTools MCP screenshot: [browser-tooling-live-session-devtools-gemini.png](./browser-tooling-live-session-devtools-gemini.png)
- CDP screenshot: [browser-tooling-live-session-cdp-gemini.png](./browser-tooling-live-session-cdp-gemini.png)
- `chrome-devtools-mcp` live attach evidence:
  - `list_pages` surfaced the already-open Gemini tab as page `1` and preserved it as selected.
  - `evaluate_script` returned title `‎Gemini - direct access to Google AI`, the same Gemini share URL, and the live page excerpt beginning with `Gemini Popular English Word Spelling Games`.
  - `take_snapshot` exposed a structured accessibility tree rooted at the Gemini share page, including the share heading, prompt headings, and response text.
- `chrome-cdp` live attach evidence:
  - `list` surfaced target `0CCE56B7` with title `‎Gemini - direct access to Google AI` and the same Gemini share URL.
  - repeated `eval` calls returned the same live page title, URL, excerpt, and `scrollY: 0` without navigation.
  - `shot` captured the current viewport and reported `DPR: 2`.

**Friction Notes**
- `chrome-devtools-mcp` could reuse the live tab, but only after choosing the correct connection path. `--browserUrl` was a dead end in this Chrome setup, while `--wsEndpoint` and `--autoConnect` worked.
- In the current already-running Codex session, switching the MCP path over to the live browser required an extra ad hoc client process because the built-in MCP binding had been established earlier against the public-site test browser.
- `chrome-cdp` was more direct for this exact situation: `list` the real tabs, pick the target ID, then read the page.

**Preliminary Conclusion**
- Both tools can continue on an already-open live Chrome tab without resetting page state.
- `chrome-cdp` had lower immediate activation friction inside an existing agent session.
- `chrome-devtools-mcp` offered richer structured page inspection once attached successfully.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 5 | 3 |
| chrome-cdp | 5 | 5 | 4 | 5 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 3` because the live Gemini tab was read accurately without reset, but getting the MCP path onto the real session required connection troubleshooting and a separate attach flow.
- `chrome-cdp`: `5 / 5` because it attached directly to the existing live tab and produced the expected title, URL, excerpt, and screenshot without reconfiguration of the current agent tooling.

### 2) Preserving Existing State And Comparing First Connection Versus Follow-Up Actions

**Outcome**
- `chrome-devtools-mcp`: Success for repeated read-only follow-up actions after attach
- `chrome-cdp`: Success for repeated read-only follow-up actions

**Evidence**
- `chrome-devtools-mcp` timing notes:
  - server initialize: about `1.6s`
  - first successful page listing after startup: about `4.8s`
  - first `evaluate_script` on the selected Gemini tab: about `250ms`
  - second `evaluate_script` on the same tab: about `216ms`
- `chrome-cdp` timing notes:
  - `list` over the live Chrome session: about `2.63s`
  - first `eval` on target `0CCE56B7`: about `70ms`
  - second `eval` on the same target: about `60ms`
- Both tools preserved the live tab URL and content across repeated reads, and both reported `scrollY: 0`.
- No navigation, reload, or UI reset was observed during the repeated reads.

**Friction Notes**
- Once `chrome-devtools-mcp` was attached to the correct live browser, follow-up reads were stable and reasonably quick.
- `chrome-cdp` had the faster repeated-read loop in this run and required less orchestration to get there.
- The `3-5 tabs` stability pass was intentionally left unrun because only one approved live target tab was provided and no extra real-browser tabs were opened during the session.
- The authenticated-page scenario remains open because this run used a public share URL, not a page gated by login.

**Preliminary Conclusion**
- The two tools overlap substantially for non-destructive live-tab inspection.
- The main difference in this run was not steady-state capability but attach/setup friction.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 4 | 5 | 5 | 3 |
| chrome-cdp | 4 | 5 | 4 | 5 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 3` because follow-up reads preserved the page state accurately, but the first attach path was materially heavier than the repeated action loop that followed.
- `chrome-cdp`: `5 / 5` because repeated reads stayed on the same live target with less setup ceremony and slightly faster follow-up timings in this sample.

## Cross-Scenario Comparison (Live Session Only)

Observed pattern from this live run:

- `Capability Completion`: tied for the covered scenarios; both tools extracted content and captured screenshots from the approved live tab.
- `State Fidelity`: tied for the covered scenarios; neither tool reset the page or lost the visible content state during read-only inspection.
- `Diagnostic Depth`: `chrome-devtools-mcp` led because the accessibility snapshot provided a more structured inspection surface than the CDP text/HTML samples alone.
- `Operational Friction`: `chrome-cdp` led inside this already-running agent session because it attached directly to the live tab without needing MCP rebinding.

## Preliminary Readout

This run does not justify treating live-session work as exclusive to either tool:

- `chrome-devtools-mcp` can reuse the real Chrome session when started in the right mode (`--wsEndpoint` or `--autoConnect` in this environment).
- `chrome-cdp` remains the cleaner tactical path when the current session already needs to continue on a live tab immediately and rebinding the MCP server would add avoidable overhead.

Scenarios still inconclusive after this run:

- authenticated-only page handling
- multi-tab (`3-5 tabs`) live-session stability
- whether a fresh agent session configured around `chrome-devtools-mcp --autoConnect` is preferable to `chrome-cdp` for repeated live-session work over a longer run
