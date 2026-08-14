# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch`
- 来源: `proposal.md` / 已确认 capabilities（用户确认：仅 Modified fetch）
- 变更类型: `modified`
- 用户确认摘要: scrape 属于 fetch 能力域（fetch spec `failure-envelope-single-implementation` 已将 scrape 列为覆盖 handler）；本 change 新增 `scrape-orchestrator-is-a-seam-module` requirement，与既有 `crawl-scrapling-orchestrator-is-a-seam-module` 同型；纯结构重构，scrape 外部行为字节级不变

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: scrape-orchestrator-is-a-seam-module

The scrape orchestrator (`runScrape`) SHALL live in `scripts/lib/scrape.mjs`, not inline in `scripts/chrome-agent-cli.mjs`. It SHALL accept its operating context as a `ctx` object (`repoRoot`, `repoRef`, `resolutionMode`, `targetUrl`) plus an `opts` object (`maxPages`, `sameDomain`, `matchPattern`, `markdown`, `merge`, `concurrency`, `fetcherOverride`, `keepHtml`, `reportOverride`, `parallel`, `workers`), plus an injected `api` bundle, replacing the prior 4 positional parameters. Because `runScrape` depends on ~13 internal cli.mjs helpers (setup, result-builders, scrapling preflight, engine fetch, obscura pool, conversion), it SHALL receive them via the injected `api` bundle rather than via circular imports. Only `runScrape` itself moves; all helpers stay in cli.mjs. This makes the BFS traversal / partial_success downgrade / parallel-fallback logic unit-testable with a stub `api`, without spawning Chrome or touching a real filesystem.

**Seam surface shape (沿用 crawl_scrapling 既有模式)**: The `api` bundle SHALL be organized as named concern objects, not a flat grab-bag. The canonical groups for the scrape seam are: `api.fs` (the `node:fs` module), `api.log` (`console`), `api.report` (makeResult, absoluteArtifact, writeTextFile, buildScrapeReport), `api.handoff` (generateHandoff, internalFailure), `api.engine` (runEngineFetch, runScraplingPreflight), `api.pool` (withObscuraPool, runObscuraPreflight), `api.traversal` (extractAllLinks), `api.convert` (convertTraversalToMarkdown, collectMarkdownArtifacts), and setup helpers (buildRunPaths, ensureDir, shouldEmitReport) SHALL be reachable via the bundle (e.g. an `api.setup` group or passed in `ctx` as pre-computed values). Every call site in `scrape.mjs` SHALL use the `api.<group>.<helper>` form; flat `api.<helper>` calls and bare-identifier calls to bundled helpers are FORBIDDEN.

**Call-site discipline (与 crawl_scrapling C4 不变量同型)**: Because the module is an independent ESM unit that does NOT import the cli.mjs helpers, every helper received via the `api` bundle SHALL be referenced through the `api.` namespace at every call site within `scrape.mjs`. Bare identifier calls to bundled helpers are FORBIDDEN — a bare identifier resolves to nothing in module scope and throws `ReferenceError` at runtime.

**Rationale boundary (不可移动 shared helper)**: Helpers that have callers elsewhere in cli.mjs (buildRunPaths, ensureDir, shouldEmitReport, runEngineFetch, runScraplingPreflight, withObscuraPool, convertTraversalToMarkdown, collectMarkdownArtifacts, extractAllLinks, buildScrapeReport, makeResult, absoluteArtifact, writeTextFile, internalFailure, generateHandoff) SHALL remain in cli.mjs and reach the seam only via the `api` bundle — moving them into `scrape.mjs` would create a circular import or force duplication. This change reshapes the bundle surface; it does NOT relocate shared helpers. In particular `extractAllLinks` and `buildScrapeReport` are scrape-specific in usage (only `runScrape` calls them) but SHALL still be injected via the bundle rather than copy-moved, to keep the module import-free of cli.mjs.

**Byte-identical invariant**: The scrape command output (manifest, report, merged markdown, artifacts) SHALL be byte-identical to the pre-change output for the same target + opts. This is a pure structural refactor, not a behavioral change.

**Markdown-artifact branch coverage**: The default scrape path runs with `opts.markdown === true`, which SHALL collect per-page markdown artifacts via `api.convert.collectMarkdownArtifacts(runDir)`. This branch SHALL be covered by at least one regression test exercising `markdown: true`; tests that only exercise `markdown: false` do NOT satisfy this requirement.

#### Scenario: orchestrator-extractable-and-importable
- **WHEN** the orchestrator module `scripts/lib/scrape.mjs` is imported in a test
- **THEN** `runScrape` SHALL be callable with a `ctx` object + an `api` bundle whose side-effecting members are stubbed, exercising BFS traversal / manifest / result synthesis without spawning Chrome or a real filesystem

#### Scenario: scrape-output-byte-identical
- **WHEN** the same scrape command runs before and after this change (same target, opts)
- **THEN** the manifest, report, and merged output SHALL be byte-identical (pure seam-surface reshape, no behavioral change)

#### Scenario: api-bundle-built-at-dispatch-site
- **WHEN** cli.mjs delegates to `runScrape` at its dispatch site (scrape command case)
- **THEN** it SHALL build the `scrapeApi` bundle once as named concern objects and pass it alongside `ctx` + `opts`; no circular import exists between `scrape.mjs` and `chrome-agent-cli.mjs`

#### Scenario: all-bundled-helpers-called-via-api-prefix
- **WHEN** `scrape.mjs` references any helper that is a member of the injected `api` bundle
- **THEN** the reference SHALL be qualified with the `api.<group>.` namespace; no bare-identifier call SHALL appear
- **AND** a static discipline test SHALL fail if a bare-identifier call to any bundled helper is present in `scrape.mjs`

#### Scenario: seam-surface-uses-named-concern-groups
- **WHEN** `scrape.mjs` references a helper that belongs to a declared concern group (report, handoff, engine, pool, traversal, convert, setup)
- **THEN** the call SHALL use the `api.<group>.<helper>` form
- **AND** a static discipline test SHALL fail if any flat `api.<helper>` call to a groupable helper appears in the module
- **AND** the cli.mjs bundle construction SHALL group helpers identically (same group → same helpers)

#### Scenario: markdown-true-branch-produces-artifacts
- **WHEN** `runScrape` is invoked with `opts.markdown === true` (the default) and the traversal reaches the final-artifact assembly block
- **THEN** it SHALL call `api.convert.collectMarkdownArtifacts(runDir)` and append the result to `finalArtifacts`
- **AND** it SHALL NOT throw `ReferenceError`
- **AND** at least one regression test SHALL exercise this path with `markdown: true`

#### Scenario: preflight-failure-emits-handoff-via-internalfailure
- **WHEN** `api.engine.runScraplingPreflight` returns `{ ok: false }` before traversal
- **THEN** `runScrape` SHALL delegate to `api.handoff.internalFailure({...})` to build the failure result (per the `failure-envelope-single-implementation` requirement)
- **AND** SHALL NOT inline a bespoke `generateHandoff(...) + makeResult("failure", {...})` block

#### Scenario: parallel-fallback-delegates-to-withobscurapool
- **WHEN** `runScrape` is invoked with `opts.parallel === true`
- **THEN** it SHALL reach the pool lifecycle via `api.pool.withObscuraPool(...)` (per the `pool-lifecycle-single-orchestration` requirement)
- **AND** SHALL NOT inline the preflight/serve/stop/fallback bookkeeping
