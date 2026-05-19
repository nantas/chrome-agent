# MediaWiki Domain: API — Merged Spec

## Source Attribution

| Source Spec | Type | Notes |
|------------|------|-------|
| `mediawiki-api-contract` | new | MediaWiki action=parse API engine input/output/error contract |
| `mediawiki-api-extraction` | new | MediaWiki API extraction pipeline (discovery, extraction, assembly) |
| `mediawiki-extraction-patterns` | new | Noise taxonomy and cleanup patterns for MediaWiki content |
| `mediawiki-site-strategy` | new | Site strategy schema for MediaWiki sites, content_profile, homepage config |

Paths have been updated to reflect the current directory structure (`scripts/pipeline/`, `scripts.pipeline`).

---

# MediaWiki API Specification

## Purpose

Define the complete MediaWiki API extraction subsystem: the API engine contract, the extraction pipeline (discovery, content extraction, output assembly), noise cleanup patterns for MediaWiki content, and site strategy schema including content_profile and homepage configuration.

---

## API Engine Contract

### Requirement: Input contract — strategy path and target URL

The mediawiki-api engine SHALL accept a strategy file path (to read `api.base_url`) and a target URL (to extract page title) as input parameters.

#### Scenario: Required parameter — strategy path (extraArgs[0])

- **WHEN** `runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs)` is invoked
- **THEN** `extraArgs[0]` SHALL be a filesystem path to a strategy.md file with valid YAML frontmatter
- **AND** the strategy SHALL have `api.base_url` defined

#### Scenario: Required parameter — targetUrl

- **WHEN** `runMediawikiApiFetch` is invoked
- **THEN** `targetUrl` SHALL be a fully-formed HTTP/HTTPS URL
- **AND** the URL SHALL contain a `/wiki/` path segment from which the page title is extracted

#### Scenario: Page title extraction

- **WHEN** the target URL is `https://example.com/wiki/The_Sad_Onion`
- **THEN** the extracted page title SHALL be `"The Sad Onion"`
- **AND** underscores in the URL path SHALL be decoded to spaces

### Requirement: Output contract — HTML file

The mediawiki-api engine SHALL output a single HTML file containing the parsed page content.

#### Scenario: Successful fetch

- **WHEN** the MediaWiki `action=parse` API returns a valid response
- **THEN** a file SHALL be written to `outputPath` containing the HTML from `data.parse.text["*"]`
- **AND** the function SHALL return `{ ok: true, stdout, command, page_title }`

### Requirement: Error contract

The mediawiki-api engine SHALL handle the following error cases and return a structured error response.

#### Scenario: Missing strategy path

- **WHEN** `extraArgs[0]` is absent or undefined
- **THEN** the function SHALL return `{ ok: false, summary, stderr: "Missing strategy path." }`

#### Scenario: Missing api.base_url

- **WHEN** the strategy frontmatter has no `api.base_url`
- **THEN** the function SHALL return `{ ok: false, summary, stderr: "Missing api.base_url in strategy." }`

#### Scenario: API request failure

- **WHEN** the `curl` request fails (non-zero exit code)
- **THEN** the function SHALL return `{ ok: false, summary, stderr }`

#### Scenario: Invalid API response

- **WHEN** the API response is not valid JSON
- **THEN** the function SHALL return `{ ok: false, summary }`

#### Scenario: API error response

- **WHEN** the API response contains `data.error`
- **THEN** the function SHALL return `{ ok: false, summary }` with the error info

### Requirement: URL construction — api.base_url handling

The engine SHALL handle `api.base_url` values both with and without `/api.php` suffix.

#### Scenario: base_url ends with /api.php

- **WHEN** `api.base_url` ends with `/api.php` (e.g., `https://bindingofisaacrebirth.wiki.gg/api.php`)
- **THEN** the constructed API URL SHALL use it directly: `{base_url}?action=parse&page=...`
- **AND** no additional `/api.php` SHALL be appended

#### Scenario: base_url without /api.php suffix

- **WHEN** `api.base_url` does not end with `/api.php`
- **THEN** the engine SHALL append `/api.php`: `{base_url}/api.php?action=parse&page=...`

---

## Pipeline Requirements

### Requirement: 管线触发条件

The system SHALL trigger the MediaWiki API extraction pipeline when a `crawl` command targets a domain whose site strategy contains a valid `api` field with `api.platform` equal to `mediawiki`.

