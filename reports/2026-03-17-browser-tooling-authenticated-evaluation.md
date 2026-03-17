# Browser Tooling Authenticated Evaluation (2026-03-17)

## Scope

- Target page: `https://atomgit.com/nantas1/game-design-patterns`
- Interaction policy: read-only inspection only; no navigation, edits, or writes

## Setup Assumptions And Limits

- The approved page is already open in the user's logged-in live Chrome session.
- Tool-specific attach assumptions and observed limits will be filled during execution.

## Scenario Findings

### 1) Authenticated Page Attach And Follow-Up Reads (`chrome-cdp`)

**Outcome**
- `chrome-cdp`: Success

**Evidence**
- Target ID: `5337A811`
- Page identity from both reads:
  - title: `game-design-patterns - AtomGit | GitCode`
  - url: `https://atomgit.com/nantas1/game-design-patterns`
- Content excerpt from page main/body (first and second read):
  - `G nantas1 / game-design-patterns ... docs: add first-pass awesome-game-design postmortems ...`
- State signal:
  - `scrollY: 0` on both reads
  - `authClue: true` from `document.body.innerText.includes("nantas1")` on both reads
- Screenshot:
  - [browser-tooling-authenticated-cdp-atomgit.png](./browser-tooling-authenticated-cdp-atomgit.png)

**First vs Follow-Up Timing Notes**
- First read-only eval: about `0.07s` (`real`)
- Second read-only eval: about `0.05s` (`real`)

**Friction Notes**
- This run succeeded after the user accepted Chrome's remote debugging `Allow` prompt.
- Once permission was active, repeated read-only access was direct with no additional page interaction.
- No page navigation, mutation, or visible state reset was observed.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-cdp | 5 | 5 | 4 | 4 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-cdp`: `5 / 4` because both reads stayed on the authenticated target page and preserved visible state, with low follow-up overhead after one-time permission acceptance.

### 2) Authenticated Page Attach And Follow-Up Reads (`chrome-devtools-mcp`)

**Outcome**
- `chrome-devtools-mcp`: Success

**Attach Method**
- `--autoConnect --no-usage-statistics`

**Evidence**
- Page identifier from `list_pages`: page `1` (`https://atomgit.com/nantas1/game-design-patterns`) and selected before reads.
- Page identity from both reads:
  - title: `game-design-patterns - AtomGit | GitCode`
  - url: `https://atomgit.com/nantas1/game-design-patterns`
- Content excerpt from page main/body (first and second read):
  - `G nantas1 / game-design-patterns ... docs: add first-pass awesome-game-design postmortems ...`
- State signal:
  - `scrollY: 0` on both reads
  - `authClue: true` from `document.body.innerText.includes('nantas1')` on both reads
- Structure excerpt from `take_snapshot`:
  - `RootWebArea "game-design-patterns - AtomGit | GitCode"`
  - link `nantas1` and link `game-design-patterns` both present
- Screenshot:
  - [browser-tooling-authenticated-devtools-atomgit.png](./browser-tooling-authenticated-devtools-atomgit.png)

**First vs Follow-Up Timing Notes**
- First read-only eval: about `804ms`
- Second read-only eval: about `207ms`

**Friction Notes**
- `--autoConnect` found the approved authenticated page directly in this run.
- No fallback to `--wsEndpoint` was required.
- No page navigation, mutation, or visible state reset was observed.

**Scores**
| Tool | Capability Completion | State Fidelity | Diagnostic Depth | Operational Friction |
|---|---:|---:|---:|---:|
| chrome-devtools-mcp | 5 | 5 | 5 | 4 |

**Score Rationale (State Fidelity / Operational Friction)**
- `chrome-devtools-mcp`: `5 / 4` because both reads stayed on the authenticated target and preserved visible state, with low follow-up overhead after attach.

## Cross-Scenario Comparison (Authenticated Only)

To be filled during execution.

## Preliminary Readout

To be filled during execution.
