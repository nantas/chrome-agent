# Browser Tooling Research Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a reusable browser-tooling evaluation workflow that compares `chrome-devtools-mcp` and `chrome-cdp`, captures evidence from public and live-session scenarios, and ends with a repository-specific tool-selection decision.

**Architecture:** Build the work in three layers. First, create the reusable evaluation documents that define scenarios, evidence collection, and automation boundaries. Next, execute the public-site and live-session comparison runs and save reports under `reports/`. Finally, synthesize the evidence into a workflow decision and update repository guidance so future tasks know when to use each tool.

**Tech Stack:** Markdown docs, repository-local `chrome-cdp` skill, project-scoped `chrome-devtools-mcp`, Chrome/Chromium, Codex browser tooling, git

---

Use `@superpowers:verification-before-completion` before claiming any report or decision is complete. If either tool behaves unexpectedly during execution, stop and use `@superpowers:systematic-debugging` before changing the workflow rules.

### Task 1: Create the Shared Evaluation Playbook Skeleton

**Files:**
- Create: `docs/playbooks/browser-tooling-evaluation.md`

**Step 1: Write the playbook header and prerequisites**

Add sections for purpose, repository assumptions, required browser setup, and evidence storage.

```markdown
# Browser Tooling Evaluation Playbook

## Purpose

Compare `chrome-devtools-mcp` and `chrome-cdp` for this repository's real browser workflows.

## Prerequisites

- `codex` can see the `chrome-devtools` MCP server
- `.agents/skills/chrome-cdp/scripts/cdp.mjs` is present
- Chrome remote debugging can be enabled when needed
- reports are saved under `reports/`
```

**Step 2: Add the scoring rubric and evidence template**

Add a section that defines:

- `Capability Completion`
- `State Fidelity`
- `Diagnostic Depth`
- `Operational Friction`

Add a reusable result template like:

```markdown
## Scenario: <name>

- Goal:
- Context:
- Tool:
- Steps:
- Result:
- Evidence:
- Notes:
```

**Step 3: Verify the playbook contains the required sections**

Run:

```bash
rg -n "## Purpose|## Prerequisites|Capability Completion|Operational Friction|## Scenario:" docs/playbooks/browser-tooling-evaluation.md
```

Expected: five matches covering the new playbook sections.

**Step 4: Commit**

```bash
git add docs/playbooks/browser-tooling-evaluation.md
git commit -m "docs: add browser tooling evaluation playbook skeleton"
```

### Task 2: Add the Public-Site Core Comparison Matrix

**Files:**
- Modify: `docs/playbooks/browser-tooling-evaluation.md`

**Step 1: Add the public-site archetype matrix**

Create a table or checklist that covers these archetypes:

- static content page
- modern SPA
- dynamic list or pagination page
- standard form page

For each archetype, include core scenarios:

- read title and URL
- extract key content
- capture screenshot
- inspect page structure
- complete a short interaction flow

**Step 2: Add per-scenario success criteria**

For each scenario, define the expected evidence. Example:

```markdown
- Extract key content
  - Expected evidence: title, URL, one main text excerpt, and one screenshot
- Complete a short interaction flow
  - Expected evidence: before/after state note and one screenshot or DOM/state excerpt
```

**Step 3: Verify the public-site matrix is present**

Run:

```bash
rg -n "static content page|modern SPA|dynamic list|standard form page|Extract key content|short interaction flow" docs/playbooks/browser-tooling-evaluation.md
```

Expected: matches for all archetypes and scenario labels.

**Step 4: Commit**

```bash
git add docs/playbooks/browser-tooling-evaluation.md
git commit -m "docs: add public site browser tooling matrix"
```

### Task 3: Add Live-Session, Stability, and Automation-Boundary Guidance

**Files:**
- Modify: `docs/playbooks/browser-tooling-evaluation.md`
- Create: `docs/plans/2026-03-17-browser-tooling-research-automation-plan.md`

**Step 1: Add the live-session and light-stability matrix**

Add scenarios for:

- continuing on an already-open tab
- reading a logged-in page
- preserving UI state such as expanded panels, scroll position, or unsaved input
- light switching across 3-5 tabs
- comparing first connection versus follow-up actions

**Step 2: Write the automation-boundary document**

Create a plan doc that separates:

- fully automatable public-site checks
- semi-automatable checks that still need human judgment
- manual-only live-session checks

Start it with:

```markdown
# Browser Tooling Research Automation Plan

## Automatable Checks

## Semi-Automatable Checks

## Manual-Only Checks
```

**Step 3: Verify both documents contain the required sections**

Run:

```bash
rg -n "already-open tab|logged-in page|3-5 tabs|first connection|follow-up actions" docs/playbooks/browser-tooling-evaluation.md
rg -n "## Automatable Checks|## Semi-Automatable Checks|## Manual-Only Checks" docs/plans/2026-03-17-browser-tooling-research-automation-plan.md
```

