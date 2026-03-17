# AtomGit Authenticated Evaluation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run a read-only authenticated-only comparison on the approved AtomGit page, save evidence under `reports/`, and update the repository workflow guidance if the new evidence changes or tightens the current decision.

**Architecture:** Reuse the existing browser-tooling evaluation playbook and report style instead of inventing a new format. Capture comparable evidence from `chrome-cdp` and `chrome-devtools-mcp` against the same already-open authenticated page, then fold the conclusion back into the workflow decision and playbook only where the new evidence materially improves guidance.

**Tech Stack:** Markdown docs, repo-local `chrome-cdp` CLI, `chrome-devtools-mcp` live-attach mode, Chrome remote debugging, git

---

### Task 1: Prepare The Authenticated Evaluation Report Skeleton

**Files:**
- Create: `reports/2026-03-17-browser-tooling-authenticated-evaluation.md`

**Step 1: Write the report header and boundary section**

Create the report with sections for:

- `# Browser Tooling Authenticated Evaluation (2026-03-17)`
- `## Scope`
- `## Setup Assumptions And Limits`
- `## Scenario Findings`
- `## Cross-Scenario Comparison (Authenticated Only)`
- `## Preliminary Readout`

State the approved target page exactly as:

```markdown
- Target page: `https://atomgit.com/nantas1/game-design-patterns`
- Interaction policy: read-only inspection only; no navigation, edits, or writes
```

**Step 2: Verify the report scaffold exists**

Run:

```bash
rg -n "Browser Tooling Authenticated Evaluation|Target page|read-only inspection" reports/2026-03-17-browser-tooling-authenticated-evaluation.md
```

Expected: matches for the title and boundary lines.

**Step 3: Commit**

```bash
git add reports/2026-03-17-browser-tooling-authenticated-evaluation.md
git commit -m "reports: add authenticated browser tooling report scaffold"
```

### Task 2: Capture `chrome-cdp` Evidence On The Approved Authenticated Page

**Files:**
- Modify: `reports/2026-03-17-browser-tooling-authenticated-evaluation.md`
- Create: `reports/browser-tooling-authenticated-cdp-atomgit.png`

**Step 1: Find the approved AtomGit target in the live Chrome session**

Run:

```bash
node .agents/skills/chrome-cdp/scripts/cdp.mjs list
```

Expected: one target line for `https://atomgit.com/nantas1/game-design-patterns`.

**Step 2: Run the first read-only evaluation**

Using the matching target ID, run:

```bash
/usr/bin/time -p node .agents/skills/chrome-cdp/scripts/cdp.mjs eval <target> '(() => {
  const main = document.querySelector("main");
  const text = (main?.innerText || document.body.innerText || "").trim().replace(/\s+/g, " ");
  return {
    title: document.title,
    url: location.href,
    excerpt: text.slice(0, 280),
    scrollY: window.scrollY,
    authClue: document.body.innerText.includes("nantas1")
  };
})()'
```

Expected: JSON including title, URL, excerpt, scroll position, and one authentication-state clue.

**Step 3: Run the follow-up read and capture a screenshot**

Run the same `eval` again, then:

```bash
node .agents/skills/chrome-cdp/scripts/cdp.mjs shot <target> reports/browser-tooling-authenticated-cdp-atomgit.png
```

Expected:

- second read returns the same page identity without reset
- screenshot file is created

**Step 4: Write the `chrome-cdp` section into the report**

Add:

- outcome
- evidence bullets
- first vs follow-up timing notes
- friction notes
- scores for all four dimensions

**Step 5: Verify the report mentions `chrome-cdp` and the screenshot**

Run:

```bash
rg -n "chrome-cdp|browser-tooling-authenticated-cdp-atomgit.png|Operational Friction" reports/2026-03-17-browser-tooling-authenticated-evaluation.md
```

Expected: matches for the tool name, screenshot filename, and scoring section.

**Step 6: Commit**

```bash
git add reports/2026-03-17-browser-tooling-authenticated-evaluation.md reports/browser-tooling-authenticated-cdp-atomgit.png
git commit -m "reports: add chrome cdp authenticated evaluation evidence"
```

### Task 3: Capture `chrome-devtools-mcp` Evidence On The Same Authenticated Page

