# Verification

## Scope

This verification covers the governance rewrite for the default webpage grabbing flow in `AGENTS.md` and the minimum writeback needed to remove stale conflicting wording elsewhere in the repository.

## Spec-to-Implementation Coverage

### Requirement: Default workflow ordering

- Verified in `AGENTS.md:22-64`.
- The document now presents one explicit operator flow: route the task, distinguish normal grabbing from approved live-session continuity, start with Scrapling, stop if satisfied, and escalate only on fallback triggers.
- Common Scrapling-first path selection is explicitly mapped:
  - `get` for static and article extraction
  - `fetch` for SPA and dynamic rendered flows
  - `stealthy-fetch` for protected or challenge-sensitive targets
  - bulk and session variants only when those scopes are actually needed

### Requirement: Fallback boundaries

- Verified in `AGENTS.md:50-55` and `AGENTS.md:147-155`.
- `chrome-devtools-mcp` is documented only as the diagnostic and evidence path.
- repo-local `chrome-cdp` is documented only as the live-session continuity path for already-open real Chrome tabs.
- The document now says fallback choice is driven by diagnostic needs versus live-tab continuity needs, not by tool overlap.

### Requirement: Authenticated read-only boundary

- Verified in `AGENTS.md:57-64`.
- Approved authenticated targets are now explicit preconditions.
- Authenticated runs remain read-only by default.
- Session-reuse failure now has a clear stop condition: if Scrapling loses the approved context through login redirect, reset, or write/logout risk, the Scrapling path stops and the approved live tab becomes the `chrome-cdp` fallback case.

### Requirement: Verification-aligned documentation

- Verified against:
  - `openspec/changes/integrate-scrapling-first-workflow/verification.md`
  - `sites/x.com-public-hashtag-search-login-gate.md`
- `AGENTS.md:64` now records the current `x.com` finding in the correct general form: Scrapling-first remains the opening move, but current-session continuity can require immediate `chrome-cdp` fallback after session reuse fails.
- Stale wording implying a non-Scrapling default path was removed from `AGENTS.md`.

## Conflict Scan

Scanned targets: `README.md`, `docs/decisions/`, `docs/playbooks/`.

Result:

- `README.md`: no direct contradiction found; wording already matches Scrapling-first as the default path.
- `docs/playbooks/browser-tooling-evaluation.md`: no direct contradiction found; playbook already treats Scrapling as the primary path and Chrome tooling as fallback.
- `docs/decisions/2026-03-17-browser-tooling-workflow.md`: direct contradiction found in `Switching triggers`, where public/repeatable work still started with `chrome-devtools-mcp`.

## Writeback Verification

- Updated `docs/decisions/2026-03-17-browser-tooling-workflow.md:34-41` to align the historical decision record with the current Scrapling-first default and the authenticated fallback stop rule.
- No README or playbook writeback was required for this change.

## Commands / Evidence

- `openspec status --change "reorganize-agents-default-web-grabbing-flow" --json`
- `openspec instructions apply --change "reorganize-agents-default-web-grabbing-flow" --json`
- `sed -n '1,260p' openspec/changes/reorganize-agents-default-web-grabbing-flow/{binding,proposal,design,tasks}.md`
- `sed -n '1,260p' openspec/changes/reorganize-agents-default-web-grabbing-flow/specs/scrapling-first-browser-workflow/spec.md`
- `sed -n '1,260p' openspec/changes/integrate-scrapling-first-workflow/verification.md`
- `sed -n '1,260p' sites/x.com-public-hashtag-search-login-gate.md`
- `rg -n "Scrapling|chrome-devtools-mcp|chrome-cdp|default path|default route|live-session|authenticated|session reuse" docs/decisions docs/playbooks README.md AGENTS.md`
- `git diff -- AGENTS.md docs/decisions/2026-03-17-browser-tooling-workflow.md`

## Result

- `AGENTS.md` main flow: aligned with spec
- fallback boundaries: aligned with spec
- authenticated read-only rule: aligned with spec
- minimal repository writeback: completed