Expected: both commands return matches.

**Step 4: Commit**

```bash
git add docs/playbooks/browser-tooling-evaluation.md docs/plans/2026-03-17-browser-tooling-research-automation-plan.md
git commit -m "docs: add live session matrix and automation boundaries"
```

### Task 4: Run the Public-Site Comparison and Save a Report

**Files:**
- Create: `reports/2026-03-17-browser-tooling-public-evaluation.md`
- Create: `reports/browser-tooling-public-*.png`

**Step 1: Verify the local tool entrypoints before running scenarios**

Run:

```bash
codex -C /Users/nantasmac/projects/agentic/chrome-agent mcp get chrome-devtools
test -f .agents/skills/chrome-cdp/scripts/cdp.mjs && echo "chrome-cdp present"
```

Expected:

- `codex` prints the configured `chrome-devtools` MCP server
- shell prints `chrome-cdp present`

**Step 2: Execute the public-site matrix with `chrome-devtools-mcp`**

Using the playbook, run the selected public-site archetypes through the MCP path and save:

- content extraction notes
- interaction results
- at least one screenshot per archetype when relevant
- any debugging evidence that materially helps evaluation

**Step 3: Execute the same public-site matrix with `chrome-cdp`**

Use the same archetypes and scenario order, then save comparable evidence and note any setup differences.

**Step 4: Write the public evaluation report**

Organize the report by scenario, and for each tool record:

- outcome
- evidence
- friction notes
- preliminary conclusion

**Step 5: Verify the report includes both tools and all four scoring dimensions**

Run:

```bash
rg -n "chrome-devtools-mcp|chrome-cdp|Capability Completion|State Fidelity|Diagnostic Depth|Operational Friction" reports/2026-03-17-browser-tooling-public-evaluation.md
```

Expected: matches for both tool names and all four scoring dimensions.

**Step 6: Commit**

```bash
git add reports/2026-03-17-browser-tooling-public-evaluation.md reports/browser-tooling-public-*.png
git commit -m "reports: add public browser tooling comparison"
```

### Task 5: Run the Live-Session and Light-Stability Comparison

**Files:**
- Create: `reports/2026-03-17-browser-tooling-live-session-evaluation.md`
- Create: `reports/browser-tooling-live-session-*.png`

**Step 1: Prepare the browser context**

Open the real Chrome session needed for comparison:

- one already-open public tab with changed state
- one logged-in tab if the user approves
- 3-5 tabs total for the light stability pass

Record the setup assumptions in the report before running either tool.

**Step 2: Attempt the live-session scenarios with `chrome-devtools-mcp`**

Try the already-open tab and logged-in/live-state scenarios first. Record whether the tool can attach cleanly, preserve state, and avoid disruptive resets.

**Step 3: Attempt the same scenarios with `chrome-cdp`**

Run the same sequence and explicitly note:

- connection flow
- repeated permission prompts
- target discovery quality
- friction across repeated entry to the same tab

**Step 4: Write the live-session report**

Include:

- live-session outcome comparison
- light stability observations
- any scenario where one tool clearly outperformed the other
- any scenario that remained inconclusive

**Step 5: Verify the report documents both live-session and stability coverage**

Run:

```bash
rg -n "logged-in|already-open tab|3-5 tabs|first connection|follow-up|chrome-devtools-mcp|chrome-cdp" reports/2026-03-17-browser-tooling-live-session-evaluation.md
```

Expected: matches for live-session terms, stability terms, and both tool names.

**Step 6: Commit**

```bash
git add reports/2026-03-17-browser-tooling-live-session-evaluation.md reports/browser-tooling-live-session-*.png
git commit -m "reports: add live session browser tooling comparison"
```

### Task 6: Write the Workflow Decision and Update Repository Guidance

**Files:**
- Create: `docs/decisions/2026-03-17-browser-tooling-workflow.md`
- Modify: `AGENTS.md`
- Modify: `README.md`

**Step 1: Write the final decision record**

Capture:

- final default path
- specialist path(s)
- switching triggers
- scenarios that remain undecided

Start with:

```markdown
# Browser Tooling Workflow Decision

## Decision

## Evidence Summary

## Default Path

## Specialist Path

## Switching Triggers
```

**Step 2: Update repository guidance**

Revise `AGENTS.md` and `README.md` so they reflect the evidence-backed workflow instead of the earlier placeholder split.

**Step 3: Verify the repository docs agree on the workflow**

Run:

```bash
rg -n "Default path|Supplemental path|Specialist path|Switching" AGENTS.md README.md docs/decisions/2026-03-17-browser-tooling-workflow.md
```

Expected: matches that show the same workflow vocabulary across the decision doc and repository guidance.

**Step 4: Commit**

```bash
git add docs/decisions/2026-03-17-browser-tooling-workflow.md AGENTS.md README.md
git commit -m "docs: record browser tooling workflow decision"
```