**Files:**
- Modify: `reports/2026-03-17-browser-tooling-authenticated-evaluation.md`
- Create: `reports/browser-tooling-authenticated-devtools-atomgit.png`

**Step 1: Attach `chrome-devtools-mcp` to the live Chrome session**

Use `DevToolsActivePort` and prefer WebSocket attach if needed:

```bash
cat "$HOME/Library/Application Support/Google/Chrome/DevToolsActivePort"
```

Then use a small newline-delimited JSON-RPC client to start:

```bash
npx -y chrome-devtools-mcp@latest --autoConnect --no-usage-statistics
```

Fallback if required:

```bash
npx -y chrome-devtools-mcp@latest --wsEndpoint ws://127.0.0.1:<port>/devtools/browser/<id> --no-usage-statistics
```

Expected: `list_pages` can see the already-open AtomGit page.

**Step 2: Run the first and follow-up read-only evaluations**

Using MCP tools:

- `list_pages`
- `select_page`
- `evaluate_script`
- `take_snapshot`
- `take_screenshot`

The evaluation function should capture:

```js
() => {
  const main = document.querySelector('main');
  const text = (main?.innerText || document.body.innerText || '').trim().replace(/\s+/g, ' ');
  return {
    title: document.title,
    url: location.href,
    excerpt: text.slice(0, 280),
    scrollY: window.scrollY,
    authClue: document.body.innerText.includes('nantas1')
  };
}
```

Expected:

- first and second reads stay on the same authenticated page
- snapshot yields a meaningful structure excerpt
- screenshot file is created

**Step 3: Write the `chrome-devtools-mcp` section into the report**

Add:

- attach method used (`--autoConnect` or `--wsEndpoint`)
- outcome
- evidence bullets
- structure excerpt notes from `take_snapshot`
- first vs follow-up timing notes
- scores for all four dimensions

**Step 4: Verify the report mentions `chrome-devtools-mcp` and the screenshot**

Run:

```bash
rg -n "chrome-devtools-mcp|browser-tooling-authenticated-devtools-atomgit.png|Diagnostic Depth" reports/2026-03-17-browser-tooling-authenticated-evaluation.md
```

Expected: matches for the tool name, screenshot filename, and scoring section.

**Step 5: Commit**

```bash
git add reports/2026-03-17-browser-tooling-authenticated-evaluation.md reports/browser-tooling-authenticated-devtools-atomgit.png
git commit -m "reports: add devtools authenticated evaluation evidence"
```

### Task 4: Finalize The Authenticated Comparison And Update Workflow Guidance

**Files:**
- Modify: `reports/2026-03-17-browser-tooling-authenticated-evaluation.md`
- Modify: `docs/decisions/2026-03-17-browser-tooling-workflow.md`
- Modify: `docs/playbooks/browser-tooling-evaluation.md`

**Step 1: Finalize the report conclusion**

Add:

- cross-scenario comparison
- final authenticated-only readout
- whether the current workflow decision remains unchanged or needs refinement

Include explicit language for:

- current workflow stands
- or authenticated-only evidence changes switching guidance

**Step 2: Update the workflow decision with authenticated evidence**

Modify `docs/decisions/2026-03-17-browser-tooling-workflow.md` to:

- add the authenticated AtomGit run to `Evidence Summary`
- clarify the specialist-path guidance if authenticated evidence strengthens it
- remove `authenticated-only page workflows` from `Scenarios Still Undecided` if covered successfully

**Step 3: Update the playbook with authenticated execution guidance**

Modify `docs/playbooks/browser-tooling-evaluation.md` so the live-session matrix or notes make the read-only authenticated-page evidence expectation more explicit.

**Step 4: Verify the updated docs**

Run:

```bash
rg -n "authenticated|AtomGit|chrome-devtools-mcp|chrome-cdp" reports/2026-03-17-browser-tooling-authenticated-evaluation.md docs/decisions/2026-03-17-browser-tooling-workflow.md docs/playbooks/browser-tooling-evaluation.md
git diff --check
```

Expected:

- all three files show authenticated references
- `git diff --check` returns no output

**Step 5: Commit**

```bash
git add reports/2026-03-17-browser-tooling-authenticated-evaluation.md docs/decisions/2026-03-17-browser-tooling-workflow.md docs/playbooks/browser-tooling-evaluation.md
git commit -m "docs: record authenticated browser tooling evaluation"
```
