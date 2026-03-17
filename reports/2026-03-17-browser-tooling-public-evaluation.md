# Browser Tooling Public-Site Evaluation (2026-03-17)

## Scope
This report compares `chrome-devtools-mcp` and `chrome-cdp` on four public-site archetypes:

- Static content page: `https://example.com`
- Modern SPA: `https://todomvc.com/examples/react/dist/`
- Dynamic list/pagination page: `https://news.ycombinator.com/news`
- Standard form page: `https://httpbin.org/forms/post`

Scoring dimensions used throughout:

- `Capability Completion`
- `State Fidelity`
- `Diagnostic Depth`
- `Operational Friction`

Scoring scale: `1` (weak) to `5` (strong).

## Scenario Findings

### 1) Static Content Page (`https://example.com`)

**Outcome**
- `chrome-devtools-mcp`: Success
- `chrome-cdp`: Success after rerun with explicit navigation

**Evidence**
- DevTools MCP screenshot: [browser-tooling-public-devtools-static.png](./browser-tooling-public-devtools-static.png)
- CDP screenshot: [browser-tooling-public-cdp-static.png](./browser-tooling-public-cdp-static.png)
- Both tools retrieved `Example Domain` title/header and followed `Learn more` to IANA (`Example Domains`).
- DevTools MCP snapshot exposed `RootWebArea`, heading, and link semantics.
- CDP DOM sample confirmed expected `<h1>Example Domain</h1>`.

**Friction Notes**
- `chrome-cdp` had an initial attach/navigation mismatch: first eval returned `about:blank` until explicit `nav` was issued.
- `chrome-devtools-mcp` completed in a direct flow without this attach-state correction.

**Preliminary Conclusion**
- Both tools are capable on basic static pages, but CDP showed higher setup sensitivity in this case.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 4 | 5 |
| chrome-cdp | 5 | 4 | 4 | 3 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 5` because observed page state matched expected title/content and flow ran without attach-state correction.
- `chrome-cdp`: `4 / 3` because final state matched after explicit `nav`, but the initial `about:blank` attach mismatch added operator overhead.

### 2) Modern SPA (`https://todomvc.com/examples/react/dist/`)

**Outcome**
- `chrome-devtools-mcp`: Success
- `chrome-cdp`: Success

**Evidence**
- DevTools MCP screenshot: [browser-tooling-public-devtools-spa.png](./browser-tooling-public-devtools-spa.png)
- CDP screenshot: [browser-tooling-public-cdp-spa.png](./browser-tooling-public-cdp-spa.png)
- Both tools validated page identity (`TodoMVC: React`, heading `todos`).
- DevTools MCP used native-like actions (`fill`, `Enter`, checkbox click) and observed `0 items left!`.
- CDP used script-driven DOM events (`input` + `keydown`) and checkbox click; confirmed `itemsLeft: "0 items left!"` and `hasTodo: true`.

**Friction Notes**
- DevTools MCP flow was straightforward through interaction primitives.
- CDP required lower-level event dispatch control, which is flexible but more operator-dependent.

**Preliminary Conclusion**
- Both can drive SPA state transitions. DevTools MCP appears lower-friction for typical user-journey flows; CDP offers fine-grained control.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 4 | 5 |
| chrome-cdp | 5 | 5 | 4 | 4 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 5` because todo creation/completion and `0 items left!` reflected expected SPA state with native-like actions.
- `chrome-cdp`: `5 / 4` because state outcomes were equivalent, but achieving them required lower-level event scripting and more manual control.

### 3) Dynamic List/Pagination (`https://news.ycombinator.com/news`)

**Outcome**
- `chrome-devtools-mcp`: Success
- `chrome-cdp`: Success

**Evidence**
- DevTools MCP screenshot: [browser-tooling-public-devtools-pagination.png](./browser-tooling-public-devtools-pagination.png)
- CDP screenshot: [browser-tooling-public-cdp-pagination.png](./browser-tooling-public-cdp-pagination.png)
- Both tools captured first story title and navigated via `More` to `?p=2`.
- DevTools MCP snapshot exposed accessible list/link structure.
- CDP diagnostic sample included network timing rows for CSS/image/script assets.

**Friction Notes**
- No major flow blockers in either tool.
- CDP exposed network-level artifacting directly in this run.

**Preliminary Conclusion**
- For pagination and list traversal, both are functionally equivalent in this sample; CDP showed a slight edge in immediate low-level diagnostics.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 4 | 5 |
| chrome-cdp | 5 | 5 | 5 | 4 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 5` because story extraction and `More` navigation to `?p=2` were consistent with expected page transitions in a direct flow.
- `chrome-cdp`: `5 / 4` because state transitions matched equally well, but the flow still carried slightly higher operator involvement than MCP.

### 4) Standard Form (`https://httpbin.org/forms/post`)

**Outcome**
- `chrome-devtools-mcp`: Success
- `chrome-cdp`: Success

**Evidence**
- DevTools MCP screenshot: [browser-tooling-public-devtools-form.png](./browser-tooling-public-devtools-form.png)
- CDP screenshot: [browser-tooling-public-cdp-form.png](./browser-tooling-public-cdp-form.png)
- Both tools filled customer fields, selected size/topping, submitted, and verified landed state at `https://httpbin.org/post` with submitted values.
- DevTools MCP diagnostics sampled:
  - network: `POST https://httpbin.org/post [200]`
  - console: no messages
- CDP DOM sample captured full form structure and post-submit result excerpt.

**Friction Notes**
- DevTools MCP leveraged direct form primitives with low ceremony.
- CDP achieved equivalent outcome through scripted field mutation/submission.

**Preliminary Conclusion**
- Both tools completed standard form workflows cleanly; diagnostic extraction was adequate in both paths.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 5 | 5 |
| chrome-cdp | 5 | 5 | 4 | 4 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 5` because submitted values and destination URL matched expectations using direct form interaction primitives.
- `chrome-cdp`: `5 / 4` because post-submit state matched, but the scripted mutation/submission path required more manual orchestration.

## Cross-Scenario Comparison (Public Sites Only)

Observed pattern from this public run:

- `Capability Completion`: effectively tied; both completed all four archetypes.
- `State Fidelity`: effectively tied after explicit navigation correction in CDP static case.
- `Diagnostic Depth`: slight split by workflow; CDP surfaced low-level DOM/network views naturally, while DevTools MCP combined accessibility snapshotting with explicit network/console listing.
- `Operational Friction`: DevTools MCP appeared lower-friction for direct interaction flows; CDP offered power/flexibility with somewhat higher operator burden (notably the initial `about:blank` attach case).

## Preliminary Readout

This is a public-site evaluation only. It supports a provisional view that both toolchains are viable for baseline browsing, interaction, and verification tasks, with a likely tradeoff of:

- `chrome-devtools-mcp`: stronger default ergonomics for repeatable user-journey execution
- `chrome-cdp`: stronger low-level control surface when explicit DOM/event/network manipulation is desired

These findings should be treated as directional input, not a final workflow decision without complementary authenticated/internal-site evaluation.
