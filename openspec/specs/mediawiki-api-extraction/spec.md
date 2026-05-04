# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认基于 balatro 爬取经验报告和实际数据对比（Scrapling MD 54KB vs API Wikitext 5KB），为 MediaWiki 游戏 wiki 建立 API-first 的结构化提取管线

## 规范真源声明

- 本文件是 `mediawiki-api-extraction` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

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

### Requirement: Phase B — 内容提取

The system SHALL extract content from each discovered page using the MediaWiki parse API.

For each page, the system SHALL:
1. Fetch wikitext via `action=parse&page={title}&prop=wikitext&format=json`
2. Extract infobox template parameters for YAML frontmatter
3. Convert wiki links to Markdown relative paths
4. Expand template calls to inline Markdown
5. Convert image references to absolute URL inline Markdown

Phase B SHALL support concurrent execution with configurable concurrency (default: 5).

#### Scenario: Wikitext fetch

- **WHEN** Phase B fetches wikitext for page "Joker"
- **THEN** the API response SHALL contain template-expanded wikitext in `parse.wikitext.*`
- **AND** the wikitext SHALL be no larger than 100KB per page
- **AND** failed fetches SHALL be retried with exponential backoff (1s, 2s, 4s, max 3 retries)

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

#### Scenario: Concurrency and rate limiting

- **WHEN** Phase B executes with concurrency 5
- **THEN** at most 5 API requests SHALL be in-flight simultaneously
- **AND** a 200ms delay SHALL be inserted between request batches to avoid triggering rate limits
- **AND** HTTP 429 responses SHALL trigger exponential backoff with jitter

#### Scenario: Partial failure during extraction

- **WHEN** some pages fail to fetch after all retries
- **THEN** the system SHALL continue processing remaining pages
- **AND** failed pages SHALL be recorded with their error reason in the crawl manifest
- **AND** the final result SHALL be `partial_success` if any pages succeeded

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
- **THEN** Joker pages SHALL be placed in `Jokers/` directory
- **AND** Tarot Card pages SHALL be placed in `Consumables/Tarot_Cards/` directory
- **AND** pages without a matching category SHALL be placed in `Misc/` directory
- **AND** the Misc ratio SHALL be reported (target: < 5% of total pages)

#### Scenario: Cross-directory link correction

- **WHEN** a page in `Jokers/Joker.md` contains `[Tarot Cards](Tarot_Cards.md)`
- **THEN** the system SHALL detect that `Tarot_Cards.md` resolves to `Consumables/Tarot_Cards/index.md`
- **AND** the link SHALL be rewritten to `[Tarot Cards](../Consumables/Tarot_Cards/index.md)`
- **AND** same-directory links SHALL remain unchanged (e.g., `[Another Joker](Another_Joker.md)` stays as-is)

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
- **AND** the output SHALL NOT contain `<dpl>...</dpl>` blocks (DPL blocks SHALL be replaced by data-driven Markdown tables per Phase C)
- **AND** the output SHALL NOT contain `<!-- ... -->` HTML comments

### Requirement: DPL 表格还原

The system SHALL replace `<dpl>...</dpl>` blocks in list pages with data-driven Markdown tables assembled from Phase B frontmatter extraction results.

Rather than parsing DPL syntax, the system SHALL derive the table structure from the strategy's `output.frontmatter_fields` and the category membership already collected in Phase A. The system SHALL:

1. Detect `<dpl>...</dpl>` blocks in list page wikitext
2. Determine which pages belong to the list page's category (from Phase A manifest)
3. Collect frontmatter fields from each page's Phase B extraction result
4. Assemble a Markdown table with columns corresponding to `output.frontmatter_fields`
5. Include page title as a linked column pointing to the page's Markdown file

#### Scenario: DPL replacement with summary table

- **WHEN** Phase C processes `Jokers/index.md` and the Jokers list page wikitext contains a `<dpl>` block
- **THEN** the system SHALL replace the `<dpl>...</dpl>` block with a Markdown table
- **AND** the table SHALL have columns derived from `output.frontmatter_fields` (e.g., effect, rarity, type, buyprice)
- **AND** the first column SHALL be the page title linked to the page's Markdown file
- **AND** each row SHALL be populated from the corresponding page's frontmatter data extracted in Phase B
- **AND** pages without matching frontmatter data SHALL be listed with a link-only row

#### Scenario: HTML comment removal

- **WHEN** Phase B processes any page's wikitext
- **THEN** the system SHALL strip all `<!-- ... -->` HTML comment blocks
- **AND** the resulting Markdown SHALL NOT contain any HTML comment syntax
