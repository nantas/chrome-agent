# Design

## Context

The normative behavior for this change is `specs/scrapling-first-browser-workflow/spec.md`.

The repository already completed the `Scrapling-first` tooling transition and verified it on public, dynamic, article, protected, and approved authenticated cases. The remaining issue is operator clarity: `AGENTS.md` still spreads the default webpage grabbing workflow across several sections, which forces readers to reconstruct the real execution order from repeated rules.

This change does not alter runtime behavior. It reorganizes the documented operator contract so that the verified default route, fallback triggers, and authenticated boundaries are explicit and internally consistent.

## Goals / Non-Goals

**Goals:**

- Reorganize `AGENTS.md` so the default webpage grabbing flow reads as one clear operator path.
- Keep `Content Retrieval` and `Platform/Page Analysis`, but make tool choice subordinate to that routing instead of scattered across multiple sections.
- Distinguish diagnostic fallback (`chrome-devtools-mcp`) from live-tab continuity fallback (`chrome-cdp`) with explicit triggers.
- Reflect the verified authenticated behavior already recorded in repo artifacts, including the current `x.com` login-state finding.
- Remove duplicated or stale wording that could imply a non-Scrapling default path.

**Non-Goals:**

- Do not change Scrapling installation, MCP configuration, or other runtime setup.
- Do not introduce new capabilities, tools, or site-specific extraction logic.
- Do not rewrite historical reports or repeat the full environment contract from the previous change.
- Do not broaden authenticated scope beyond the existing read-only, user-approved boundary.

## Decisions

- **Structure decision:** Reframe the current workflow guidance around a new explicit `Default Web Grabbing Flow` section, then keep supporting sections for route-specific behavior and verification expectations.
- **Ordering decision:** The documented operator order is fixed as: classify route, decide whether live-session continuity is required, start with Scrapling, stop if sufficient, escalate only on defined fallback triggers.
- **Fallback decision:** Keep `chrome-devtools-mcp` and `chrome-cdp` in separate boundary language. `chrome-devtools-mcp` is for diagnostics and evidence; `chrome-cdp` is for immediate continuation on an already-open real Chrome tab.
- **Authenticated decision:** Document that approved authenticated runs may try Scrapling session reuse first, but if session continuity is lost through login redirect or reset, the Scrapling path stops and the approved live tab becomes a `chrome-cdp` fallback case.
- **Scope decision:** Limit required writeback to `AGENTS.md`, unless implementation discovers a directly conflicting statement in `README.md` or another stable governance doc that would otherwise leave the repo inconsistent.

## Risks / Migration

- Reorganizing the document without removing duplicated statements could leave mixed guidance behind. Implementation should collapse or delete redundant wording instead of only appending a new section.
- Overfitting the authenticated wording to one site could make the contract too narrow. The `x.com` result should be documented as a verified example that sharpens the general rule, not as a site-specific exception encoded into the main workflow.
- If `AGENTS.md` is updated but surrounding governance docs still state a different default path, operators may continue reading inconsistent instructions. Implementation should check for direct contradictions and either align them or record why no update is needed.
