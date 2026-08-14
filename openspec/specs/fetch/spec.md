# Specification: fetch

## Purpose

fetch 能力负责从目标站点获取原始内容（HTML / MediaWiki wikitext / API JSON）。内核统一为 pipeline MediaWiki API 与 CDP fetch 阶段；`.mjs` 层与 explore 探测通过委托内核复用同一语义，避免多套 API client。抓取引擎（scrapling / cloakbrowser / obscura 等）经 `runEngineFetch` 路由，能力本身不绑定单一引擎。

## Capability 对齐

- Capability: `fetch`
- 4 维坐标: `(capability=fetch, execution_path=mirrors, strategy_variant=none, input_format=api|html|browser)`
- 镜像模型: 同一语义（获取内容），不同引擎/协议，分别实现
- 合并: `.mjs` mediawiki-api fetch → pipeline F1 统一

## 架构声明

```
Fetch 能力
├── kernel
│   ├── pipeline MediaWiki API: scripts/pipeline/pipeline/phases/fetch.py
│   ├── pipeline CDP: scripts/pipeline/pipeline/phases/fetch_cdp.py
│   └── explore probe: scripts/explore/probe_chain.py (多引擎探测)
├── 基础设施 (不注册为能力):
│   ├── chrome-agent-cli.mjs runEngineFetch() — 引擎路由
│   └── 各引擎适配器 (runScraplingFetch, runCloakbrowserFetch, etc.)
└── 引擎注册: configs/engine-registry.json + configs/engine-versions.json
```

## 已有行为规范

| 规范 | 内容 |
|------|------|
| `openspec/specs/pipeline-fetch-phase/spec.md` | Pipeline fetch 阶段流程 |
| `openspec/specs/mediawiki-api-contract/spec.md` | MediaWiki API 调用契约 |
## Requirements
### Requirement: unified-mediawiki-fetch-kernel

All MediaWiki API fetch operations SHALL route through `scripts/pipeline/pipeline/phases/fetch.py` as the single kernel. The `.mjs` Node.js layer SHALL delegate via subprocess rather than implementing its own API client.

#### Scenario: mjs-delegates-to-fetch-kernel
- **WHEN** `.mjs` needs to fetch a MediaWiki page
- **THEN** it SHALL call the pipeline fetch kernel (via subprocess or import)
- **AND** SHALL NOT spawn `standalone.py` for page fetching

### Requirement: probe-chain-as-explore-fetch

`scripts/explore/probe_chain.py` SHALL remain the explore path's fetch implementation, probing multiple engines in serial order to discover which engine can successfully fetch this site.

#### Scenario: probe-chain-discovers-viable-engine
- **WHEN** an explore operation needs to fetch a page
- **THEN** probe_chain SHALL try engines in order until one succeeds
- **AND** return the successful engine name and fetched HTML

### Requirement: crawl-scrapling-orchestrator-is-a-seam-module

The scrapling crawl orchestrator (`runCrawlScrapling`) SHALL live in `scripts/lib/crawl_scrapling.mjs`, not inline in `scripts/chrome-agent-cli.mjs`. It SHALL accept its operating context as a `ctx` object plus an `opts` object, replacing the prior 12 positional parameters. Because the function depends on internal cli.mjs helpers, it SHALL receive them via an injected `api` bundle rather than via circular imports. Only `runCrawlScrapling` itself moves; all helpers stay in cli.mjs. This makes the traversal/manifest/handoff logic unit-testable with a stub `api`.

**Call-site discipline (C4 不变量，保留)**: Because the module is an independent ESM unit that does NOT import the cli.mjs helpers, every helper received via the `api` bundle SHALL be referenced through the `api.` namespace at every call site within `crawl_scrapling.mjs`. Bare identifier calls to bundled helpers are FORBIDDEN — a bare identifier resolves to nothing in module scope and throws `ReferenceError` at runtime.