The pipeline SHALL NOT be triggered for:
- `fetch` commands (single-page Scrapling remains the default)
- `scrape` commands (strategy-free recursive crawling)
- Strategies without an `api` field

#### Scenario: API pipeline triggered by crawl with strategy

- **WHEN** `chrome-agent crawl https://balatrowiki.org/w/Jokers` is invoked and the matching strategy has `api.platform: mediawiki`
- **THEN** the system SHALL route to the MediaWiki API extraction pipeline
- **AND** the result SHALL identify `extraction_method: mediawiki_api`

#### Scenario: API pipeline not triggered for fetch

- **WHEN** `chrome-agent fetch https://balatrowiki.org/w/Joker` is invoked
- **THEN** the system SHALL NOT route to the API pipeline
- **AND** the system SHALL use the standard Scrapling engine path

#### Scenario: API pipeline not triggered without strategy api field

- **WHEN** `chrome-agent crawl <url>` is invoked but the matching strategy has no `api` field
- **THEN** the system SHALL NOT route to the API pipeline
- **AND** the system SHALL fall through to the standard Scrapling crawl pipeline

### Requirement: API 端点探测

The system SHALL probe the MediaWiki API endpoint before executing the extraction pipeline.

The system SHALL attempt the following paths in order:
1. `{strategy.api.base_url}` (if specified in strategy)
2. `{origin}/api.php`
3. `{origin}/w/api.php`

Probing SHALL use `action=query&meta=siteinfo&format=json` with a 5-second timeout.

#### Scenario: Probe succeeds on first attempt

- **WHEN** probing `https://balatrowiki.org/api.php?action=query&meta=siteinfo&format=json` returns HTTP 200 with valid JSON
- **THEN** the system SHALL use `https://balatrowiki.org/api.php` as the API base for all subsequent requests
- **AND** the system SHALL log the resolved endpoint

#### Scenario: Probe fails on all candidates

- **WHEN** all probe candidates return non-200 or non-JSON responses
- **THEN** the system SHALL log the failure with resolution "api_unreachable"
- **AND** the system SHALL fall back to the Scrapling crawl pipeline
- **AND** the fallback SHALL be explicitly recorded in the crawl report

#### Scenario: Rate limit during probe

- **WHEN** any probe candidate returns HTTP 429
- **THEN** the system SHALL retry after 2 seconds, up to 2 retries
- **AND** if all retries fail, SHALL treat as probe failure and fall back to Scrapling

### Requirement: Phase A — 页面发现

The system SHALL discover the full page inventory and category taxonomy through the MediaWiki API.

Page discovery SHALL use `action=query&list=allpages&apnamespace=0&apfilterredir=nonredirects&aplimit=500` with pagination via `continue.apcontinue`.

Category discovery SHALL use `action=query&prop=categories&cllimit=max` in batches of 50 page titles per request.

#### Scenario: Full page inventory discovery

- **WHEN** Phase A executes against balatrowiki.org
- **THEN** all non-redirect main-namespace pages SHALL be collected (expected ~467 pages)
- **AND** each page SHALL be recorded with its page title, page ID, and namespace
- **AND** the page inventory SHALL be saved as `page_manifest.json` in the crawl run directory

#### Scenario: Category taxonomy discovery

- **WHEN** Phase A collects categories for all discovered pages
- **THEN** each page SHALL be associated with its MediaWiki category memberships
- **AND** categories matching `strategy.api.taxonomy.category_filters` (if specified) SHALL be excluded
- **AND** the category-to-page mapping SHALL be added to `page_manifest.json`

#### Scenario: List page content capture

- **WHEN** Phase A encounters pages listed in `strategy.api.taxonomy.list_pages`
- **THEN** the system SHALL fetch their wikitext via `action=parse&prop=wikitext`
- **AND** the captured content SHALL be reserved for Phase C index.md generation
- **AND** non-list pages SHALL be deferred to Phase B for full extraction

### Requirement: Rate Limit 配置解析

The system SHALL resolve the final rate limit configuration for the MediaWiki API pipeline using a four-layer override priority before executing Phase B.

