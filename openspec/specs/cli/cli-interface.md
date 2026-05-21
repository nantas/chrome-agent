# CLI Domain: Interface — Merged Spec

> **Merged from**: `global-capability-cli`, `global-workflow-skill`
> **Purpose**: Defines the CLI command surface, internal routing structure, structured result format, handoff gate integration, and the global workflow skill's result passthrough and packaging rules.

---

## Part 1 — Source: `global-capability-cli`

### Requirement: Crawl internal routing structure

`runCrawl()` SHALL be a thin routing entry point delegating to three dispatch functions:

- `runCrawlMediawikiApi(repoRoot, strategy, runDir, targetUrl, opts)` — MediaWiki API pipeline path
- `runCrawlScraplingDiscovery(repoRoot, strategy, runDir, targetUrl, startPage, opts)` — Scrapling link discovery
- `runCrawlScrapling(repoRoot, strategy, runDir, targetUrl, startPage, opts)` — Standard Scrapling bounded crawl

`runCrawl()` routing:
- `apiConfig.platform === "mediawiki"` → `runCrawlMediawikiApi()`
- `discoveryOnly && !doc?.api?.platform` → `runCrawlScraplingDiscovery()`
- Otherwise → `runCrawlScrapling()`

#### Scenario: External interface preservation
- **WHEN** any dispatch path produces a result
- **THEN** result structure (`command`, `target`, `repoRef`, `summary`, `artifacts`, `nextAction`, `result`, `extra`) SHALL be identical to pre-refactoring output
- **AND** all CLI parameters (`--max-pages`, `--discovery-only`, `--phase`, `--re-fetch`, `--from-manifest`, `--exclude-category`, `--parallel`, `--concurrency`, `--keep-html`, `--merge`, `--report`, `--yes`) SHALL behave identically

### Requirement: Crawl function size governance

- `runCrawl()` SHALL NOT exceed 80 lines
- Each dispatch function SHALL NOT exceed 400 lines

### Requirement: maxPages null semantics

`--max-pages` CLI parameter and `maxPages` function parameter SHALL use `null` to express "no limit":

- When `--max-pages` is not provided on CLI, `parsed.maxPages` SHALL be `null`, meaning no page limit
- When `--max-pages N` is provided, `maxPages` SHALL be `N`, limiting to N pages
- All dispatch functions (`runCrawl`, `runCrawlMediawikiApi`, `runCrawlScrapling`, `runScrape`) SHALL default `maxPages` to `null` in destructuring
- All conditions using `maxPages` SHALL be null-safe: `if (maxPages != null)` for spawnSync args, `(maxPages == null || ... < maxPages)` for loop/queue guards

#### Scenario: crawl without max-pages
- **WHEN** CLI user runs `crawl` without `--max-pages`
- **THEN** crawl SHALL NOT limit number of pages

#### Scenario: crawl with max-pages
- **WHEN** CLI user runs `crawl --max-pages 50`
- **THEN** crawl SHALL limit to 50 pages

---

## Part 2 — Source: `global-workflow-skill`

### Requirement: Structured result passthrough

The global workflow skill SHALL derive its final user-facing result from the CLI JSON contract.

When CLI result contains `handoff_path`, the skill SHALL:
1. Recognize it as chrome-agent-repo-bound signal
2. Invoke Handoff Gate protocol
3. Present structured halting message

When no `handoff_path`, existing passthrough applies.

#### Scenario: CLI result passthrough without handoff
- **WHEN** CLI result does not contain `handoff_path`
- **THEN** skill SHALL use CLI JSON result as source of truth for `result`, `summary`, `artifacts`, and remediation

#### Scenario: CLI result with handoff blocks passthrough
- **WHEN** CLI result contains `handoff_path`
- **THEN** skill SHALL trigger Handoff Gate protocol
- **THEN** Handoff Gate SHALL take precedence over normal result packaging

### Requirement: Result packaging format

Preferred output shape:

```
result: <success|partial_success|failure>
command: <fetch|explore|crawl|doctor>
target: <url or runtime>
repo_ref: <repo://chrome-agent|path:...|env:CHROME_AGENT_REPO>
summary: <brief backend-grounded summary>
artifacts:
- <absolute path>
next_action: <none or remediation>
workflow: <content_retrieval|platform_analysis|runtime_support>
engine_path: <backend path summary>
handoff_path: <absolute path>          (only when handoff generated)
handoff_summary: <one-line summary>     (only when handoff_path present)
```

When `handoff_path` present, `next_action` SHALL contain: "The problem must be resolved in the chrome-agent repository. See handoff document at <handoff_path>."