**Seam surface shape (本 change 新增)**: The `api` bundle SHALL be organized as **named concern objects**, not a flat grab-bag. Each concern group gathers the helpers that belong to one responsibility. The canonical groups are: `api.fs` (filesystem), `api.log` (logging), `api.report` (result/file builders: makeResult, absoluteArtifact, writeTextFile, buildCrawlReport), `api.handoff` (generateHandoff), `api.engine` (runEngineFetch, selectFetcher), `api.cache` (scrapling cache lifecycle: scraplingCacheDir, ensureDir, isScraplingCached, saveScraplingCache, scraplingSlugFromUrl, loadScraplingCache, buildScraplingExtractionArgs, runScraplingPreflight), `api.pool` (obscura serve-pool: findAvailablePort, startObscuraServe, concurrentFetch, stopObscuraServe, runObscuraPreflight), `api.traversal` (pagePatternMatches, collectLinksFromHtml, nextPaginationUrl), `api.convert` (convertTraversalToMarkdown, collectMarkdownArtifacts, urlToStructuredPath). Every call site in `crawl_scrapling.mjs` SHALL use the `api.<group>.<helper>` form; flat `api.<helper>` calls are FORBIDDEN after this change. The cli.mjs bundle construction SHALL match this grouping. A static discipline test SHALL assert both invariants: (a) no bare-identifier call to any bundled helper, (b) no flat `api.<helper>` call to a helper that belongs to a declared group.

**Rationale boundary (不可移动 shared helper)**: Helpers that have callers elsewhere in cli.mjs (pagePatternMatches, selectFetcher, buildScraplingExtractionArgs, convertTraversalToMarkdown, collectMarkdownArtifacts, collectLinksFromHtml, urlToStructuredPath, scraplingSlugFromUrl) SHALL remain in cli.mjs and reach the seam only via the `api` bundle — moving them into `crawl_scrapling.mjs` would create a circular import or force duplication. This change reshapes the bundle surface; it does NOT relocate shared helpers.

**Markdown-artifact branch coverage (C4 保留)**: The default crawl path runs with `opts.markdown === true`, which SHALL collect per-page markdown artifacts via `api.convert.collectMarkdownArtifacts(runDir)` into `finalArtifacts`. This branch SHALL be covered by at least one regression test exercising `markdown: true`; tests that only exercise `markdown: false` do NOT satisfy this requirement.

#### Scenario: orchestrator-extractable-and-importable
- **WHEN** the orchestrator module is imported in a test
- **THEN** `runCrawlScrapling` SHALL be callable with a `ctx` object + an `api` bundle whose side-effecting members are stubbed, exercising traversal/manifest/handoff without spawning Chrome

#### Scenario: crawl-output-byte-identical
- **WHEN** the same crawl command runs before and after this change (same target, strategy, opts)
- **THEN** the manifest, report, and merged output SHALL be byte-identical (pure seam-surface reshape, no behavioral change)

#### Scenario: api-bundle-built-once-in-cli
- **WHEN** cli.mjs delegates to `runCrawlScrapling` at its 3 call sites
- **THEN** it SHALL build the `api` bundle once as named concern objects (api.report, api.engine, api.cache, api.pool, api.traversal, api.convert, api.handoff, api.fs, api.log) and pass it; no circular import exists

#### Scenario: all-bundled-helpers-called-via-api-prefix
- **WHEN** `crawl_scrapling.mjs` references any helper that is a member of the injected `api` bundle
- **THEN** the reference SHALL be qualified with the `api.` namespace (preserved from C4); no bare-identifier call SHALL appear

#### Scenario: markdown-true-branch-produces-artifacts-not-reference-error (C4 保留)
- **WHEN** `runCrawlScrapling` is invoked with `opts.markdown === true` (the default) and the traversal reaches the final-artifact assembly block
- **THEN** it SHALL call `api.convert.collectMarkdownArtifacts(runDir)` and append the result to `finalArtifacts`
- **AND** it SHALL NOT throw `ReferenceError: collectMarkdownArtifacts is not defined`
- **AND** at least one regression test SHALL exercise this path with `markdown: true` and assert the artifacts list is non-empty / well-formed rather than catching a thrown error

#### Scenario: seam-surface-uses-named-concern-groups
- **WHEN** `crawl_scrapling.mjs` references a helper that belongs to a declared concern group (report, handoff, engine, cache, pool, traversal, convert)
- **THEN** the call SHALL use the `api.<group>.<helper>` form
- **AND** a static discipline test SHALL fail if any `api.<helper>` flat call to a groupable helper appears in the module
- **AND** the cli.mjs bundle construction SHALL group helpers identically (same group → same helpers)

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