The four layers, from highest to lowest priority, SHALL be:
1. **CLI arguments**: `--concurrency`, `--batch-delay-ms`, `--max-retries`, `--backoff-multiplier`, `--jitter`
2. **Site Strategy local overrides**: `api.rate_limit.{concurrency, batch_delay_ms, retry.*}`
3. **Anti-Crawl tier template**: The `rate_limit_tiers` tier referenced by `api.rate_limit.tier` from the matching anti-crawl strategy
4. **Code safe defaults**: `concurrency=1`, `batch_delay_ms=1000`, `retry.max_retries=5`, `retry.initial_delay_sec=1.0`, `retry.backoff_multiplier=2.0`, `retry.max_delay_sec=60.0`, `retry.jitter=true`

#### Scenario: 配置解析在 pipeline 启动时完成

- **WHEN** the pipeline starts with a valid site strategy and optional CLI arguments
- **THEN** the system SHALL resolve the final rate limit configuration before Phase A execution
- **AND** the resolved configuration SHALL be logged at INFO level
- **AND** the same configuration object SHALL be passed to both `ApiClient` and `run_phase_b`

#### Scenario: 无策略配置时使用安全默认值

- **WHEN** the pipeline runs against a site strategy with no `api.rate_limit` field and no CLI overrides
- **THEN** the system SHALL use code safe defaults for all rate limit parameters
- **AND** Phase B SHALL execute with `concurrency=1` and `batch_delay_ms=1000`

### Requirement: Phase B — 内容提取

The system SHALL extract content from each discovered page using the MediaWiki parse API.

For each page, the system SHALL:
1. Fetch wikitext via `action=parse&page={title}&prop=wikitext&format=json`
2. Extract infobox template parameters for YAML frontmatter
3. Convert wiki links to Markdown relative paths
4. Expand template calls to inline Markdown
5. Convert image references to absolute URL inline Markdown

Phase B SHALL support concurrent execution with **configurable concurrency** (resolved via the four-layer priority; safe default: 1).

#### Scenario: Wikitext fetch

- **WHEN** Phase B fetches wikitext for page "Joker"
- **THEN** the API response SHALL contain template-expanded wikitext in `parse.wikitext.*`
- **AND** the wikitext SHALL be no larger than 100KB per page
- **AND** failed fetches SHALL be retried with exponential backoff using the resolved retry parameters

#### Scenario: Infobox frontmatter extraction

- **WHEN** wikitext contains a template call matching `strategy.api.output.frontmatter_fields` entries
- **THEN** the system SHALL extract parameter key-value pairs from the template
- **AND** extracted values SHALL be written as YAML frontmatter fields in the output Markdown
- **AND** the `source_url` field SHALL always be present, set to the page's canonical URL

#### Scenario: Wiki link to Markdown conversion

- **WHEN** wikitext contains `[[Page Title|display text]]`
- **THEN** the system SHALL convert it to `[display text](Page_Title.md)`
- **AND** if the target page's directory differs from the source page's directory (per Phase A manifest), the link SHALL include the cross-directory relative path
- **AND** links to non-content namespaces (`File:`, `Category:`, `Template:`, `Special:`) SHALL be excluded

#### Scenario: Template expansion to inline Markdown

- **WHEN** wikitext contains template calls like `{{Mult|+4}}` or `{{Chips|+5}}`
- **THEN** the system SHALL convert them to inline Markdown bold: `**+4 Mult**` or `**+5 Chips**`
- **AND** unrecognized template calls SHALL be logged as warnings and preserved as `{{...}}` text
- **AND** the list of expandable templates SHALL be configurable via `strategy.api.output.template_map`

#### Scenario: Image reference conversion

- **WHEN** wikitext contains `[[File:Joker.png|thumb|alt text]]`
- **THEN** the system SHALL convert it to `![alt text](https://{domain}/images/Joker.png)`
- **AND** the image URL SHALL use the site's canonical image path (derived from API base URL)
- **AND** thumbnail size parameters SHALL be stripped from the output URL

#### Scenario: Partial failure during extraction

- **WHEN** some pages fail to fetch after all retries
- **THEN** the system SHALL continue processing remaining pages
- **AND** failed pages SHALL be recorded with their error reason in the crawl manifest
- **AND** the final result SHALL be `partial_success` if any pages succeeded

### Requirement: Concurrency and rate limiting

The system SHALL control concurrent API requests and inter-batch delays using the resolved rate limit configuration.

The Phase B executor SHALL:
1. Create a `ThreadPoolExecutor` with `max_workers` equal to the resolved `concurrency`
2. Submit page processing futures to the executor
3. After each completion checkpoint (or after each batch of completions), sleep for `batch_delay_ms / 1000.0` seconds before continuing
4. Ensure that the batch delay is applied regardless of whether the completed requests succeeded or failed

