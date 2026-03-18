# Browser Workflow Routing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update `AGENTS.md` so the repository routes browser tasks into a fast content-retrieval workflow by default and a full evidence-heavy analysis workflow when the prompt asks for deeper page/platform investigation.

**Architecture:** Keep the existing tool-selection policy, but split workflow execution by user intent. Add explicit route definitions, prompt-level routing rules, different reporting expectations, and different verification baselines for the two workflows.

**Tech Stack:** Markdown, `AGENTS.md`, repository workflow docs

---

### Task 1: Add The Dual Workflow Model

**Files:**
- Modify: `AGENTS.md`

**Step 1: Add workflow-type definitions**

Document:

- `Content Retrieval` as the default fast path
- `Platform/Page Analysis` as the deep evidence path

**Step 2: Add prompt-intent routing rules**

Document:

- when a bare URL or content request should route to `Content Retrieval`
- when analysis/debug/evidence/structure prompts should route to `Platform/Page Analysis`
- when mixed signals should prefer the deep path

**Step 3: Verify the new routing section exists**

Run: `rg -n "Workflow A|Workflow B|Intent Routing|Content Retrieval|Platform/Page Analysis" AGENTS.md`
Expected: matches covering the new route definitions and routing section

### Task 2: Split Reporting And Verification Requirements

**Files:**
- Modify: `AGENTS.md`

**Step 1: Rewrite reporting expectations by workflow**

Document:

- Workflow A returns content or failure directly by default
- Workflow A creates `reports/` entries only when useful or requested
- Workflow B defaults to full reports and evidence capture

**Step 2: Rewrite verification baselines by workflow**

Document:

- Workflow A uses lightweight verification
- Workflow B keeps the heavier baseline with screenshots and structure clues
- article extraction still preserves DOM order and inline image URLs

**Step 3: Verify final wording**

Run: `sed -n '1,260p' AGENTS.md`
Expected: `AGENTS.md` reads as a clear two-route workflow without losing the existing tool-selection guidance
