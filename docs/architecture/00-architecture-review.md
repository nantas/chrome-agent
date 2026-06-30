# 00 — Architecture Review: Multi-Dimensional Drift Root-Cause Analysis

> **Status**: Frozen (session diagnostic artifact). This document captures the 2026-06-29
> grill-with-docs architecture review findings. It does not evolve — corrections
> go through new ADRs.
>
> **Companion**: [ADR 0013 — 4-dimensional domain model](../adr/0013-four-dimensional-domain-model.md)
> (the decision. This file is the full argument with evidence.)

## 1. Executive Summary

chrome-agent has recurring architecture-implementation drift (preprocess_html
no-ops, multi-converter fork, fanbox duplication, gate bypasses). After
5 rounds of manual fixes across 2026-03 to 2026-06, the pattern persists.

Root cause: the business domain has **4 orthogonal dimensions** (Capability,
Execution Path, Strategy Variant, Input Format), but all architectural
expression layers — directory layout, naming schema, spec model, documentation,
governance — only model **1** (Capability). The other 3 dimensions are never
declared, never visible, never checked. This produces 6 structural defects that
systematically generate drift. Each manual fix addresses a symptom; none
disarms the generation mechanism.

The cure requires establishing the 4-dimensional model as first-class
architectural governance, expressed in a target-architecture document that
makes every module's dimensional coordinates, mirror relationships, and
equivalence contracts **structurally answerable without reading all the code**.

## 2. The Four-Dimensional Domain Model

chrome-agent's scraping/conversion/extraction domain has four orthogonal,
independent axes. Every module simultaneously occupies a point in this 4-axis
space.

| Axis | Name | Values in this project | What it governs |
|------|------|------------------------|-----------------|
| **A** | Capability | fetch, convert, extract, discover, assemble | What work the module does |
| **B** | Execution Path | explore (sampling audit), pipeline (batch production), site-samples (quality regression) | Which pipeline context invokes it |
| **C** | Strategy Variant | generic, fandom, wiki.gg, … (per-domain) | What site-specific adaptation it carries |
| **D** | Input Format | rendered HTML, wikitext, API JSON | What data shape it consumes |

**Why this matters**: any two modules that share A-axis (e.g. both do
"convert") but differ on B or C are **mirrors** or **variants** — they must be
explicitly declared as such and must have declared equivalence contracts.
Without this declaration, they appear as unrelated files that drift silently.
Every symptom observed in this session traces back to this unmodeled
multi-dimensionality.

## 3. Six Structural Defects

Each defect is a specific failure mode caused by the unmodeled dimensions.
Evidence for each defect is drawn from code inspection conducted during the
2026-06-29 session.

### Defect 1: Multiple dimensions collapsed into single files

`lib/extraction/converter.py` IS the shared converter — but it simultaneously
exposes two entry points for two different B-axis contexts: `HtmlToMarkdownConverter`
(class, used by pipeline) and `convert_html_to_markdown` (function, dynamically
grabbed by explore via `sample_converter.py`). The file name only expresses the
A-axis ("converter"). The B-axis split is invisible unless you read the
implementation. Worse: the split is implemented as a `context` parameter on
`preprocess_html()`, creating a runtime fork where one branch was a no-op stub
until fix ca192d8.

**Evidence**: `preprocess_html(context="pipeline")` returned html unchanged
prior to C4 fix. Gate passed because `"cleanup"` appeared textually in the
source — it just wasn't executed.

### Defect 2: Mirrors (same capability, different execution paths) have no equivalence declaration

The explore convert mirror and pipeline convert mirror MUST be behaviorally
equivalent (both apply cleanup ops, both preserve content). But this
equivalence exists only as an implicit expectation. No structural declaration
says "explore convert ↔ pipeline convert are mirrors; their equivalence is
proven by test X." Without this, drift between mirrors is undetectable until
manual inspection — which is exactly what the C4 bug was.

**Evidence**: The 2026-06-29 session's C4 fix added `preprocess_html` to the
previously-no-op pipeline path. The explore path had been applying cleanup ops
all along. These mirrors diverged for an unknown period.

### Defect 3: Two conflicting variant mechanisms with no shared abstraction

Strategy variants (C-axis) are expressed through two unrelated mechanisms:

- **Configuration-driven** (wiki.gg, etc.): `strategy.md` frontmatter declares
  `cleanup` ops arrays, processed by `preprocessor.py`.
- **File-fork** (fandom): `pipeline/converters/fandom_html_to_markdown.py` is a
  completely independent implementation — shares zero code with the generic
  converter, uses its own bs4+markdownify stack.

A developer or agent faced with "add a new site strategy convert variant" has
no structural guidance on which mechanism to use. The two mechanisms coexist
with no declared relationship.

**Evidence**: `fandom_html_to_markdown.py` imports neither `converter.py` nor
`html_to_markdown.py`.

### Defect 4: Naming schema exposes inconsistent dimensional coordinates

Four conversion-related files, four naming conventions, each exposing a
different subset of dimensions:

| File | Exposed dimensions |
|------|--------------------|
| `converter.py` | A only (Capability) |
| `html_to_markdown.py` | A only (Capability, verb-phrased) |
| `fandom_html_to_markdown.py` | C + A (the only one exposing Variant) |
| `sample_converter.py` | B + A (the only one exposing Execution Path) |

