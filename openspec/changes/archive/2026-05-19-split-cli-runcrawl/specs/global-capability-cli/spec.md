# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-capability-cli`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认本次为纯内部重构，将 `runCrawl()` 拆分为三路独立调度函数，外部接口不变

## 规范真源声明

- 本文件是 `global-capability-cli` 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/global-capability-cli/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Crawl internal routing structure

The `crawl` command's internal implementation SHALL separate the three mutually-exclusive dispatch paths into independent functions, with `runCrawl()` acting solely as a thin routing entry point that selects and delegates to the appropriate path.

The three dispatch functions SHALL be:

- `runCrawlMediawikiApi(repoRoot, strategy, runDir, targetUrl, opts)` — SHALL handle the MediaWiki API pipeline path, spawning `python3 -m scripts.pipeline` with appropriate arguments and returning `makeResult()` directly
- `runCrawlScraplingDiscovery(repoRoot, strategy, runDir, targetUrl, startPage, opts)` — SHALL handle the Scrapling first-level link discovery path, fetching the homepage via `runEngineFetch()`, extracting links via `collectLinksFromHtml()`, building a discovery summary, and returning `makeResult()` directly
- `runCrawlScrapling(repoRoot, strategy, runDir, targetUrl, startPage, opts)` — SHALL handle the standard Scrapling bounded crawl path, including preflight, queue-driven traversal loop, Phase 2 Markdown conversion (with parallel/Obscura fallback), manifest writing, artifact collection, and returning `makeResult()` directly

`runCrawl()` AFTER refactoring SHALL:

- Parse opts into named variables (unchanged from current behavior)
- Resolve strategy, entry points, and start page (unchanged)
- Route to `runCrawlMediawikiApi()` when `apiConfig.platform === "mediawiki"`
- Route to `runCrawlScraplingDiscovery()` when `discoveryOnly && !doc?.api?.platform`
- Route to `runCrawlScrapling()` for all other cases
- NOT contain any crawl traversal logic, spawn logic, or artifact collection logic directly

#### Scenario: MediaWiki API crawl routing

- **WHEN** `runCrawl()` detects `apiConfig.platform === "mediawiki"`
- **THEN** it SHALL delegate to `runCrawlMediawikiApi()` and return its result directly
- **AND** `runCrawl()` itself SHALL NOT contain any `spawnSync("python3", ...)` calls

#### Scenario: Scrapling discovery-only routing

- **WHEN** `runCrawl()` detects `discoveryOnly && !doc?.api?.platform`
- **THEN** it SHALL delegate to `runCrawlScraplingDiscovery()` and return its result directly
- **AND** `runCrawl()` itself SHALL NOT contain any `collectLinksFromHtml()` calls

#### Scenario: Default Scrapling crawl routing

- **WHEN** `runCrawl()` reaches the default (non-API, non-discovery-only) path
- **THEN** it SHALL delegate to `runCrawlScrapling()` and return its result directly
- **AND** `runCrawl()` itself SHALL NOT contain any queue traversal loop or `selectFetcher()` calls

#### Scenario: External interface preservation

- **WHEN** any of the three dispatch paths produces a result via `makeResult()`
- **THEN** the result structure (`command`, `target`, `repoRef`, `summary`, `artifacts`, `nextAction`, `result`, `extra`) SHALL be identical to the pre-refactoring output
- **AND** all CLI parameter handling (`--max-pages`, `--discovery-only`, `--phase`, `--re-fetch`, `--from-manifest`, `--exclude-category`, `--parallel`, `--concurrency`, `--keep-html`, `--merge`, `--report`, `--yes`) SHALL behave identically

### Requirement: Crawl function size governance

The `crawl` command's implementation SHALL comply with the repository's God Object governance constraint (AGENTS.md §2.5 模式 2): no single function SHALL exceed 300 lines when it combines multiple unrelated responsibilities.

#### Scenario: runCrawl size after refactoring

- **WHEN** the refactoring is complete
- **THEN** `runCrawl()` SHALL NOT exceed 80 lines
- **AND** each of the three extracted dispatch functions SHALL NOT exceed 400 lines

#### Scenario: Each function has a single concern

- **WHEN** reviewing any of the four crawl-related functions
- **THEN** each function SHALL address exactly one dispatch concern (routing, MediaWiki API pipeline, Scrapling discovery, or Scrapling bounded crawl)
