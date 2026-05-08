# Specification Delta: html-rendered-acquisition

## Capability 对齐（已确认）

- Capability: `html-rendered-acquisition`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认通过 MediaWiki API `action=parse&prop=text` 获取服务端渲染 HTML 作为主要获取路径，替代 wikitext-first 方案

## 规范真源声明

- 本文件是 `html-rendered-acquisition` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: api-parse-html-fetch
The system SHALL provide a content acquisition strategy that fetches page content via MediaWiki `action=parse` with `prop=text`, returning the server-rendered HTML fragment.

#### Scenario: fetch-sts2-entity-page
- **WHEN** the acquisition strategy is invoked for title `Slay the Spire 2:Bash`
- **THEN** it SHALL issue `action=parse&page=Slay_the_Spire_2:Bash&prop=text`
- **AND** return the HTML content from `parse.text.*`
- **AND** the returned HTML SHALL contain `.mw-parser-output` wrapper with complete infobox, headings, images, and internal links

#### Scenario: fetch-sts2-list-page
- **WHEN** the acquisition strategy is invoked for title `Slay the Spire 2:Cards_List`
- **THEN** it SHALL issue the same API call
- **AND** the returned HTML SHALL contain the complete `#cardsContainer` grid with all `card-box` elements and their data attributes
- **AND** the HTML size SHALL exceed 1 MB, confirming full server-side rendering of dynamic card grids

#### Scenario: fetch-sts1-page
- **WHEN** the acquisition strategy is invoked for a StS1 page (ns=0) such as `Bash`
- **THEN** it SHALL issue `action=parse&page=Bash&prop=text`
- **AND** return the HTML with the same structural guarantees as StS2 pages

### Requirement: api-fallback-on-parse-failure
The system SHALL fallback to wikitext acquisition (`prop=wikitext`) if `prop=text` returns empty or malformed HTML.

#### Scenario: parse-html-empty
- **WHEN** `action=parse&prop=text` returns empty or missing `parse.text.*`
- **THEN** the system SHALL automatically retry with `prop=wikitext`
- **AND** log a warning indicating the fallback

### Requirement: rate-limiting-and-retry
The system SHALL respect rate limiting for all API calls, with exponential backoff retry on HTTP 429 or transient failures.

#### Scenario: api-rate-limited
- **WHEN** the API returns HTTP 429
- **THEN** the system SHALL wait with exponential backoff (base 1s, max 8s)
- **AND** retry up to 3 times before failing the page
