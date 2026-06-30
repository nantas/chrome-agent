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
| 1 | Target Architecture Design | Architecture meta-design (no code changes) | Independent — produces `00-target-architecture.md` | `done` |
| 2 | Capability Map Realignment | Documentation alignment (no code changes) | Independent — updates `01-08` + AGENTS.md + specs | `done` |
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
- [x] Cross-cutting design decisions resolved via grill:
  - [x] Mirror equivalence contract form (golden snapshot, §4.3)
  - [x] Variant mechanism policy (config-driven only, §4.2)
  - [x] Format split policy (D-axis boundary = input syntax, §4.5)
  - [x] Naming schema convention (§4.1)
- [x] Per-capability target profiles designed:
  - [x] convert (1 shared kernel with optional wiki_domain + format_converter for wikitext)
  - [x] fetch (engine router as infrastructure, probe_chain as explore fetch kernel)
  - [x] discover (consolidated into explore site_analysis; pipeline no longer discovers)
  - [x] extract (removed preprocessor context param; moved sample_converter orchestration into kernel)
  - [x] assemble (run_assemble as sole kernel, mergeMarkdownFiles as infrastructure tool)

### Primary deliverable

`docs/architecture/00-target-architecture.md` containing:
- §1 4-dim model (reference ADR 0013)
- §2 Declaration schema (what each capability MUST declare)
- §3 Capability registry (per-capability profiles: mirrors, variants, format, kernel, equivalence)

### Exit criteria

- [x] `00-target-architecture.md` exists，5 章节含全部能力流程图、决策表、声明 Schema
- [x] All cross-cutting design decisions resolved and documented (§4)
- [x] All capability profiles filled with target declarations (§3)
- [x] No code changes — only `docs/architecture/00-target-architecture.md` created

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

- [x] Stage 1 complete (exit criteria met)

### Work items

| Target doc | Current state | Required changes |
|------------|--------------|-----------------|
| `AGENTS.md` §2 Capability Framework | 1-dim (capability names only) | ✅ Replaced with 4-dim capability table |
| `AGENTS.md` §10 SSOT Map | Maps knowledge → file, no dimensions | ✅ Added `00-target-architecture` as architecture SSOT |
| `docs/architecture/01-overview.md` | Missing converter.py; wrong html_to_markdown location | ✅ Fixed extraction listing, removed dead converter refs, added 00 link |
| `docs/architecture/02-pipeline-flow.md` | Pipeline only, no mirror context | ✅ Added B-axis context in 关联文档 |
| `docs/architecture/05-converter-architecture.md` | Specific to wikitext path | ✅ 4-dim model framing + fandom dead-code annotation + 关联文档 updated |
| `docs/architecture/07-explore-workflow.md` | Explore only | ✅ Added B-axis context in 关联文档 |
| `CONTEXT.md` | Updated in c9b474f (terms added) | ✅ Verified — 8 references to 4-dim/mirror/kernel terms already present |
| `openspec/specs/` | A-axis behaviour only | ⏭ Deferred to Stage 3 — B/C/D dimension expression belongs in 00-target-architecture, Stage 3 openspec change will align specs with code changes |

### Exit criteria

- [x] All 01-08 docs reference the 4-dim model from `00-target-architecture`
- [x] `AGENTS.md` capability framework updated with dimensional coordinates
- [x] No code changes outside docs/ (7 files, all docs)
- [x] `git diff --stat` changes are documentation-only

---

## Stage 3: Residual Audit & Fix

**Goal**: Compare the target architecture against current code, tests, and
docs. List every drift. Fix them. This is the only stage that modifies code.

### Entry criteria

- [x] Stage 1 complete
- [x] Stage 2 complete

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