#### Scenario: 批次延迟在成功和失败后都生效

- **WHEN** a batch of 5 requests completes with 3 successes and 2 failures
- **THEN** the system SHALL wait for the resolved `batch_delay_ms` before processing the next batch
- **AND** the wait SHALL NOT be skipped because some requests failed

#### Scenario: 429 退避使用配置参数

- **WHEN** an API request returns HTTP 429
- **AND** the resolved retry configuration is `max_retries=5`, `initial_delay_sec=1.0`, `backoff_multiplier=2.5`, `max_delay_sec=60.0`, `jitter=true`
- **THEN** the first retry SHALL wait approximately 1.0s (±20% jitter)
- **AND** the second retry SHALL wait approximately 2.5s (±20% jitter)
- **AND** the third retry SHALL wait approximately 6.25s (±20% jitter)
- **AND** delays SHALL cap at 60.0s regardless of further multiplications

### Requirement: Phase C — 输出组装

The system SHALL assemble extracted content into a structured directory tree with correct internal links.

Phase C SHALL:
1. Organize pages into directories based on category mapping from Phase A
2. Correct cross-directory internal links using the full page manifest
3. Generate `index.md` for each directory with list page content and file inventory
4. Generate `_index.md` as the top-level directory index
5. Output frontmatter-enriched Markdown files with consistent formatting

#### Scenario: Directory organization by category

- **WHEN** Phase C organizes pages per `strategy.api.taxonomy.list_pages` and category mapping
- **THEN** pages SHALL be placed in directories based on category mapping from Phase A
- **AND** pages without a matching category SHALL be placed in `Misc/` directory
- **AND** the Misc ratio SHALL be reported (target: < 5% of total pages)

#### Scenario: Cross-directory link correction

- **WHEN** a page in `Jokers/Joker.md` contains `[Tarot Cards](Tarot_Cards.md)`
- **THEN** the system SHALL detect that `Tarot_Cards.md` resolves to the correct cross-directory path
- **AND** the link SHALL be rewritten with the appropriate relative path
- **AND** same-directory links SHALL remain unchanged

#### Scenario: Index.md generation

- **WHEN** a directory has a corresponding list page (per `strategy.api.taxonomy.list_pages`)
- **THEN** the list page's converted content SHALL be used as the `index.md` body
- **AND** a YAML frontmatter SHALL be prepended with `title`, `source_url`, and `category` fields
- **AND** a "Pages in this category" section SHALL be appended with a file listing

#### Scenario: _index.md top-level generation

- **WHEN** Phase C completes all directory organization
- **THEN** a top-level `_index.md` SHALL be generated
- **AND** it SHALL contain a crawl date, total page count, and table of contents linking to each directory's `index.md`

### Requirement: Fallback 到 Scrapling

The system SHALL fall back to the Scrapling crawl pipeline when the API pipeline fails at any phase.

Fallback SHALL be triggered by:
- API endpoint probe failure (all candidates unreachable)
- Phase A failure (unable to discover pages or categories)
- Phase B failure rate exceeding 50% (more than half of pages fail to extract)
- Strategy `api` field missing or invalid

#### Scenario: API probe failure triggers fallback

- **WHEN** the API endpoint probe fails for all candidate URLs
- **THEN** the system SHALL log "api_unreachable, falling back to scrapling"
- **AND** the system SHALL execute the standard Scrapling crawl pipeline
- **AND** the fallback SHALL be recorded in the crawl report with the probe error details

#### Scenario: Partial success with fallback

- **WHEN** Phase B succeeds for some pages but fails for others at a rate below 50%
- **THEN** the system SHALL NOT trigger full fallback
- **AND** failed pages SHALL be recorded as extraction failures
- **AND** the result SHALL be `partial_success`

### Requirement: 输出格式契约

The system SHALL produce output Markdown files that are semantically equivalent to Scrapling crawl output in structure, enabling interchangeable consumption.

Each output `.md` file SHALL contain:
- YAML frontmatter with at minimum `title`, `source_url`
- Body content as standard Markdown
- Inline images using absolute URLs in `![](url)` format
- Internal links as relative paths in `[text](path.md)` format
- No wikitext artifacts, no HTML, no navigation noise

