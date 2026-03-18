# Chrome Agent Global Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a globally installable `chrome-agent` skill that dispatches webpage extraction tasks into the local `chrome-agent` repository and reports status plus artifact paths back to the parent session.

**Architecture:** Add a repo-owned global skill source under `skills/chrome-agent/`, document the installation and runtime contract around `CHROME_AGENT_REPO`, and provide a guarded installation workflow that checks for existing skill and environment variable state before making persistent changes. The runtime behavior remains a thin dispatcher that forwards tasks into the target repository through `codex-agent` first and `repo-agent` second.

**Tech Stack:** Markdown skill definitions, shell-based installation flow, existing `codex-agent` and `repo-agent` skills, repository documentation under `docs/plans/`

---

### Task 1: Create the global skill source

**Files:**
- Create: `skills/chrome-agent/SKILL.md`
- Modify: `README.md`
- Test: manual verification of the installed skill directory contents

**Step 1: Draft the skill contract**

Write the skill instructions so runtime behavior is explicit:

- validate `~/.agents/skills/codex-agent` or `~/.agents/skills/repo-agent`
- validate `CHROME_AGENT_REPO`
- dispatch to the repository and require stable output fields

**Step 2: Review the skill against existing repository workflow**

Run: `sed -n '1,260p' AGENTS.md`
Expected: confirms the repository still expects `codex-agent` as the primary browser-task entrypoint and routes extraction through current workflow rules

**Step 3: Write the skill file**

Create `skills/chrome-agent/SKILL.md` with:

- installation assumptions
- runtime checks
- dispatcher priority
- downstream prompt contract
- output contract

**Step 4: Verify the skill file exists and is readable**

Run: `sed -n '1,260p' skills/chrome-agent/SKILL.md`
Expected: the skill content renders without missing sections

**Step 5: Commit**

```bash
git add skills/chrome-agent/SKILL.md README.md
git commit -m "feat: add chrome-agent global dispatcher skill"
```

### Task 2: Add installation documentation and environment variable rules

**Files:**
- Modify: `README.md`
- Modify: `docs/setup/chrome-tooling.md`
- Test: manual review of installation instructions

**Step 1: Write the failing documentation checklist**

Checklist:

- no documented global install location
- no documented `CHROME_AGENT_REPO` contract
- no documented overwrite policy for existing global skill or env var

**Step 2: Update install docs**

Document:

- source directory: `skills/chrome-agent/`
- destination: `~/.agents/skills/chrome-agent/`
- env var: `CHROME_AGENT_REPO`
- preflight checks before copying or writing shell config

**Step 3: Add one-line install guidance**

Include a user-facing installation path that starts from a single prompt, while making clear that persistent changes still require confirmation when conflicts exist.

**Step 4: Review docs**

Run: `rg -n "CHROME_AGENT_REPO|~/.agents/skills/chrome-agent|overwrite|conflict" README.md docs/setup/chrome-tooling.md`
Expected: all key installation rules appear in docs

**Step 5: Commit**

```bash
git add README.md docs/setup/chrome-tooling.md
git commit -m "docs: add chrome-agent global skill installation guidance"
```

### Task 3: Define the installer workflow

**Files:**
- Create: `docs/playbooks/chrome-agent-global-install.md`
- Modify: `README.md`
- Test: playbook review against design requirements

**Step 1: Write the install workflow steps**

Include explicit decision points for:

- existing global skill path
- existing matching env var
- existing conflicting env var
- user confirmation before persistent writes

**Step 2: Write example commands**

Document the exact shell commands an operator would run to:

- inspect current skill path
- inspect current env var
- copy the skill directory
- append to shell config after confirmation

**Step 3: Review the playbook**

Run: `sed -n '1,260p' docs/playbooks/chrome-agent-global-install.md`
Expected: it gives a complete operator path without hidden assumptions

**Step 4: Commit**

```bash
git add docs/playbooks/chrome-agent-global-install.md README.md
git commit -m "docs: add chrome-agent global install playbook"
```

### Task 4: Verify dispatch contract with both downstream agents

**Files:**
- Modify: `skills/chrome-agent/SKILL.md`
- Create: `reports/2026-03-18-chrome-agent-global-skill-verification.md`
- Test: manual dry-run commands for `codex-agent` and `repo-agent`

**Step 1: Write dry-run prompts**

Prepare one prompt template for `codex-agent` and one for `repo-agent` that require:

- reading target `AGENTS.md`
- executing a webpage extraction task
- returning `result`, `target`, `summary`, `artifacts`, `next_action`

**Step 2: Run the dry-run checks**

Run the minimum safe dry-run invocation for both dispatchers against the current repository path and inspect whether the output shape is practical.

**Step 3: Refine the contract**

Tighten `skills/chrome-agent/SKILL.md` if either dispatcher returns output that is too loose to summarize reliably.

**Step 4: Save verification notes**

Record:

- command used
- which dispatcher path worked
- any output normalization gaps

**Step 5: Commit**

```bash
git add skills/chrome-agent/SKILL.md reports/2026-03-18-chrome-agent-global-skill-verification.md
git commit -m "test: verify chrome-agent global dispatcher contract"
```

### Task 5: Final review and handoff

**Files:**
- Modify: `docs/plans/2026-03-18-chrome-agent-global-skill-design.md`
- Modify: `docs/plans/2026-03-18-chrome-agent-global-skill.md`
- Test: repository diff review

**Step 1: Review the design against implementation artifacts**

Confirm the implemented skill and docs still match:

- skill name
- source and install locations
- `CHROME_AGENT_REPO`
- `codex-agent` primary / `repo-agent` fallback
- conflict-checking behavior

**Step 2: Review the final diff**

Run: `git diff --stat HEAD~5..HEAD`
Expected: only the intended skill, docs, playbook, and verification files changed

**Step 3: Run a final status check**

Run: `git status --short --branch`
Expected: clean working tree on the intended branch

**Step 4: Commit any final plan/doc alignment**

```bash
git add docs/plans/2026-03-18-chrome-agent-global-skill-design.md docs/plans/2026-03-18-chrome-agent-global-skill.md
git commit -m "docs: finalize chrome-agent global skill plan"
```
