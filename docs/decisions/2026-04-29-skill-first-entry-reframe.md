# Skill-First Entry Reframe

## Context

Phase 5 introduced a repo-backed global `chrome-agent` CLI and explicitly downgraded `skills/chrome-agent` to a historical compatibility artifact. In practice that removed the agent-facing intent layer instead of removing complexity: upstream callers still had to decide between `fetch`, `explore`, and `crawl`, which contradicted the repository's `workflow-driven` governance model.

The real execution authority already lived inside this repository through `AGENTS.md`, stable specs, strategy files, and engine rules. Removing the workflow skill did not simplify that authority boundary; it only pushed workflow choice back out to callers and revived demand for extra wrappers around the CLI.

## Decision

Supersede the Phase 5 assumption that the global skill should be retired as a formal primary entry.

Adopt a two-layer public contract instead:

- the global `chrome-agent` workflow skill is the recommended agent-first entry
- the repo-backed global `chrome-agent` CLI remains the low-level explicit execution surface and shell/backend entry
- the skill performs only `doctor` preflight, intent routing, and CLI-result packaging
- the CLI remains the execution backend and JSON source of truth

This preserves the thin launcher model while restoring a stable intent-facing entry that does not depend on prompt-forwarding runtimes.

## Consequences

- `skills/chrome-agent/SKILL.md` becomes an actively governed repository artifact again
- `README.md`, `AGENTS.md`, and install guidance must describe skill-first / CLI-backed layering consistently
- `explore` must represent the Platform/Page Analysis backend rather than a narrow strategy-gap probe
- old documentation that framed the CLI as the only formal external entry is now historical and must be treated as superseded
