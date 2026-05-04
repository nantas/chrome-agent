# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrape-command`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认新增策略无关的递归爬取命令，支持自发现式链接遍历，默认输出 Markdown

## 规范真源声明

- 本文件是 `scrape-command` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Scrape command surface

The system SHALL expose `scrape` as a first-class command in the `chrome-agent` CLI surface.

#### Scenario: Command inventory

- **WHEN** an operator invokes `chrome-agent --help`
- **THEN** the CLI SHALL present `scrape` alongside `explore`, `fetch`, `crawl`, `doctor`, and `clean`
- **AND** it SHALL describe `scrape` as a strategy-free recursive crawling workflow

### Requirement: No strategy dependency

The `scrape` command SHALL NOT require a matching `site-strategy` to execute.

#### Scenario: Scrape without strategy

- **WHEN** `scrape <url>` is invoked and no matching `site-strategy` exists
- **THEN** the command SHALL proceed using self-discovered link following
- **AND** it SHALL NOT refuse execution or instruct the caller to run `explore` first

#### Scenario: Scrape with strategy present

- **WHEN** `scrape <url>` is invoked and a matching `site-strategy` exists
- **THEN** the command SHALL ignore the strategy and proceed with self-discovered link following
- **AND** it SHALL NOT read or apply any strategy-declared selectors, pagination, or entry points

### Requirement: Self-discovered link traversal

The `scrape` command SHALL discover next-page URLs by extracting all anchor links from fetched HTML and filtering them.

#### Scenario: Same-domain filtering

- **WHEN** `scrape <url>` runs with the default `--same-domain` behavior (on by default)
- **THEN** it SHALL only follow links whose hostname matches the initial target URL's hostname
- **AND** it SHALL skip cross-domain links without treating them as failures

#### Scenario: URL pattern matching

- **WHEN** the caller supplies `--match <glob>`
- **THEN** the command SHALL only follow links whose pathname matches the supplied glob pattern
- **AND** it SHALL skip non-matching links without treating them as failures

#### Scenario: Dedup and cycle prevention

- **WHEN** a discovered URL has already been visited or is already queued
- **THEN** the command SHALL skip it and continue
- **AND** it SHALL not revisit the same URL within the same scrape run

### Requirement: Bounded traversal

The `scrape` command SHALL be bounded by an explicit `--max-pages` limit.

#### Scenario: Default page limit

- **WHEN** `scrape <url>` is invoked without `--max-pages`
- **THEN** the default limit SHALL be 10 pages

#### Scenario: Custom page limit

- **WHEN** `scrape <url> --max-pages 500` is invoked
- **THEN** the command SHALL traverse up to 500 pages
- **AND** it SHALL stop when the limit is reached, regardless of remaining queued URLs

### Requirement: Default Markdown output

The `scrape` command SHALL default to producing Markdown output for each crawled page.

#### Scenario: Default Markdown mode

- **WHEN** `scrape <url>` is invoked without `--no-markdown`
- **THEN** the command SHALL execute Phase 2 Markdown conversion after traversal completes
- **AND** each successfully visited page SHALL produce a `.md` file

#### Scenario: HTML-only mode

- **WHEN** `scrape <url> --no-markdown` is invoked
- **THEN** the command SHALL skip Phase 2 Markdown conversion
- **AND** it SHALL retain intermediate `.html` files as the final output

### Requirement: Structured directory output

The `scrape` command SHALL organize per-page `.md` files in a directory structure reflecting the URL pathname hierarchy.

#### Scenario: Subdirectory organization

- **WHEN** `scrape <url>` produces Markdown for pages with pathnames like `/wiki/Weapons` and `/docs/Guide`
- **THEN** the output files SHALL be placed at `<runDir>/wiki/Weapons.md` and `<runDir>/docs/Guide.md`
- **AND** page-to-page links within the Markdown SHALL be rewritten as relative paths

#### Scenario: Link preservation

- **WHEN** a page contains a link to another visited page
- **THEN** the link SHALL be converted from an absolute URL to a relative file path
- **AND** external links SHALL remain unchanged

### Requirement: Optional merged output

The `scrape` command SHALL support merging all per-page Markdown files into a single document.

#### Scenario: Merge flag

- **WHEN** `scrape <url> --markdown --merge` is invoked
- **THEN** after Phase 2 conversion completes, the command SHALL concatenate all `.md` files into `scrape-output.md`
- **AND** the merged document SHALL include a table of contents derived from each page's first `#` heading
- **AND** per-page `.md` files SHALL remain alongside the merged file

### Requirement: Concurrent Markdown conversion

The `scrape` command SHALL support concurrent Phase 2 Markdown conversion.

#### Scenario: Default concurrency

- **WHEN** Phase 2 conversion runs without an explicit `--concurrency` value
- **THEN** the default concurrency SHALL be 5 concurrent Scrapling invocations

#### Scenario: Custom concurrency

- **WHEN** `scrape <url> --concurrency 10` is invoked
- **THEN** Phase 2 conversion SHALL run with up to 10 concurrent Scrapling invocations

### Requirement: Fetcher override

The `scrape` command SHALL allow the caller to override the default Scrapling fetcher.

#### Scenario: Default fetcher

- **WHEN** `scrape <url>` runs without `--fetcher`
- **THEN** it SHALL use `scrapling-get` as the default fetcher for all pages

#### Scenario: Explicit fetcher override

- **WHEN** `scrape <url> --fetcher stealthy-fetch` is invoked
- **THEN** it SHALL use the specified fetcher for both Phase 1 traversal and Phase 2 conversion

### Requirement: Partial failure semantics

The `scrape` command SHALL support partial completion when some pages succeed and others fail.

#### Scenario: Phase 1 partial failure

- **WHEN** some pages fail to fetch during traversal but others succeed
- **THEN** the command SHALL continue processing queued pages
- **AND** the final result SHALL be `partial_success`

#### Scenario: Phase 2 partial failure

- **WHEN** some Markdown conversions fail but others succeed
- **THEN** the failure of a single conversion SHALL NOT block other conversions
- **AND** the failed URLs SHALL be recorded in the manifest
- **AND** the final result SHALL be `partial_success` if any conversions succeeded

### Requirement: HTML intermediate cleanup

The `scrape` command SHALL treat Phase 1 `.html` files as intermediate artifacts and clean them up after Phase 2 completes.

#### Scenario: Default cleanup

- **WHEN** `scrape <url> --markdown` completes successfully
- **THEN** all intermediate `.html` files SHALL be removed from the run directory
- **AND** only `.md` files (and the manifest/report) SHALL remain

#### Scenario: Keep HTML

- **WHEN** `scrape <url> --markdown --keep-html` is invoked
- **THEN** intermediate `.html` files SHALL be retained alongside `.md` files
- **AND** they SHALL be labeled as `disposable` artifacts in the result