#### Scenario: Output equivalence with Scrapling crawl

- **WHEN** both API and Scrapling pipelines produce output for the same MediaWiki site
- **THEN** the `.md` files from both paths SHALL be consumable by the same downstream tools
- **AND** the API output SHALL contain frontmatter fields that Scrapling output may lack
- **AND** both outputs SHALL use the same image reference format (absolute URL inline)

#### Scenario: No wikitext artifacts in output

- **WHEN** Phase B converts wikitext to Markdown
- **THEN** the output SHALL NOT contain `{{...}}` template calls (except for unrecognized templates per warning log)
- **AND** the output SHALL NOT contain `[[Category:...]]` lines
- **AND** the output SHALL NOT contain `[[File:...]]` wiki syntax
- **AND** the output SHALL NOT contain HTML entity references (converted to plain text)
- **AND** the output SHALL NOT contain `<dpl>...</dpl>` blocks
- **AND** the output SHALL NOT contain `<!-- ... -->` HTML comments

### Requirement: DPL 表格还原

The system SHALL replace `<dpl>...</dpl>` blocks in list pages with data-driven Markdown tables assembled from Phase B frontmatter extraction results.

The system SHALL:
1. Detect `<dpl>...</dpl>` blocks in list page wikitext
2. Determine which pages belong to the list page's category (from Phase A manifest)
3. Collect frontmatter fields from each page's Phase B extraction result
4. Assemble a Markdown table with columns corresponding to `output.frontmatter_fields`
5. Include page title as a linked column pointing to the page's Markdown file

#### Scenario: DPL replacement with summary table

- **WHEN** Phase C processes an index.md and the list page wikitext contains a `<dpl>` block
- **THEN** the system SHALL replace the `<dpl>...</dpl>` block with a Markdown table
- **AND** the table SHALL have columns derived from `output.frontmatter_fields`
- **AND** the first column SHALL be the page title linked to the page's Markdown file
- **AND** each row SHALL be populated from the corresponding page's frontmatter data extracted in Phase B

#### Scenario: HTML comment removal

- **WHEN** Phase B processes any page's wikitext
- **THEN** the system SHALL strip all `<!-- ... -->` HTML comment blocks
- **AND** the resulting Markdown SHALL NOT contain any HTML comment syntax

---

## Strategy Interface Requirements

### Requirement: Capabilities 受控词汇表

The system SHALL define a controlled vocabulary for MediaWiki API capabilities, enabling strategy-driven validation instead of hardcoded capability checks.

| Capability ID | Type | Description |
|--------------|------|-------------|
| `page_list` | `required` | Ability to enumerate pages via `action=query&list=allpages` or similar |
| `category_lookup` | `required` | Ability to query category memberships per page via `action=query&prop=categories` |
| `wikitext_parse` | `required` | Ability to fetch wikitext content via `action=parse&prop=wikitext` |
| `html_parse` | `optional` | Ability to fetch rendered HTML via `action=parse&prop=text` |
| `imageinfo_query` | `optional` | Ability to query image metadata via `action=query&prop=imageinfo` |
| `redirect_resolve` | `optional` | Ability to resolve redirects via `action=query&prop=redirects` |

The system SHALL validate that the strategy's declared `api.capabilities` superset covers the union of `required_capabilities` from all chosen strategies.

#### Scenario: Validation passes with complete strategy capabilities

- **WHEN** the strategy declares `capabilities: [page_list, category_lookup, wikitext_parse]`
- **AND** the selected strategies require the union of those capabilities
- **THEN** validation SHALL pass

#### Scenario: Validation fails with missing capability

- **WHEN** the strategy declares capabilities that do not cover the union of required capabilities
- **THEN** validation SHALL fail with a message indicating the missing capability

### Requirement: 策略接口契约

The system SHALL define five strategy interfaces as Python `Protocol` classes:

1. **DiscoveryStrategy**: Page and category discovery, page classification
2. **ContentAcquisitionStrategy**: Content source fetching (wikitext, rendered HTML, images)
3. **LinkResolver**: Wiki link to Markdown relative path resolution
4. **TemplateProcessor**: Frontmatter extraction, template expansion, cleanup
5. **ListPageAssembler**: Index page assembly (DPL table replacement, directory index)

Each strategy interface SHALL declare a `required_capabilities` property returning a set of capability IDs.

#### Scenario: DiscoveryStrategy interface

