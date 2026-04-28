# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-fetch-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——fetch 引擎契约 + Twitter 公开推文 smoke check（Phase 2 新补证据）。fetch 使用 Playwright 渲染 JS 页面

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — URL and Playwright parameters

The system SHALL define the accepted input parameters for Scrapling fetch, which uses Playwright browser automation for SPA and dynamic pages.

#### Scenario: Required parameter — url

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL require a `url` parameter of type string, supporting HTTP and HTTPS schemes

#### Scenario: Browser mode parameters

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL accept optional `headless` boolean, defaulting to `true`
- **AND** it SHALL accept optional `real_chrome` boolean, defaulting to `false`
- **AND** it SHALL accept optional `cdp_url` string for connecting to an existing Chrome instance
- **AND** it SHALL accept optional `disable_resources` boolean, defaulting to `false`, which drops font/image/media/stylesheet requests for speed

#### Scenario: Wait strategy parameters

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL accept optional `wait` in milliseconds, defaulting to 0, for post-load wait before extraction
- **AND** it SHALL accept optional `wait_selector` CSS selector string
- **AND** it SHALL accept optional `wait_selector_state` with values `attached` (default), `detached`, `hidden`, `visible`
- **AND** it SHALL accept optional `network_idle` boolean, defaulting to `false`, which waits until no network activity for 500ms

#### Scenario: Content extraction parameters

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL accept optional `extraction_type` with values `markdown` (default), `text`, or `html`
- **AND** it SHALL accept optional `css_selector` for targeted extraction
- **AND** it SHALL accept optional `main_content_only` boolean, defaulting to `true`

#### Scenario: Browser identity parameters

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL accept optional `useragent` string for custom user agent
- **AND** it SHALL accept optional `timezone_id` string for browser timezone
- **AND** it SHALL accept optional `locale` string for browser locale (e.g., `en-GB`)
- **AND** it SHALL accept optional `extra_headers` dictionary
- **AND** `google_search` SHALL default to `true`, setting a Google referer header

#### Scenario: Network and auth parameters

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL accept optional `timeout` in milliseconds, defaulting to 30000
- **AND** it SHALL accept optional `proxy` as string or server/username/password dictionary
- **AND** it SHALL accept optional `cookies` as Playwright cookie array

#### Scenario: Session mode

- **WHEN** Scrapling fetch is invoked
- **THEN** it SHALL support single-shot mode by default
- **AND** it SHALL support persistent session mode via `session_id` from `open_session`
- **AND** bulk usage SHALL be through `bulk_fetch` variant
- **AND** when a `session_id` is provided, browser-level params from session creation SHALL take precedence

#### Scenario: Authentication boundary

- **WHEN** Scrapling fetch is used with cookies or authenticated session
- **THEN** the target page SHALL require explicit user approval
- **AND** the run SHALL remain read-only by default
- **AND** if session reuse redirects to login or loses authenticated context, the path SHALL stop and record failure

### Requirement: Output contract — response structure

The system SHALL define the structure of a successful Scrapling fetch response.

#### Scenario: Post-render extraction

- **WHEN** Scrapling fetch completes successfully after Playwright renders the page
- **THEN** the output SHALL contain content extracted AFTER JavaScript execution and any `wait`/`wait_selector`/`network_idle` conditions are satisfied
- **AND** the output SHALL distinguish rendered content from pre-render shell content

#### Scenario: Response format and metadata

- **WHEN** Scrapling fetch completes successfully
- **THEN** the output SHALL include: extracted content in the requested format (markdown default), page title, final URL (after all redirects), and response timestamp
- **AND** the response SHALL indicate `fetcher_path: scrapling-fetch`

#### Scenario: Image handling

- **WHEN** Scrapling fetch extracts content with images
- **THEN** inline image URLs SHALL be preserved using Markdown image syntax
- **AND** image URLs SHALL retain DOM reading order positions

#### Scenario: SPA content detection

- **WHEN** the target is an SPA where initial HTML contains minimal content
- **THEN** the wait strategy `wait_selector` or `network_idle` SHALL be used to ensure dynamic content has loaded before extraction

### Requirement: Error contract — failure classification

The system SHALL define error categories for Scrapling fetch failures, extending the get contract with browser-specific errors.

#### Scenario: Error categories

- **WHEN** Scrapling fetch fails
- **THEN** the error SHALL be classified into one of: network, timeout, block, parse, browser

| Error Category | Description |
|---------------|-------------|
| network | DNS failure, connection refused, TLS error |
| timeout | Page load or wait_selector exceeded timeout (default 30000ms) |
| block | HTTP 4xx/5xx, anti-bot detection, WAF challenge (no stealth) |
| parse | Extraction failed despite successful navigation and render |
| browser | Playwright launch failure, CDP connection failure, Chrome crash |

#### Scenario: Error response structure

- **WHEN** an error occurs
- **THEN** the error response SHALL include: error category, HTTP status code (if available), final URL reached, wait conditions satisfied/failed, human-readable message, and diagnostic context

#### Scenario: Recommended next action per browser error

- **WHEN** a browser error occurs (Playwright crash, CDP disconnect)
- **THEN** the recommended next action SHALL be: retry with `real_chrome=true` if a local Chrome is available; if persistent, escalate to `chrome-devtools-mcp` for browser-level diagnostics

#### Scenario: Recommended next action per block error

- **WHEN** a block error occurs (403, challenge page)
- **THEN** the recommended next action SHALL be: escalate to `scrapling-stealthy-fetch` with `solve_cloudflare=true`

### Requirement: Smoke-check scenario — Twitter public tweet

The system SHALL validate the Scrapling fetch contract against a known SPA target.

#### Scenario: Twitter public tweet extraction

- **WHEN** Scrapling fetch is tested against a public Twitter tweet page at `https://x.com/<username>/status/<tweet-id>`
- **THEN** the page SHALL be rendered via Playwright with `network_idle=true` or equivalent wait to ensure dynamic tweet content loads
- **AND** the extraction SHALL verify the tweet author, tweet text content, and any embedded media links are present in the output
- **AND** the response SHALL include `final_url` and `fetcher_path: scrapling-fetch`
- **AND** if the public tweet page redirects to login (as observed with `get`), the test SHALL record this as a known limitation for public SPA targets on that domain
