# Explore Domain: Validation Gates — Merged Spec

> **Merged from**: `explore-architecture-gate`, `explore-strategy-pipeline-bridge`
> **Purpose**: Covers the Architecture Gate (bidirectional strategy↔pipeline alignment validation) and the Strategy-Pipeline Bridge (API-platform-aware fetcher selection, sample converter CLI entry, main.py API config integration).

---

## Part 1 — Source: `explore-architecture-gate`

### Requirement: single-pipeline-validation

The Architecture Gate SHALL validate against a single pipeline converter file (`scripts/pipeline/converters/html_to_markdown.py`) after the converter unification is complete.

`_PIPELINE_FILES` SHALL be reduced from 2 entries back to 1.

#### Scenario: single-file-architecture-gate
- **WHEN** the Architecture Gate initializes
- **THEN** `_PIPELINE_FILES` SHALL contain exactly one entry: the unified `HtmlToMarkdownConverter` path
- **AND** `_PIPELINE_FILES` SHALL NOT include `scripts/explore/sample_converter.py`
- **AND** the gate SHALL validate against only this single file

### Requirement: partial-coverage-removal

The partial_coverage tracking system SHALL be removed from the Architecture Gate, as it is no longer necessary when only one converter file is validated.

A field is either `covered` (referenced in the single pipeline file) or `dead_config` (not referenced). There is no in-between state.

#### Scenario: no-partial-coverage
- **WHEN** the Architecture Gate runs validation
- **THEN** the `strategy_to_pipeline` result SHALL NOT contain a `partial_coverage` key
- **AND** a field is either `covered` or `dead_config`

### Requirement: dead-config-detection-simplified

The dead config detection logic SHALL be simplified back to single-file scanning, removing the dual-file aggregation logic (`_detect_dead_config_dual()`).

The original `_detect_dead_config()` function (single file) SHALL be restored as the primary detection mechanism.

#### Scenario: dead-config-single-file
- **WHEN** `_detect_dead_config()` is called with a pipeline path
- **THEN** it SHALL scan only that one file for config field references
- **AND** the return type SHALL be `list[str]` (no more tuple with partial_coverage)

---

## Part 2 — Source: `explore-strategy-pipeline-bridge`

### Requirement: api-platform-aware-fetcher-selection

`selectFetcher()` in `chrome-agent-cli.mjs` SHALL detect `strategy.document.api.platform` and return `"mediawiki-api"` when the platform is `"mediawiki"` or `"mediawiki-fandom"`, BEFORE falling through to scrapling-based engine checks.

#### Scenario: mediawiki-platform-returns-api
- **WHEN** `selectFetcher(strategy, page)` is called
- **AND** `strategy.document.api.platform` is `"mediawiki"` or `"mediawiki-fandom"`
- **THEN** the function SHALL return `"mediawiki-api"`
- **THEN** the function SHALL NOT check `engine_preference`, `protection_level`, or `anti_crawl_refs`

#### Scenario: no-api-platform-falls-through
- **WHEN** `strategy.document.api` is absent or `api.platform` is undefined
- **THEN** the function SHALL continue with existing checks

### Requirement: mediawiki-api-engine-handler

`runEngineFetch()` SHALL handle the `"mediawiki-api"` fetcher name by calling `runMediawikiApiFetch()` which fetches HTML via the MediaWiki `action=parse` API.

#### Scenario: api-fetch-calls-parse-endpoint
- **WHEN** `runMediawikiApiFetch()` executes
- **THEN** it SHALL read `strategy.document.api.base_url`
- **THEN** it SHALL call `{base_url}?action=parse&page={title}&redirects=true&prop=text&format=json`
- **THEN** it SHALL write the HTML content to `outputPath`

### Requirement: sample-converter-cli-entry

`scripts/explore/sample_converter.py` SHALL provide `main()` with `apply` and `fetch-and-apply` subcommands.

#### Scenario: apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py apply --strategy <path> --html <path> --title <name> --output <path>` is invoked
- **THEN** it SHALL load extraction rules, read HTML, produce Markdown, write to `--output`

#### Scenario: fetch-and-apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py fetch-and-apply --strategy <path> --page <title> --output <path>` is invoked
- **THEN** it SHALL read `base_url` from strategy, fetch HTML via MediaWiki API, produce Markdown

### Requirement: main-py-api-config-aware-engine

`scripts/explore/main.py` SHALL check `api_config` before falling back to the probe chain engine when selecting the sample conversion engine.

#### Scenario: api-config-prioritized
- **WHEN** `main.py` selects the engine for sample conversion
- **AND** `api_config` is not None and `api_config.get("type") == "mediawiki"`
- **THEN** `engine` SHALL be set to `"mediawiki-api"`

#### Scenario: no-api-config-falls-through
- **WHEN** `api_config` is None or not a known API type
- **THEN** the existing logic SHALL apply

### Requirement: skill-md-sample-conversion-route

The chrome-agent SKILL.md SHALL include a "Route to sample conversion" section documenting the standard path from matched strategy to strategy-driven sample conversion using the sample converter CLI.

#### Scenario: agent-reads-skill
- **WHEN** an agent reads SKILL.md after `explore` returns a matched strategy
- **THEN** the agent SHALL find instructions for:
  1. Reading the strategy file
  2. Selecting 3-7 representative sample pages
  3. Running `python3 scripts/explore/sample_converter.py fetch-and-apply` for each sample
  4. Running self-check on converted samples
  5. Presenting quality report before user confirmation
