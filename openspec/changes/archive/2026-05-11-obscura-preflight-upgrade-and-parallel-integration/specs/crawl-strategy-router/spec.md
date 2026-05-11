# Specification Delta

## Capability 对齐（已确认）

- Capability: `crawl-strategy-router`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: crawl-strategy-routing

The crawl command SHALL read the strategy frontmatter's `api.platform` field to determine content acquisition pipeline.

`api.platform === "mediawiki"` → route to MediaWiki API pipeline (unchanged behavior, no Obscura involvement). Otherwise → route to Browser crawl pipeline (Scrapling serial by default, optional Obscura parallel).

#### Scenario: crawl-api-route
- **WHEN** the strategy frontmatter contains `api.platform: mediawiki`
- **THEN** the system SHALL route to `scripts/mediawiki-api-extract` as before (unchanged behavior)

#### Scenario: crawl-browser-route-default
- **WHEN** the strategy has no `api` field or `api.platform` is not `mediawiki`, and `--parallel` is not specified
- **THEN** the system SHALL use the existing Scrapling serial crawl path (default, unchanged)

#### Scenario: crawl-browser-route-parallel
- **WHEN** the strategy has no `api` field or `api.platform` is not `mediawiki`, and `--parallel` is specified
- **THEN** the system SHALL use the Obscura serve pool parallel crawl path

### Requirement: crawl-parallel-three-phase

The crawl command with `--parallel` SHALL execute a three-phase workflow: traversal → serve pool fetch → markdown conversion.

#### Scenario: crawl-parallel-traversal
- **WHEN** `crawl --parallel` starts
- **THEN** Phase 1 (traversal) SHALL use Scrapling `get` to discover and collect all URLs, building the same `visited` set as the serial crawl, up to `--max-pages` limit

#### Scenario: crawl-parallel-batch-fetch
- **WHEN** Phase 1 completes and the visited URL set is available
- **THEN** Phase 2 SHALL start the Obscura serve pool with `--workers` count, fetch all visited URLs concurrently, and save HTML files to the run directory

#### Scenario: crawl-parallel-markdown
- **WHEN** Phase 2 completes and all HTML files are saved
- **THEN** Phase 3 SHALL call `convertTraversalToMarkdown` with the manifest, producing Markdown output identical to the serial crawl path
