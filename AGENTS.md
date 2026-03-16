# AGENTS.md

This repository is a browser-agent workspace for website access, debugging, evidence collection, and execution reporting.

## Goals

1. Use `codex-agent` as the primary entrypoint for browser-driven tasks
2. Keep workflows driven by `AGENTS.md + skills`, not by ad hoc scripts
3. Accumulate reusable reports and site-specific experience over time

## Scope

- In scope:
  - Website access and information gathering through a browser agent workflow
  - Frontend debugging, page inspection, and evidence capture
  - Reporting what was attempted, what succeeded, what failed, and what to try next
- Out of scope for v1:
  - Credential management
  - A large automation framework
  - Hard-coding detailed skill or config structures before real usage validates them

## Workflow

1. Understand the task, target site, and expected output first
2. Decide whether the task is primarily access/collection or debugging/inspection
3. Prefer `chrome-devtools-mcp` as the default browser tooling path
4. Consider `chrome-cdp-skill` when the task depends on reusing the current live Chrome session
5. Record the execution result in `reports/`
6. If the task reveals reusable site knowledge, update `sites/` or `docs/playbooks/`

## Tooling Strategy

- Default path: `chrome-devtools-mcp`
- Supplemental path: `chrome-cdp-skill`
- Do not assume both are required for every task
- Let real tasks drive how skills, configs, and playbooks evolve

## Reporting Requirements

Each completed browser task should capture at least:

- Task goal
- Target site or page
- Tooling path used
- Result: success, partial success, or failure
- Key evidence
- Next recommended action

## Repository Expectations

- Keep top-level structure stable
- Avoid premature abstraction in `skills/` and `configs/`
- Prefer writing down decisions after real runs instead of guessing them up front