- **WHEN** a DiscoveryStrategy implementation is used in the pipeline
- **THEN** it SHALL expose: `discover_pages`, `discover_categories`, `classify_page`, `fetch_list_pages`, `required_capabilities`

#### Scenario: ContentAcquisitionStrategy interface

- **WHEN** a ContentAcquisitionStrategy implementation is used
- **THEN** it SHALL expose: `fetch_page_content`, `required_capabilities`

#### Scenario: LinkResolver interface

- **WHEN** a LinkResolver implementation is used
- **THEN** it SHALL expose: `convert_links`, `resolve`

#### Scenario: TemplateProcessor interface

- **WHEN** a TemplateProcessor implementation is used
- **THEN** it SHALL expose: `extract_frontmatter`, `expand_templates`, `remove_infobox`, `clean_remaining_templates`

#### Scenario: ListPageAssembler interface

- **WHEN** a ListPageAssembler implementation is used
- **THEN** it SHALL expose: `assemble_index`

### Requirement: Pipeline 策略注入

The system SHALL support strategy injection at pipeline composition time via a `build_pipeline` function or equivalent mechanism.

The pipeline SHALL accept a `PipelineStrategies` container holding one instance of each strategy interface.

The `content_profile` field in `strategy.api` SHALL allow declarative strategy selection. When absent, all default strategies SHALL be used.

#### Scenario: Default strategy composition

- **WHEN** `strategy.api.content_profile` is absent from the strategy file
- **THEN** the pipeline SHALL compose all default implementations:
  - `discovery_strategy: "allpages"` → `AllPagesDiscoveryStrategy`
  - `content_acquisition: "wikitext_only"` → `WikitextOnlyAcquisitionStrategy`
  - `link_resolver: "exact_title_match"` → `ExactTitleLinkResolver`
  - `template_processor: "simple_substitution"` → `SimpleSubstitutionTemplateProcessor`
  - `list_page_assembler: "frontmatter_driven"` → `FrontmatterDrivenListPageAssembler`

### Requirement: Namespace 策略化

The system SHALL read the namespace parameter from `strategy.api.namespace` for page discovery. When not specified, namespace SHALL default to `0` (main namespace).

#### Scenario: Namespace from strategy

- **WHEN** a strategy specifies `api.namespace: 3000`
- **THEN** `discover_all_pages` SHALL use `apnamespace=3000`

#### Scenario: Namespace default

- **WHEN** a strategy does NOT specify `api.namespace`
- **THEN** `discover_all_pages` SHALL use `apnamespace=0`

### Requirement: 管线核心流程与策略挂载点

The system SHALL maintain a stable three-phase pipeline structure with clearly defined strategy mount points:

```
Phase A (Page Discovery)  ─── 委托 → DiscoveryStrategy
     │
     ▼
Phase B (Content Extraction)  ─── 委托 → ContentAcquisitionStrategy
     │                                    ┌─ LinkResolver
     │                                    ├─ TemplateProcessor
     │                                    └─ (utility: table converter, formatting)
     ▼
Phase C (Output Assembly)  ─── 委托 → ListPageAssembler
                                    (复用 LinkResolver)
```

Each phase SHALL accept its delegated strategy interface(s) as parameters. Strategy objects SHALL be stateless.

---

## Site Strategy Schema

### Requirement: content_profile 字段定义

The system SHALL recognize an `api.content_profile` field in the strategy frontmatter that allows declarative strategy selection.

The `content_profile` field is OPTIONAL. When absent, the pipeline SHALL use all default strategy implementations.

The `content_profile` schema:

```yaml
api:
  content_profile:
    discovery_strategy: "<strategy-id>"      # OPTIONAL, default: "allpages"
    content_acquisition: "<strategy-id>"     # OPTIONAL, default: "wikitext_only"
    link_resolver: "<strategy-id>"           # OPTIONAL, default: "exact_title_match"
    template_processor: "<strategy-id>"      # OPTIONAL, default: "simple_substitution"
    list_page_assembler: "<strategy-id>"     # OPTIONAL, default: "frontmatter_driven"
```

#### Scenario: content_profile absent, defaults used

- **WHEN** the strategy file has no `api.content_profile` field
- **THEN** the pipeline SHALL compose all default strategy implementations

#### Scenario: content_profile partially specified

