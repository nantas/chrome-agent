# Specification Delta

## Capability 对齐（已确认）

- Capability: `markdown-conversion-pipeline`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认新增共享的 Markdown 转换管线，供 crawl 和 scrape 复用

## 规范真源声明

- 本文件是 `markdown-conversion-pipeline` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Shared conversion interface

The system SHALL provide a reusable `convertTraversalToMarkdown` function (or equivalent) that can be invoked by both `crawl` and `scrape` workflows.

#### Scenario: Unified input contract

- **WHEN** Phase 1 traversal completes and produces a manifest with `visited` URLs
- **THEN** the conversion pipeline SHALL accept at minimum:
  - `runDir`: the directory containing intermediate `.html` files
  - `manifest`: the traversal manifest with `visited` array
  - `fetcherFn`: a function that resolves the Scrapling fetcher for a given URL
  - `concurrency`: maximum number of concurrent conversions
  - `merge`: whether to produce a merged output file
  - `cleanupHtml`: whether to delete intermediate `.html` files after conversion

#### Scenario: Consumed by crawl

- **WHEN** `crawl` completes its strategy-guided traversal
- **THEN** it SHALL invoke the shared conversion pipeline to produce Markdown

#### Scenario: Consumed by scrape

- **WHEN** `scrape` completes its self-discovered traversal
- **THEN** it SHALL invoke the shared conversion pipeline to produce Markdown

### Requirement: Concurrent re-fetch with --ai-targeted

The conversion pipeline SHALL re-fetch each visited URL using Scrapling with the `--ai-targeted` flag to produce Markdown.

#### Scenario: Per-page conversion

- **WHEN** a visited URL is processed by the pipeline
- **THEN** it SHALL invoke `scrapling extract <fetcher> <url> <outputPath>.md --ai-targeted`
- **AND** the output path SHALL follow the same numbering scheme as the intermediate `.html` files (e.g., `01.md` for `01.html`)

#### Scenario: Concurrency limiting

- **WHEN** the number of pending conversions reaches the configured `concurrency` limit
- **THEN** the pipeline SHALL wait for at least one pending conversion to settle before starting a new one
- **AND** it SHALL never exceed the configured concurrency limit at any time

### Requirement: Failure isolation

The conversion pipeline SHALL treat each per-page conversion as an independent operation; the failure of one conversion SHALL NOT block others.

#### Scenario: Individual conversion failure

- **WHEN** a single Scrapling invocation fails during Phase 2
- **THEN** the pipeline SHALL record the URL and error in the `failed` array
- **AND** it SHALL write a `.error.log` file next to the intended `.md` output
- **AND** it SHALL continue processing remaining URLs

#### Scenario: All conversions succeed

- **WHEN** all conversions succeed
- **THEN** the `failed` array SHALL be empty
- **AND** the pipeline SHALL return `successful` containing all URLs and their output paths

### Requirement: HTML intermediate cleanup

The conversion pipeline SHALL optionally remove intermediate `.html` files after all conversions complete.

#### Scenario: Cleanup enabled

- **WHEN** `cleanupHtml` is `true`
- **THEN** after all conversions settle (success or failure)
- **THEN** the pipeline SHALL delete all files in `runDir` ending with `.html`

#### Scenario: Cleanup disabled

- **WHEN** `cleanupHtml` is `false`
- **THEN** all `.html` files SHALL remain in `runDir`
- **AND** the pipeline SHALL NOT modify them

### Requirement: Optional merge

The conversion pipeline SHALL optionally merge all successfully produced `.md` files into a single document.

#### Scenario: Merge enabled

- **WHEN** `merge` is `true` and at least one conversion succeeded
- **THEN** the pipeline SHALL concatenate all successful `.md` files in visit-order
- **AND** it SHALL produce a `crawl-output.md` or `scrape-output.md` (named according to the calling command)
- **AND** the merged document SHALL begin with a `#` heading containing the command name and target URL
- **AND** each page's content SHALL be preceded by a `##` subheading derived from the page's first `# ` line, or the page number if no heading is found
- **AND** per-page `.md` files SHALL remain alongside the merged file

#### Scenario: Merge disabled

- **WHEN** `merge` is `false`
- **THEN** the pipeline SHALL NOT produce a merged file
- **AND** only per-page `.md` files SHALL exist

### Requirement: Return contract

The conversion pipeline SHALL return a structured result describing the outcome of Phase 2.

#### Scenario: Return value

- **WHEN** the pipeline completes
- **THEN** it SHALL return an object containing:
  - `successful`: array of `{ url, path }` for each successful conversion
  - `failed`: array of `{ url, error }` for each failed conversion
  - `mergedPath`: string or `null`, the absolute path to the merged file if `merge` was enabled and at least one page succeeded

### Requirement: Structured directory output

The conversion pipeline SHALL produce `.md` files in a directory structure that mirrors the URL pathname hierarchy of each visited page.

#### Scenario: URL pathname to file path mapping

- **WHEN** a visited URL has pathname `/wiki/Category:Weapons`
- **THEN** the output file SHALL be placed at `<runDir>/wiki/Category-Weapons.md`
- **AND** intermediate directories SHALL be created as needed

#### Scenario: Root path handling

- **WHEN** a visited URL has pathname `/` or is empty
- **THEN** the output file SHALL be named `<runDir>/index.md`

#### Scenario: Special character slugification

- **WHEN** a URL pathname contains characters not valid in file paths (e.g., `:`, `?`)
- **THEN** those characters SHALL be replaced with `-` in the file path
- **AND** consecutive `-` SHALL be collapsed to a single `-`

### Requirement: Link relativization

The conversion pipeline SHALL post-process each `.md` file to convert absolute same-domain links into relative file paths.

#### Scenario: Markdown link conversion

- **WHEN** a `.md` file contains a link `[text](https://domain.com/path)`
- **AND** `https://domain.com/path` is in the visited URL set
- **THEN** the link SHALL be rewritten to `[text](relative/path.md)`
- **AND** the relative path SHALL be computed from the source file's directory to the target file

#### Scenario: Angle-bracket link conversion

- **WHEN** a `.md` file contains an angle-bracket URL `<https://domain.com/path>`
- **AND** that URL is in the visited set
- **THEN** it SHALL be rewritten to `[url](relative/path.md)`

#### Scenario: External link preservation

- **WHEN** a link points to a URL not in the visited set or to a different domain
- **THEN** the link SHALL remain unchanged

### Requirement: Manifest augmentation

The conversion pipeline SHALL augment the traversal manifest with Phase 2 results.

#### Scenario: Phase 2 metadata

- **WHEN** the pipeline completes
- **THEN** it SHALL update the manifest with:
  - `phase2`: object containing `successful_count`, `failed_count`, and `failed_urls`
  - `conversion_engine`: the Scrapling fetcher used for conversion
  - `merge_output`: the merged file path, or `null`
  - `url_to_path`: mapping from visited URL to output file path
