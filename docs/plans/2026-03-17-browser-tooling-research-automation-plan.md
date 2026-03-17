# Browser Tooling Research Automation Plan

## Automatable Checks

- Public-site checks with no login dependency (title/URL read, key content extraction, screenshot capture).
- Deterministic DOM or accessibility-tree inspection for known selectors or structures.
- Repeatable interaction smoke flows on public pages where expected outcomes are explicit.
- Baseline timing or step-count capture for tool setup and simple repeat runs.

## Semi-Automatable Checks

- Checks where scripts can collect evidence but human review is needed to judge content quality or relevance.
- Stability comparisons that need interpretation (for example, whether minor UI differences are acceptable).
- Multi-step diagnostic captures where automated collection is reliable but root-cause conclusions require manual analysis.
- Light cross-tab checks where success can be logged automatically but operator judgment confirms practical usability.

### Promote to Manual Execution When Any Trigger Is True

- Two consecutive scripted attempts disagree on pass/fail for the same check.
- Required evidence is missing or ambiguous after one re-run.
- A go/no-go decision depends on policy, trust, or workflow judgment that cannot be asserted from captured artifacts alone.

## Manual-Only Checks

- Live-session checks that must continue on an already-open tab tied to a real user workflow.
- Logged-in or sensitive pages where session trust, account context, or policy boundaries require human control.
- UI-state preservation validation involving unsaved input, in-progress edits, or nuanced panel/scroll context.
- Edge-case follow-ups where a human must decide whether to proceed, stop, or change tooling path.
