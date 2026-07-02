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
| 3 | Residual Audit & Fix | Code/test/doc drift resolution | 3 openspec changes: unify-html-converter, unify-extract-fetch-kernels, migrate-discovery-to-explore | `done` |

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
docs. List every drift. Fix them in 3 parallel openspec changes.

### Entry criteria

- [x] Stage 1 complete
- [x] Stage 2 complete

### Drift Register (from `00-target-architecture.md` §3)

| # | Capability | Drift | Type | Change |
|---|-----------|-------|------|--------|
| 1 | Convert | `fandom_html_to_markdown.py` 零调用者，功能已被 `converter.py` + `preprocessor` 覆盖 | 删除 | unify-html-converter |
| 2 | Convert | `html_to_markdown.py` 是共享内核 `converter.py` 的重复实现（python regex vs selectolax），功能并入 converter.py generic 路径 | 删除+合并 | unify-html-converter |
| 3 | Convert | 无镜像等价测试（explore convert vs pipeline convert 输出从未对比） | 缺测试 | unify-html-converter |
| 4 | Fetch | `.mjs` mediawiki-api fetch（spawn `standalone.py`）与 pipeline `fetch.py` 两条代码路径做同一件事 | 合并 | unify-extract-fetch-kernels |
| 5 | Extract | `preprocessor.py` 有 `context` 参数分 explore/pipeline 分支 | 删除 | unify-extract-fetch-kernels |
| 6 | Extract | `sample_converter._apply_extraction()` 编排逻辑不在共享内核 | 移动 | unify-extract-fetch-kernels |
| 7 | Discover | `discovery_homepage.py` + `discovery_allpages.py` 在 pipeline 而非 explore | 移动 | migrate-discovery-to-explore |
| 8 | Discover | `pipeline/strategies/discovery.py` 应在 explore 复用 | 移动 | migrate-discovery-to-explore |
| 9 | Discover | pipeline 不应有 discover 阶段——页面清单来自 strategy manifest | 删除 | migrate-discovery-to-explore |
| — | Assemble | 无 drift | — | — |

### Openspec Changes

3 个并行 change，执行顺序 Convert → Extract+Fetch → Discover。测试标准：回归通过。

#### Change 1: `unify-html-converter`

**范围**：消除 3 份 HTML→Markdown 实现，保留唯一的 selectolax 内核。

| Deliverable | 内容 |
|-------------|------|
| `proposal.md` | 问题陈述：3 个转换器并存（converter / html_to_markdown / fandom_html_to_markdown），B 轴和 C 轴不应通过代码分叉表达 |
| `specs/` | delta spec：Convert 能力的 4 维坐标、kernel 唯一性、镜像等价契约 |
| `design.md` | 删除策略：先验证测试覆盖 → 删 fandom → 删 html_to_markdown → 补 golden snapshot |
| `tasks.md` | ① 跑 site-samples 确认现有覆盖 ② 删 fandom_html_to_markdown.py ③ 确认 generic HTML 路径 converter.py wiki_domain=None 覆盖 ④ 删 html_to_markdown.py ⑤ 添 golden snapshot 测试（cache 已有页面走 explore + pipeline 两条路径） ⑥ 全域回归 |
| `verification.md` | golden snapshot 差异 = 0；三项自问可答 |

#### Change 2: `unify-extract-fetch-kernels`

**范围**：消除 preprocessor 的 context 分支 + 编排逻辑移入共享内核 + fetch 路径统一。

| Deliverable | 内容 |
|-------------|------|
| `proposal.md` | 问题陈述：preprocessor 有 B 轴分支、_apply_extraction 不在 kernel、mjs 和 pipeline 有重复 MediaWiki fetch |
| `specs/` | delta spec：preprocessor 统一路径、converter.convert_page_full 声明、fetch 唯一 kernel |
| `design.md` | 步骤：删 context 参数 → 移 _apply_extraction 到 converter → fetch 路径收束 |
| `tasks.md` | ① 全量 grep context= 调用点 ② 删 preprocessor context 参数 ③ converter.py 加 convert_page_full() ④ sample_converter 改为调用 convert_page_full ⑤ mjs mediawiki-api 路径改为调 fetch.py ⑥ 回归 |
| `verification.md` | preprocessor 无 context 参数；sample_converter 不自行编排；mjs 不调 standalone.py 做 fetch |

#### Change 3: `migrate-discovery-to-explore`

**范围**：pipeline 的 discover 阶段移入 explore，pipeline 不再自行发现页面。

| Deliverable | 内容 |
|-------------|------|
| `proposal.md` | 问题陈述：discover 职责分裂在 pipeline 和 explore 两处，违反「explore 发现→freeze→pipeline 消费」单向数据流 |
| `specs/` | delta spec：pipeline manifest 来源 = strategy frontmatter，discover 仅在 explore |
| `design.md` | 移动策略：discovery_*.py → explore；pipeline orchestrator 去 discover 阶段；discovery.py 策略接口探索复用 |
| `tasks.md` | ① 确认 pipeline orchestrator 中 discover 调用点 ② 移 discovery_homepage + discovery_allpages → explore ③ 移 discovery 策略接口 ④ pipeline 去 discover phase ⑤ 确认 explore freeze 输出的 manifest 可被 pipeline 直接消费 ⑥ 全链路回归（explore → freeze → pipeline） |
| `verification.md` | pipeline 无 discover 阶段；explore manifest → pipeline 可直达 |

### Exit criteria

- [x] Drift register complete and reviewed
- [x] All 9 drifts fixed
- [x] Full test suite green (80 unit + 13 site-samples × 3 changes)
- [x] Three-question criteria verifiable for every capability
- [x] 3 openspec changes archived
- [x] `verification.md` per change confirms spec→code→test triangle closed
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
