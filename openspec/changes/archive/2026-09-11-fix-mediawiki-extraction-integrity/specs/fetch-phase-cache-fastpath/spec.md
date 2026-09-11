# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-phase-cache-fastpath`
- 来源: `proposal.md` / 用户授权“按照你建议的方案创建 change”。
- 变更类型: modified
- 用户确认摘要: 落实已讨论的抽取完整性修复范围；不自动恢复全站抓取。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 以此为依据，页面回写不得替代 spec delta。

## MODIFIED Requirements

### Requirement: full-cache-fastpath
`run_fetch()` SHALL check all manifest pages for compatible cache entries using `mediawiki-cache-integrity` before creating a ThreadPoolExecutor. Only when every page passes admission and `re_fetch == False` SHALL it return skipped statistics without worker scheduling or API requests. No fixed sub-second wall-clock bound SHALL override identity and payload validation.

#### Scenario: all-pages-cached
- **WHEN** all N manifest pages have compatible entries and re-fetch is false
- **THEN** fetch SHALL create no executor, make no API calls, and return total=N, fetched=0, skipped=N, failed=0.

#### Scenario: all-pages-cached-with-re-fetch
- **WHEN** re-fetch is true
- **THEN** the fast path SHALL NOT trigger and every manifest page SHALL be scheduled for acquisition.

#### Scenario: filenames-exist-but-mode-changed
- **WHEN** every title has a cache file but any entry fails current-mode admission
- **THEN** the all-cached fast path SHALL NOT trigger.

### Requirement: partial-cache-prefilter
`run_fetch()` SHALL partition manifest pages by compatible cache admission before scheduling workers. Only incompatible or absent entries SHALL be fetched, unless re-fetch is true. Compatible entries SHALL count as skipped without futures. Failed replacement acquisition SHALL remain a failure and SHALL NOT authorize conversion of incompatible old content.

#### Scenario: mixed-cache
- **WHEN** 4,900 entries are compatible and 100 are missing or incompatible
- **THEN** only 100 futures SHALL be submitted and initial skipped count SHALL be 4,900.

#### Scenario: no-cache
- **WHEN** no manifest page has a compatible entry
- **THEN** all pages SHALL be scheduled.

#### Scenario: replacement-fetch-fails
- **WHEN** acquiring HTML to replace old hybrid content fails
- **THEN** the page SHALL remain failed and incompatible old content SHALL NOT be reported as a successful cache fallback.

## ADDED Requirements

### Requirement: acquired-payload-admission
Freshly acquired content SHALL satisfy the same identity, resolved acquisition and payload requirements before being counted as fetched successfully or replacing a valid cache entry. An HTML request returning only fallback wikitext SHALL remain an acquisition failure for that request.

#### Scenario: fresh-html-request-without-html
- **WHEN** an HTML acquisition response contains empty HTML and fallback wikitext
- **THEN** fetch SHALL report a payload incompatibility instead of recording an HTML success.

#### Scenario: failed-forced-fetch-is-not-a-cache-hit
- **WHEN** a forced fetch fails despite an older compatible cache entry
- **THEN** fetch SHALL report the failed title, fetch-only SHALL return a nonzero exit code, and combined conversion SHALL NOT resume that title from the old entry.
