# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选定 Modified `fetch`——在既有 `crawl-scrapling-orchestrator-is-a-seam-module` requirement 上声明 seam surface 形状契约（named concern objects + `api.<group>.<helper>` 调用约定）。与 C4 修复（commit c51e771）同能力同 requirement，契约闭环。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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
