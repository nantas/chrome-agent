# Specification Delta

## Capability 对齐（已确认）

- Capability: `cdp-page-cache`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 确认 — chrome-cdp 引擎需接入 Pipeline `.cache/` 持久化缓存体系

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: CDP cache write
The system SHALL persist CDP-fetched page content to `<repo_root>/.cache/chrome-cdp/<domain>/<safe_path>.json` using the same `save_page_cache()` interface as the MediaWiki pipeline.

- The `platform` field SHALL be `"chrome-cdp"`.
- The `domain` SHALL be the hostname extracted from the page URL.
- The `safe_path` SHALL be the page's URL path with `/` replaced by `_` and `.html` suffix preserved, used as the cache filename via `raw_to_cache_filename()`.
- The cache entry SHALL include `html` (raw HTML string), `fetched_at` (ISO 8601 UTC timestamp), and `url` (the full source URL).

#### Scenario: First fetch caches the page
- **WHEN** a CDP page is extracted via `nav` + `eval` and saved with `save_page_cache(repo_root, "chrome-cdp", domain, raw_data)`
- **THEN** a `.json` file is atomically written to `.cache/chrome-cdp/<domain>/<safe_path>.json` containing `html`, `url`, and `fetched_at`

#### Scenario: Re-fetch skips cached pages
- **WHEN** `list_cached_pages(repo_root, "chrome-cdp", domain)` returns the page's safe path
- **THEN** the fetch phase SHALL skip CDP navigation for that page and return `skipped` status

### Requirement: CDP cache read
The system SHALL support loading cached CDP pages via `load_page_cache(repo_root, "chrome-cdp", domain, safe_path)`.

#### Scenario: Load valid cache entry
- **WHEN** a cached `.json` file exists at `.cache/chrome-cdp/<domain>/<safe_path>.json`
- **THEN** `load_page_cache()` returns a dict with `html`, `url`, and `fetched_at` fields

#### Scenario: Missing cache returns None
- **WHEN** no cache entry exists for the given domain and safe_path
- **THEN** `load_page_cache()` returns `None`

### Requirement: Cache path convention
The cache SHALL use the directory structure `.cache/chrome-cdp/<domain>/` with files named by URL-safe path conversion.

#### Scenario: URL path to safe filename
- **WHEN** the page URL path is `/Packages/Network/Guides/NX-Account_Guide/contents/Pages/Page_106359742.html`
- **THEN** `raw_to_cache_filename()` produces `Packages_Network_Guides_NX-Account_Guide_contents_Pages_Page_106359742.html.json`
