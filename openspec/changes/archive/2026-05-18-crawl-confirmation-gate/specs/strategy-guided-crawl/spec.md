# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-guided-crawl`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: explore 阶段确认 —— CLI `crawl` 命令新增 `--discovery-only`、`--from-manifest`、`--yes`、`--exclude-category` 参数；Scrapling 路径新增首页链接发现模式

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/strategy-guided-crawl/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: discovery-only-mode

The `crawl` command SHALL support a `--discovery-only` flag that stops execution after the discovery phase, producing `discovery_summary.json` and (for API path) `page_manifest.json`, without proceeding to extraction or assembly.

#### Scenario: api-pipeline-discovery-only

- **WHEN** `crawl <url> --discovery-only` targets a site with `api.platform: "mediawiki"`
- **THEN** the command SHALL route to the MediaWiki API pipeline with `--phase discover`
- **AND** the pipeline SHALL run only the discovery phase (homepage or allpages, per `--discovery` resolution)
- **AND** the pipeline SHALL produce `page_manifest.json` and `discovery_summary.json` in the run directory
- **AND** the pipeline SHALL exit after discovery without running extraction or assembly
- **AND** the result SHALL include `discovery_summary_path` and `manifest_path` in artifacts

#### Scenario: scrapling-discovery-only

- **WHEN** `crawl <url> --discovery-only` targets a non-API site
- **THEN** the command SHALL fetch the strategy's main page using the configured fetcher
- **AND** the command SHALL extract all links matching the strategy's `links_to` selectors
- **AND** the command SHALL group discovered URLs by matching `structure.pages[].id` patterns
- **AND** the command SHALL produce `discovery_summary.json` with `discovery_method: "first_level_links"`
- **AND** the summary SHALL include `caveats` documenting the first-level-only limitation
- **AND** the result shall have `manifest_path: null`

#### Scenario: discovery-only-does-not-run-extraction

- **WHEN** `--discovery-only` is passed
- **THEN** the command SHALL NOT invoke Phase B extraction
- **AND** the command SHALL NOT invoke Phase C assembly
- **AND** the command SHALL NOT invoke Markdown conversion
- **AND** the run directory SHALL NOT contain `.md` files from extraction

### Requirement: from-manifest-resume

The `crawl` command SHALL support a `--from-manifest <path>` flag that skips the discovery phase and proceeds directly to extraction and assembly using the specified manifest file.

#### Scenario: api-pipeline-from-manifest

- **WHEN** `crawl <url> --from-manifest <path/to/page_manifest.json>` targets a site with `api.platform: "mediawiki"`
- **THEN** the command SHALL load the manifest from the specified path
- **AND** the command SHALL route to the MediaWiki API pipeline with `--phase extract` (for extraction) or `--phase all` (for extraction + assembly)
- **AND** the pipeline SHALL skip discovery and use the loaded manifest
- **AND** the pipeline SHALL run extraction and assembly normally

#### Scenario: scrapling-from-manifest

- **WHEN** `crawl <url> --from-manifest <path>` targets a non-API site
- **THEN** the command SHALL load the manifest's `visited` URLs
- **AND** the command SHALL seed the traversal queue with the loaded URLs
- **AND** the command SHALL skip initial entry-point discovery

#### Scenario: from-manifest-with-exclusions

- **WHEN** `--from-manifest` is combined with `--exclude-category`
- **THEN** the command SHALL filter out pages belonging to excluded categories before extraction
- **AND** filtering SHALL be applied to the in-memory manifest, not written back to the file

### Requirement: yes-no-confirm-flag

The `crawl` command SHALL accept a `--yes` flag (aliased as `--no-confirm` in negation form). This flag is a passthrough signal: the CLI SHALL include it in the result JSON for the SKILL to consume, but the CLI itself SHALL NOT change behavior based on this flag.

The default behavior (no `--yes`) SHALL NOT differ from `--yes` at the CLI level — the gate is a SKILL-layer concern.

#### Scenario: yes-flag-included-in-result

- **WHEN** `crawl <url> --yes` is invoked
- **THEN** the result JSON SHALL include `confirmation_bypassed: true`
- **AND** the CLI SHALL run the full crawl (discovery + extraction + assembly) normally

#### Scenario: no-yes-flag-default

- **WHEN** `crawl <url>` is invoked without `--yes`
- **THEN** the result JSON SHALL include `confirmation_bypassed: false`
- **AND** the CLI SHALL run the full crawl normally
- **AND** the SKILL MAY interpret `confirmation_bypassed: false` as a signal to invoke the confirmation gate

### Requirement: exclude-category-runtime-filter

The `crawl` command SHALL support a repeatable `--exclude-category <name>` flag that filters categories during the extraction phase without modifying the strategy file.

#### Scenario: single-exclusion

- **WHEN** `crawl <url> --from-manifest <path> --exclude-category Music` is invoked
- **THEN** pages in the "Music" category SHALL be excluded from extraction
- **AND** the strategy file SHALL NOT be modified
- **AND** the exclusion SHALL be reflected in the extraction results

#### Scenario: multiple-exclusions

- **WHEN** `crawl <url> --from-manifest <path> --exclude-category Music --exclude-category Modding` is invoked
- **THEN** pages in both "Music" and "Modding" SHALL be excluded
- **AND** the strategy file SHALL NOT be modified

#### Scenario: exclusion-with-strategy-level-exclusions

- **WHEN** the strategy already has `api.exclude_categories: ["Music"]`
- **AND** `--exclude-category Modding` is also passed
- **THEN** the merged exclusion set SHALL include both "Music" and "Modding"
- **AND** `--exclude-category` values SHALL be merged (union) with strategy-level exclusions

### Requirement: scrapling-first-level-discovery

The Scrapling crawl path SHALL support a first-level discovery mode that extracts links from the main page and groups them by strategy page type, without performing recursive traversal.

#### Scenario: first-level-link-extraction

- **WHEN** `crawl <url> --discovery-only` targets a non-API site with a strategy defining `structure.pages` and `links_to` selectors
- **THEN** the command SHALL fetch the main page HTML
- **AND** the command SHALL apply all declared `links_to[*].selector` CSS selectors to extract links
- **AND** the command SHALL group links by matching `structure.pages[].url_pattern` against each discovered URL
- **AND** the command SHALL deduplicate URLs within each group
- **AND** the command SHALL produce `discovery_summary.json` with per-group counts

#### Scenario: first-level-caveat

- **WHEN** `discovery_summary.json` is produced by the Scrapling path
- **THEN** `discovery_method` SHALL be `"first_level_links"`
- **AND** `caveats` SHALL contain at minimum a message stating that only first-level links were discovered
- **AND** `page_count` values SHALL represent the count of unique first-level URLs (not a precise count after full traversal)
