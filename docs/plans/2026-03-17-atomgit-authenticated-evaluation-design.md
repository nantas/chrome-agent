# AtomGit Authenticated Evaluation Design

## Goal

Design a minimal but decision-relevant authenticated-only research pass that validates how `chrome-devtools-mcp` and `chrome-cdp` behave on an already-open, logged-in real Chrome page without performing any write actions.

## Current Repository Context

The repository already has:

- a browser-tooling workflow decision in `docs/decisions/2026-03-17-browser-tooling-workflow.md`
- a reusable comparison playbook in `docs/playbooks/browser-tooling-evaluation.md`
- public-site comparison evidence in `reports/2026-03-17-browser-tooling-public-evaluation.md`
- live-session evidence from a public Gemini share page in `reports/2026-03-17-browser-tooling-live-session-evaluation.md`

That evidence is good enough to define a default path and specialist path, but one gap remains open: the workflow is not yet backed by authenticated-only evidence from a real logged-in page.

## Research Target

Approved authenticated target:

- `https://atomgit.com/nantas1/game-design-patterns`

Assumptions confirmed with the user:

- the page is already open in the user's currently logged-in Chrome session
- only read-only inspection is allowed
- screenshots and small structured excerpts are allowed as evidence

## Working Hypothesis

The existing workflow likely remains correct:

- `chrome-devtools-mcp` stays the default path for structured diagnostics and repeatable browser tasks
- `chrome-cdp` stays the specialist path when the current agent session must immediately continue on the user's already-open live tab

The authenticated-only run is intended to validate or refine that split, not replace it.

## Scope

### In Scope

- one already-open authenticated page in the user's real Chrome session
- read-only evidence collection only
- comparison of first attach versus follow-up reads
- comparison of state preservation across repeated reads
- whether the page remains in the expected logged-in context for both tools

### Out of Scope

- any write action, form submission, or repository mutation on AtomGit
- opening or inspecting unrelated user tabs
- broad multi-tab stability coverage in this pass
- credential handling or login automation

## Test Scenarios

This pass should stay narrow and only cover three scenarios.

### 1. Authenticated Page Attach And Read

For each tool:

- attach to the already-open authenticated page
- capture title and URL
- capture one visible content excerpt
- capture one structure excerpt
- capture one screenshot
- note one logged-in-state clue visible on the page

Purpose:

- verify that the tool can read the correct authenticated page rather than a reset or anonymous state

### 2. State Preservation And Follow-Up Read

For each tool:

- perform one initial read
- perform one follow-up read on the same page
- compare visible state clues such as scroll position, page heading, or authenticated UI markers
- record whether anything resets, reloads, or drops the logged-in context

Purpose:

- validate `State Fidelity` on a real authenticated page

### 3. First Attach Versus Follow-Up Friction

For each tool:

- record how the page is discovered
- note initial attach/setup friction
- note whether repeated reads are easier after the first attach
- compare the amount of operator effort needed to stay on the same page

Purpose:

- determine whether authenticated live-session work should change the current switching guidance

## Evidence Requirements

The authenticated report must include:

- target page and explicit read-only boundary
- browser context source: current logged-in Chrome session
- tool path used
- attach method used
- outcome per scenario
- screenshot links
- small content/structure excerpts
- scoring across:
  - `Capability Completion`
  - `State Fidelity`
  - `Diagnostic Depth`
  - `Operational Friction`
- final conclusion stating whether the existing workflow decision changes

## Risk Controls

- never click buttons that might trigger write operations
- never edit fields or submit anything
- never navigate away from the approved page
- never inspect unrelated tabs
- keep evidence minimal and task-relevant
- if either tool causes a login reset, redirect, or unexpected page transition, stop that path immediately and record the failure

## Expected Repository Outputs

This design should produce:

1. a new authenticated evaluation report under `reports/`
2. optional playbook clarification if authenticated-only execution needs tighter guidance
3. optional workflow-decision refinement if the authenticated evidence materially changes the current split

## Decision Criteria

Use these criteria to interpret the outcome:

1. If both tools can read the authenticated page without resetting state, the existing workflow likely stands.
2. If `chrome-cdp` clearly shows lower attach friction in the current live session while `chrome-devtools-mcp` still provides richer structure once attached, keep the current default/specialist split.
3. Only change the workflow decision if the authenticated page demonstrates a materially different boundary than the public-site and public live-session evidence already showed.
