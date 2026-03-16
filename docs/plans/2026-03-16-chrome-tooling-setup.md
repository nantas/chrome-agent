# Chrome Tooling Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal repo-local Node setup that pins `chrome-devtools-mcp` and `chrome-cdp-skill`, documents local usage, and records a first browser-task verification.

**Architecture:** Keep everything at repo root with `npm` and a committed lockfile. Use a normal npm package for `chrome-devtools-mcp`, a pinned GitHub dependency for `chrome-cdp-skill`, and only thin package scripts plus docs/report updates.

**Tech Stack:** Node.js 24, npm 11, `chrome-devtools-mcp`, `pi-chrome-cdp`

---

### Task 1: Create the minimal repo-local Node scaffolding

**Files:**
- Create: `package.json`

**Step 1: Write the package manifest**

Define the package name, mark it private, and add only the scripts needed to run the two local tools.

**Step 2: Install pinned dependencies**

Run: `npm install --save-dev chrome-devtools-mcp@0.20.0 github:pasky/chrome-cdp-skill#7c2940af8dbe12745f24845f352e7555baed0304`

Expected: `package-lock.json` is created and both tools are available in `node_modules/`.

### Task 2: Update project docs for future local runs

**Files:**
- Modify: `README.md`
- Modify: `docs/setup/chrome-tooling.md`

**Step 1: Document the local install path**

Add the minimal commands that future `codex-agent` runs should use from the repo root.

**Step 2: Document environment assumptions and blockers**

Record how `chrome-devtools-mcp` and `chrome-cdp-skill` differ, what local Chrome conditions are required, and any blocker discovered during verification.

### Task 3: Record the first verification report

**Files:**
- Create: `reports/2026-03-16-example-com-verification.md`

**Step 1: Run a safe public-page verification**

Use `example.com` to validate the local setup as far as the environment allows.

**Step 2: Capture evidence and next actions**

Write the result, exact commands used, and any residual blockers in the report.
