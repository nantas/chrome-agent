# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-strategy-pipeline-bridge`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: 用户基于完整问题分析方案确认此 change，拆分 13 个问题为 10 项修复任务，分 3 个 Phase 执行

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: api-platform-aware-fetcher-selection

`selectFetcher()` in `chrome-agent-cli.mjs` SHALL detect `strategy.document.api.platform` and return `"mediawiki-api"` when the platform is `"mediawiki"` or `"mediawiki-fandom"`, BEFORE falling through to scrapling-based engine checks.

#### Scenario: mediawiki-platform-returns-api
- **WHEN** `selectFetcher(strategy, page)` is called
- **AND** `strategy.document.api.platform` is `"mediawiki"` or `"mediawiki-fandom"`
- **THEN** the function SHALL return `"mediawiki-api"`
- **THEN** the function SHALL NOT check `engine_preference`, `protection_level`, or `anti_crawl_refs`

#### Scenario: no-api-platform-falls-through
- **WHEN** `selectFetcher(strategy, page)` is called
- **AND** `strategy.document.api` is absent or `api.platform` is undefined
- **THEN** the function SHALL continue with existing checks (`engine_preference` → `protection` → `page_type`)
- **THEN** the existing default `return "get"` SHALL remain unchanged

### Requirement: mediawiki-api-engine-handler

`runEngineFetch()` in `chrome-agent-cli.mjs` SHALL handle the `"mediawiki-api"` fetcher name by calling a new `runMediawikiApiFetch()` function that fetches HTML via the MediaWiki `action=parse` API.

#### Scenario: api-fetch-dispatches
- **WHEN** `runEngineFetch(repoRoot, "mediawiki-api", targetUrl, outputPath, extraArgs)` is called
- **THEN** the function SHALL call `runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs)`
- **THEN** it SHALL NOT call `runScraplingFetch()` or `runCloakbrowserFetch()`

#### Scenario: api-fetch-calls-parse-endpoint
- **WHEN** `runMediawikiApiFetch()` executes
- **THEN** it SHALL read `strategy.document.api.base_url` to determine the API endpoint
- **THEN** it SHALL extract the page title from `targetUrl` (strip `/wiki/` prefix, decode `_` to spaces)
- **THEN** it SHALL call `{base_url}?action=parse&page={title}&redirects=true&prop=text&format=json`
- **THEN** it SHALL extract `data.parse.text["*"]` as HTML
- **THEN** it SHALL write the HTML content to `outputPath`

### Requirement: sample-converter-cli-entry

`scripts/explore/sample_converter.py` SHALL provide a `main()` function with an `argparse` CLI supporting `apply` and `fetch-and-apply` subcommands for standalone invocation.

#### Scenario: apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py apply --strategy <path> --html <path> --title <name> --output <path>` is invoked
- **THEN** it SHALL load extraction rules from the strategy file's YAML frontmatter
- **THEN** it SHALL read HTML from `--html` file
- **THEN** it SHALL call `_apply_extraction(html, extraction_rules, {title})` to produce Markdown
- **THEN** it SHALL write the Markdown to `--output`
- **THEN** it SHALL print `{ "ok": true, "output": "<path>", "length": <int> }` to stdout

#### Scenario: fetch-and-apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py fetch-and-apply --strategy <path> --page <title> --output <path>` is invoked
- **THEN** it SHALL read `base_url` from strategy's `image_handling.base_url` (fallback to `api.base_url`)
- **THEN** it SHALL call `_fetch_via_mediawiki_api(base_url, page_title, temp_html_path)` to get HTML
- **THEN** it SHALL call `_apply_extraction(html, extraction_rules, {page_title})` to produce Markdown
- **THEN** it SHALL write the Markdown to `--output`

### Requirement: main-py-api-config-aware-engine

`scripts/explore/main.py` SHALL check `api_config` before falling back to the probe chain engine when selecting the sample conversion engine.

#### Scenario: api-config-prioritized
- **WHEN** `main.py` selects the engine for sample conversion
- **AND** `api_config` is not None and `api_config.get("type") == "mediawiki"`
- **THEN** `engine` SHALL be set to `"mediawiki-api"`
- **THEN** the probe chain's `success_engine` SHALL NOT be used

#### Scenario: no-api-config-falls-through
- **WHEN** `api_config` is None or `api_config.get("type")` is not a known API type
- **THEN** the existing logic (`protection.get("engine_override") or probe_result.get("success_engine") or "scrapling-get"`) SHALL apply

### Requirement: skill-md-sample-conversion-route

The chrome-agent SKILL.md SHALL include a "Route to sample conversion" section documenting the standard path from a matched strategy to strategy-driven sample conversion using the sample converter CLI.

#### Scenario: agent-reads-skill
- **WHEN** an agent reads SKILL.md after `explore` returns a matched strategy
- **THEN** the agent SHALL find instructions for:
  1. Reading the strategy file
  2. Selecting 3-7 representative sample pages from taxonomy
  3. Running `python3 scripts/explore/sample_converter.py fetch-and-apply --strategy <path> --page <title> --output <path>` for each sample
  4. Running self-check on converted samples
  5. Presenting quality report before user confirmation
