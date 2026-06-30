# 4-Dimensional Architecture Refactor — Implementation Plan

> **Status**: Living document (evolves as stages complete).
> Last updated: 2026-06-29.
>
> **Background**: [00-architecture-review.md](../architecture/00-architecture-review.md)
> diagnosed the root cause of recurring architecture-implementation drift:
> chrome-agent's 4-dimensional domain is only modelled in 1 dimension.
> This plan defines the 3-stage refactor to establish the 4-dimensional model
> as governing architectural infrastructure.

## Stage Overview

| # | Stage | Nature | Governance Track | Current Status |
|---|-------|--------|-----------------|----------------|
| 1 | Target Architecture Design | Architecture meta-design (no code changes) | Independent — produces `00-target-architecture.md` | `pending` |
| 2 | Capability Map Realignment | Documentation alignment (no code changes) | Independent — updates `01-08` + AGENTS.md + specs | `pending` |
| 3 | Residual Audit & Fix | Code/test/doc drift resolution | **openspec change** — `[TBD]` | `pending` |

**Governance**: Stages 1 and 2 are architecture design — they produce new or
revised source-of-truth documents. Stage 3 is a behavioural change (code+test
modifications) and follows the full openspec lifecycle: proposal → specs →
design → tasks → implement → verify → archive.

## Stage 1: Target Architecture Design

**Goal**: Produce a single authoritative document that declares the 4-dimensional
target architecture for chrome-agent. This is the "ruler" against which Stage 3
will measure all drift.

### Entry criteria

- [x] 4-dimensional domain model confirmed (ADR 0013)
- [x] Root cause diagnosed (00-architecture-review.md)
- [x] Three-question cure criteria accepted
- [ ] Cross-cutting design decisions resolved via grill:
  - Mirror equivalence contract form
  - Variant mechanism policy (config-driven vs file-fork)
  - Format split policy (when is D-axis split legitimate vs accidental)
  - Naming schema convention
- [ ] Per-capability target profiles designed:
  - convert (6 impls → target: 1 shared kernel + declared mirrors)
  - fetch (engine stack + pipeline phases → target: mirror declaration)
  - discover (explore + pipeline → target: mirror declaration)
  - extract (good, mostly → target: formalize shared kernel contract)
  - assemble / link_fix (single impl → target: archive as-is)

### Primary deliverable

`docs/architecture/00-target-architecture.md` containing:
- §1 4-dim model (reference ADR 0013)
- §2 Declaration schema (what each capability MUST declare)
- §3 Capability registry (per-capability profiles: mirrors, variants, format, kernel, equivalence)

### Exit criteria

- [ ] `00-target-architecture.md` exists and is reviewed
- [ ] All cross-cutting design decisions resolved and documented
- [ ] All capability profiles filled with target declarations
- [ ] No code changes (verify: `git diff --stat` is empty outside docs/)

### Grill prompts (to be used in Stage 1 grill sessions)

1. "Design the declaration schema — what fields does each capability registry entry need?"
2. "Resolve the mirror equivalence contract form — golden snapshot? assertion test? both?"
3. "Resolve the variant mechanism policy — when config-driven, when file-fork?"
4. "Design the target profiles for convert, then fetch, then discover, then extract"

---

## Stage 2: Capability Map Realignment

**Goal**: Propagate the target architecture into all derived documentation,
so every architectural layer consistently expresses the 4-dimensional model.

### Entry criteria

- [ ] Stage 1 complete (exit criteria met)

### Work items

| Target doc | Current state | Required changes |
|------------|--------------|-----------------|
| `AGENTS.md` §2 Capability Framework | 1-dim (capability names only) | Add dimensional coordinate schema per capability; update Reference Index |
| `AGENTS.md` §10 SSOT Map | Maps knowledge → file, no dimensions | Add capability registry pointer |
| `docs/architecture/01-overview.md` | Missing converter.p整体 y; wrong html_to_markdown location | Rewrite with dimensional declarations; place `00-target-architecture` as root reference |
| `docs/architecture/02-pipeline-flow.md` | Pipeline only, no mirror context | Add B-axis context; declare pipeline mirrors of explore capabilities |
| `docs/architecture/05-converter-architecture.md` | Specific to wikitext path | Expand to 4-dim convert model: mirrors, variants, shared kernel |
| `docs/architecture/07-explore-workflow.md` | Explore only | Add B-axis context; declare explore mirrors of pipeline capabilities |
| `CONTEXT.md` | Updated in c9b474f (terms added) | Verify alignment with Stage 1 declaration schema — no structural changes expected |
| `openspec/specs/capability-contracts/` | A-axis behaviour only | Determine whether to add B/C/D expression or defer to Stage 3 openspec change |
| `openspec/specs/capabilities-derivation/` | Same | Same as above |

### Exit criteria

- [ ] All 01-08 docs reference the 4-dim model from `00-target-architecture`
- [ ] `AGENTS.md` capability framework updated with dimensional coordinates
- [ ] No code changes outside docs/
- [ ] `git diff --stat` changes are documentation-only

---

## Stage 3: Residual Audit & Fix

**Goal**: Compare the target architecture against current code, tests, and
docs. List every drift. Fix them. This is the only stage that modifies code.

### Entry criteria

- [ ] Stage 1 complete
- [ ] Stage 2 complete

### Method

1. For each capability entry in `00-target-architecture.md` §3, audit the
   codebase and produce a **drift register** (list of violations).
2. Prioritise: security/safety > mirror non-equivalence > dead code > naming.
3. Fix each drift with TDD: test red → implementation green → refactor.
4. At completion, verify against the three-question cure criteria.

### Openspec change

This stage is a formal openspec change (name TBD during Stage 3 launch).
It follows the full lifecycle:

```
proposal → specs → design → tasks → implement → verify → writeback → archive
```

Key deliverables within the change:
- `proposal.md`: problem statement (reference 00-architecture-review.md)
- `specs/`: delta specs for capabilities being modified
- `design.md`: per-capability fix design
- `tasks.md`: vertical slices, TDD sequence
- `verification.md`: spec-to-implementation mapping with all three questions answerable per module
- `writeback.md`: affected architecture docs + openspec specs to backfill

### Exit criteria

- [ ] Drift register complete and reviewed
- [ ] All prioritised drifts fixed
- [ ] Full test suite green
- [ ] Three-question criteria verifiable for every capability
- [ ] openspec change archived
- [ ] `verification.md` confirms spec→code→test triangle closed for every affected requirement

---

## Governance Notes

- **Updating this plan**: This file is the master tracker. After each session,
  update the relevant stage's status and checkboxes. After Stage 1 and 2
  complete, archive their grill outputs as design references but do NOT
  rewrite this file's stage descriptions — they are the plan, frozen once
  the stage enters execution.
- **Design decisions**: Stage 1 and 2 produce design decisions. Those that
  meet ADR criteria (hard-to-reverse, surprising, real trade-off) should be
  recorded as additional ADRs. Minor decisions are captured in the stage's
  design artifacts.
- **Relationship to 00-architecture-review.md**: The review document is the
  *diagnosis*. This plan is the *treatment*. They are sibling files — the plan
  references the review; the review does not reference the plan (it's frozen).
