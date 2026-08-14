# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选定 Modified `fetch`（A+B 候选）+ REMOVED on `pipeline-infobox.md`（C 候选）。A+B 在 fetch 能力下声明 2 个新 requirement（failure-envelope-single-implementation + pool-lifecycle-single-orchestration），让契约可执行。本文件是 fetch 能力的 delta（ADDED 2 requirement）；pipeline-infobox.md 的 REMOVED 是 C 候选的独立 delta（见 `specs/pipeline-infobox/spec.md`）。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: failure-envelope-single-implementation

All internal-failure result construction across cli.mjs command handlers (crawl, scrape, batch, explore, sitemap discovery/extraction, etc.) SHALL route through a single `internalFailure` builder rather than inlining the `generateHandoff(...) + makeResult("failure", {workflow, engine_path, handoff_path, handoff_summary})` envelope per call site. The builder SHALL accept a uniform parameter object (`{command, target, repoRef, runDir, reason, summary, stderr, enginePath, artifacts, strategy, ...}`) covering the union of fields the inlined blocks currently pass; per-call-site variations (e.g. specific `reason` strings, `engine_path` values, extra artifacts) SHALL be expressible as arguments, not as bespoke envelope re-derivations. The pre-existing `crawlInternalError` SHALL become a thin crawl-prefixed caller of `internalFailure`, not a parallel implementation.

Rationale: a change to the failure-result shape (e.g. a new metadata field, a handoff doc format change) SHALL be a 1-edit, not a 10-edit. This is the "deep module that should exist, now fully born" — the team already saw the concern (they extracted `crawlInternalError`) but only covered 1 of 10 call sites (its own body).

#### Scenario: all-internal-failure-sites-delegate-to-builder
- **WHEN** any cli.mjs command handler needs to emit an internal-failure result (generateHandoff + makeResult failure)
- **THEN** it SHALL call `internalFailure({...})` (or a command-specific thin wrapper that delegates to it)
- **AND** SHALL NOT inline a bespoke `generateHandoff(...) + makeResult("failure", {...})` block
- **AND** a static check SHALL fail if any such inline block remains

#### Scenario: failure-envelope-byte-identical
- **WHEN** the same internal-failure condition occurs before and after this change (same command, reason, context)
- **THEN** the emitted handoff document and failure result (artifacts, engine_path, handoff_path, summary) SHALL be byte-identical to the pre-change output

### Requirement: pool-lifecycle-single-orchestration

The obscura serve-pool lifecycle (preflight → guard ok+workerOk → findAvailablePort → startObscuraServe → concurrentFetch → stopObscuraServe → catch serial-fallback with reason) SHALL be orchestrated by a single `withObscuraPool` helper rather than inlined per caller. The three current call sites — `runScrape`, `runBatch`, and `runCrawlScrapling` (the latter via the injected `api.pool` bundle, per the `crawl-scrapling-orchestrator-is-a-seam-module` seam surface) — SHALL delegate to `withObscuraPool(repoRoot, urls, workers, fn) → {results, fallbackReason}`. The helper SHALL own preflight guarding, serve/stop ordering (stop-on-throw included), and fallback-reason bookkeeping, so a lifecycle bug is fixed in one place not three.

#### Scenario: all-pool-callers-delegate-to-withObscuraPool
- **WHEN** runScrape, runBatch, or runCrawlScrapling needs parallel obscura fetch
- **THEN** the pool lifecycle (preflight → serve → fetch → stop → fallback) SHALL be owned by `withObscuraPool`
- **AND** the caller SHALL only provide the per-command fetch/conversion logic via the `fn` callback
- **AND** the `crawl_scrapling.mjs` caller SHALL reach `withObscuraPool` via `api.pool.withObscuraPool` (grouped seam surface preserved)

#### Scenario: pool-output-and-fallback-byte-identical
- **WHEN** the same parallel obscura fetch runs before and after this change (same urls, workers, timeout)
- **THEN** the fetch results and the fallback-reason (when preflight fails or serve throws) SHALL be identical to the pre-change behavior