- **WHEN** `api.content_profile` specifies only one dimension
- **THEN** the specified dimension SHALL use the indicated implementation
- **AND** all unspecified concerns SHALL use their default implementations

### Requirement: api-homepage-config-block

The system SHALL recognize an optional `api.homepage` configuration block in the strategy YAML frontmatter for homepage-driven crawl entry points.

The `api.homepage` block SHALL contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_title` | string | yes | The actual wiki page title of the homepage |
| `category_sections` | object[] | yes | CSS selectors to extract category links from homepage HTML |
| `categories` | object[] | yes | List of categories with name-to-directory mapping |
| `category_page_types` | object | no | Map of category name to page type. Default: `list_page` |
| `assignment_priority` | string[] | yes | Ordered list of category names for multi-category page assignment priority |
| `manual_assignments` | object | no | Map of page title to output directory for manual override |

#### Scenario: valid-homepage-config

- **WHEN** a strategy file defines `api.homepage` with all required fields
- **THEN** the strategy SHALL be accepted for `--phase homepage` pipeline execution

#### Scenario: missing-homepage-config

- **WHEN** a strategy file does NOT define `api.homepage`
- **THEN** the strategy SHALL remain valid for all other pipeline phases
- **THEN** `--phase homepage` SHALL NOT be available for this strategy

#### Scenario: category-page-type-distinction

- **WHEN** `category_page_types` maps a category to `"category_page"`
- **THEN** discovery for that category SHALL use `categorymembers` API
- **THEN** categories NOT listed SHALL default to `list_page` (using `prop=links`)

### Requirement: structure-category-page-type

The system SHALL accept `category` as a valid value for `structure.pages[].type` in site strategy files.

A page with `type: category` SHALL:
- Have `content_type: wiki_category`
- Default discovery strategy SHALL be `categorymembers` (via ns=14 Category namespace)

---

## Extraction Patterns

### Requirement: 噪音分类学

The system SHALL define a taxonomy of MediaWiki content extraction noise organized into four clusters: navigation, template, link, and table.

#### Scenario: Navigation 噪音

- **WHEN** extracting content from a MediaWiki page
- **THEN** the following elements SHALL be identified as navigation noise:
  - Footer sections (Tools, Privacy, About, Disclaimers)
  - Section edit links (`[edit]`, `[edit source]`)
  - Skip links (`Jump to navigation`, `Jump to search`)
  - "Navigation menu" heading

#### Scenario: Template 噪音

- **WHEN** extracting content from a MediaWiki page
- **THEN** the following elements SHALL be identified as template noise:
  - DPL wikitext artifacts exposed from `metadata-dpl` spans
  - Scribunto JSON data rows
  - Empty parentheses `()` from empty template data
  - Inline `<style>` blocks with `data-mw-deduplicate` attributes

#### Scenario: Link 噪音

- **WHEN** extracting content from a MediaWiki page
- **THEN** the following elements SHALL be identified as link noise:
  - Nested image links: `[![](thumb)](page)` pattern
  - Internal link title residue: `"title")` trailing artifacts
  - Category links: `[[Category:...]]` lines

#### Scenario: Table 噪音

- **WHEN** extracting content from a MediaWiki page
- **THEN** the following elements SHALL be identified as table noise:
  - Infobox tables with many empty columns (detect: `len(cells) > 5 && non_empty <= 2`)
  - Missing Markdown table separator rows after headers

### Requirement: 通用模式文档

The system SHALL create `docs/patterns/mediawiki-extraction.md` as a reusable reference for all MediaWiki scraping tasks.

#### Scenario: 文档结构

- **WHEN** the pattern document is created
- **THEN** it SHALL contain the following sections:
  1. **Platform Taxonomy** — Weird Gloop vs self-hosted, version considerations
  2. **Noise Taxonomy** — the four clusters with known variants per site
  3. **Cleanup Pipeline** — rule ordering rationale and cluster execution flow
  4. **Cross-site Reuse** — checklist for adapting patterns to new MediaWiki sites

#### Scenario: 跨站点复用指南

- **WHEN** a new MediaWiki site is encountered
- **THEN** the operator SHALL be able to use the cross-site reuse checklist to:
  1. Verify the site is MediaWiki (generator meta, DOM structure)
  2. Run `scrapling-get` to assess protection level
  3. Compare Scrapling output against the noise taxonomy
  4. Select the appropriate site profile for cleanup
  5. Identify any site-specific noise not covered by existing clusters
