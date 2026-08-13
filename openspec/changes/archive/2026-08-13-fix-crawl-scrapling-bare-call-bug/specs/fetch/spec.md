# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选定 Modified `fetch`——在既有 `crawl-scrapling-orchestrator-is-a-seam-module` 契约上补调用点 `api.` 前缀纪律不变量 + `markdown:true` 回归覆盖，与原 extract change 同能力同 requirement，契约闭环最自然。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: crawl-scrapling-orchestrator-is-a-seam-module

The scrapling crawl orchestrator (`runCrawlScrapling`) SHALL live in `scripts/lib/crawl_scrapling.mjs`, not inline in `scripts/chrome-agent-cli.mjs`. It SHALL accept its operating context as a `ctx` object (repo_root, repo_ref, resolution_mode, run_dir, report_path, manifest_path, emit_report, target_url, strategy, doc, start_page, matching_page, entry_points) plus an `opts` object (max_pages, concurrency, from_manifest, markdown, ...), replacing the prior 12 positional parameters. Because the function depends on ~26-32 internal cli.mjs helpers (filesystem, result-builders, scrapling/obscura fetch, conversion, markdown-artifact collection), it SHALL receive them via an injected `api` bundle (flat object: `api.fs` + the named helper functions) rather than via circular imports. Only `runCrawlScrapling` itself moves; all helpers stay in cli.mjs. This makes the traversal/manifest/handoff logic unit-testable with a stub `api` (real pure helpers, stubbed side-effecting helpers), without spawning Chrome or touching a real filesystem.

**Call-site discipline (新增不变量)**: Because the module is an independent ESM unit that does NOT import the cli.mjs helpers, every helper received via the `api` bundle SHALL be referenced through the `api.` prefix at every call site within `crawl_scrapling.mjs`. Bare identifier calls to bundled helpers (e.g. `collectMarkdownArtifacts(runDir)` instead of `api.collectMarkdownArtifacts(runDir)`) are FORBIDDEN — a bare identifier resolves to nothing in the module scope and throws `ReferenceError` at runtime. The only top-level import permitted in the module is `node:path` (plus future pure, dependency-free utility modules); any identifier not imported at the top of the module and not declared in module-local scope MUST be accessed via `api.`.

**Markdown-artifact branch coverage**: The default crawl path runs with `opts.markdown === true`, which SHALL collect per-page markdown artifacts via `api.collectMarkdownArtifacts(runDir)` into `finalArtifacts`. This branch SHALL be covered by at least one regression test exercising `markdown: true`; tests that only exercise `markdown: false` do NOT satisfy this requirement.

#### Scenario: orchestrator-extractable-and-importable
- **WHEN** the orchestrator module is imported in a test
- **THEN** `runCrawlScrapling` SHALL be callable with a `ctx` object + an `api` bundle whose side-effecting members (fs, fetch/preflight helpers, port/server helpers) are stubbed, exercising traversal/manifest/handoff without spawning Chrome

#### Scenario: crawl-output-byte-identical
- **WHEN** the same crawl command runs before and after extraction (same target, strategy, opts)
- **THEN** the manifest, report, and merged output SHALL be byte-identical (pure structural refactor, no behavioral change)

#### Scenario: api-bundle-built-once-in-cli
- **WHEN** cli.mjs delegates to `runCrawlScrapling` at its 3 call sites
- **THEN** it SHALL build the `api` bundle once (real `fs` + real helpers + `buildScraplingExtractionArgs` already imported) and pass it, alongside `ctx` + `opts`; no circular import exists between crawl_scrapling.mjs and cli.mjs

#### Scenario: all-bundled-helpers-called-via-api-prefix
- **WHEN** `crawl_scrapling.mjs` references any helper that is a member of the injected `api` bundle (including but not limited to `collectMarkdownArtifacts`, `runScraplingPreflight`, `runEngineFetch`, `generateHandoff`, `makeResult`, `absoluteArtifact`, `writeTextFile`, `findAvailablePort`, `startObscuraServe`, `stopObscuraServe`, `runObscuraPreflight`)
- **THEN** the reference SHALL be qualified with the `api.` prefix; no bare-identifier call to a bundled helper SHALL appear in the module
- **AND** a module-level static check (test) SHALL grep the module source for bundled-helper bare calls and fail if any exist

#### Scenario: markdown-true-branch-produces-artifacts-not-reference-error
- **WHEN** `runCrawlScrapling` is invoked with `opts.markdown === true` (the default) and the traversal reaches the final-artifact assembly block
- **THEN** it SHALL call `api.collectMarkdownArtifacts(runDir)` and append the result to `finalArtifacts`
- **AND** it SHALL NOT throw `ReferenceError: collectMarkdownArtifacts is not defined`
- **AND** at least one regression test SHALL exercise this path with `markdown: true` and assert the artifacts list is non-empty / well-formed rather than catching a thrown error