There is no naming schema. The file name cannot be used to infer a module's
dimensional coordinates.

### Defect 5: "Shared" layer semantics are undefined and violated

`lib/extraction/` is designated as the shared layer. But its contents have
different actual sharing profiles:

| Module | Actual sharing | Matches "shared" label? |
|--------|----------------|------------------------|
| `preprocessor.py` | Pipeline + explore, direct import | ✅ True shared |
| `converter.py` | Pipeline (class) + explore (indirect, function) | △ Nominal but asymmetric |
| `html_to_markdown.py` | Pipeline only + test_runner | ❌ Not shared |
| `infobox.py` | Both | ✅ True shared |

The label "shared" is an aspiration, not a fact. Modules that aren't shared
live in the shared layer; the only real shared module is also the one that
splits its interface by context.

### Defect 6: Architecture documentation never described the core module's dimensional position

`docs/architecture/01-overview.md` — the system overview — lists
`lib/extraction/` as "extraction tools (infobox, preprocessor)." It **never
mentions `converter.py`**, a 954-line production-critical module. And it
incorrectly places `html_to_markdown.py` under `pipeline/converters/` (it is
actually in `lib/extraction/`).

The documentation does not describe module *belonging* — only module *location*.
It provides a file listing, not dimensional coordinates.

## 4. Causal Chain: Symptoms ← Defects ← Root Cause

All five symptoms observed in the 2026-06-29 session trace back through the
six defects to the single root cause.

| Session symptom | Immediate defect | Defect # |
|-----------------|-----------------|----------|
| `preprocess_html(context="pipeline")` was a no-op stub | Mirror split hidden inside a single file via `context` parameter; one branch untested | Defect 1 (dimension collapse) |
| `fanbox-download-videos.mjs` existed in two copies, one with hardcoded secret | No structural declaration of authoritative source; SSOT declared in prose, not enforced | Defect 3 (dual mechanism) + Defect 4 (naming) |
| `test_runner site-samples` tested `html_to_markdown.py` instead of pipeline's `converter.py` | Two modules in "shared" layer, tester picked the wrong one because "shared" is undefined | Defect 5 (shared semantics) + Defect 1 |
| Architecture gate scanned only `converter.py`, missed `preprocessor.py` where cleanup actually lives | No mirror/equivalence declaration — gate didn't know cleanup spans two files | Defect 2 (no mirror declaration) + Defect 6 (docs gap) |
| Gate had hardcoded `if key == "cleanup": return True` bypass | Drift detector itself drifted — because no one owns "verifying the verifier" | Defect 6 (ownership gap) |

All five converge to the same root: **the architecture has no layer that models
the 4-dimensional space, so module identity, mirror relationships, and
equivalence are always implicit — and implicit invariants drift.**

## 5. Duty Gap: Which Layer Should Own What

For each architectural expression layer, the table below shows what it
currently owns vs. what it would need to own for the 4-dimensional model to
be structurally visible.

| Layer | Current ownership | Missing responsibility |
|-------|-------------------|------------------------|
| Directory layout | Subsystem grouping (pipeline/explore/lib) | Dimensional coordinate declaration |
| Naming schema | Inconsistent, mostly A-axis | Uniform schema exposing B/C/D where relevant |
| openspec specs (114 total) | Capability behavior (A-axis SHALL/MUST) | No expression for B/C/D or mirror equivalence |
| Architecture docs (01-08) | File listing + teaching flow | No dimensional coordinates per module |
| Governance (C1-C10, GOVERNANCE.md) | Code-looks-like constraints | No constraint on dimensional declaration or mirror equivalence |
| `architecture_gate.py` | Text-pattern match in source files | No execution-based verification; cold path only (manual explore) |

**Key finding**: "Dimensional coordinate declaration" as a responsibility has
**never been assigned to any layer.** It does not appear in any governance
document, any hard constraint, any spec, or any docs directive. The absence is
total — not a failure of execution, but a gap in the architecture's conceptual
model from its inception.

## 6. Cure Criteria: The Three Questions

A "cured" architecture is one where a new agent, encountering any module for
the first time, can structurally answer three questions (without reading all
the source code or asking a human):

1. **Is this module a single shared kernel, or a mirror/variant of something else?**
   (Declared dimensional coordinates)

2. **If it is a mirror — which other modules are its mirror partners, and what
   equivalence contract binds them?**
   (Declared mirror relationship)

3. **Where is the proof that the equivalence holds?**
   (Runnable test / golden snapshot pointer)

These three questions define the acceptance criteria for the entire
architectural refactor.

## 7. References

- [ADR 0013](../adr/0013-four-dimensional-domain-model.md) — Decision to adopt 4-dim model
- [CONTEXT.md](../../CONTEXT.md) — Domain glossary (updated with dimensional terms)
- [GOVERNANCE.md](../GOVERNANCE.md) — Governance workflow design
- [01-overview.md](01-overview.md) — Current system overview (to be aligned)
- Session: 2026-06-29 grill-with-docs (full transcript in session log)
- Commits: ca192d8 (C4 fix), 9b5f56b (fanbox dedup), c1af15d (L2 test), c9b474f (ADR 0013)
