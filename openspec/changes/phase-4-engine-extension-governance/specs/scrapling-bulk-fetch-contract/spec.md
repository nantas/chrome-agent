# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-bulk-fetch-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: explore mode 中确认——scrapling-bulk-fetch 作为示例扩展引擎，已验证可用（example.com + httpbin.org 双 URL 测试通过），支持 session_id 复用

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — batch URL fetching

The system SHALL define the input parameters for scrapling-bulk-fetch, a Playwright-based batch webpage fetching engine that retrieves multiple URLs in a single browser session.

#### Scenario: Required input — URLs array

- **WHEN** scrapling-bulk-fetch is invoked
- **THEN** the `urls` parameter SHALL be a non-empty array of fully-formed HTTPS URLs
- **AND** each URL SHALL be a valid absolute URL string (e.g., `["https://example.com", "https://httpbin.org/get"]`)

#### Scenario: Optional input — extraction format

- **WHEN** `extraction_type` is specified
- **THEN** it SHALL accept `"text"`, `"html"`, or `"markdown"`
- **AND** the default SHALL be `"markdown"`
- **AND** each URL's response SHALL use the same extraction format

#### Scenario: Optional input — CSS selector

- **WHEN** `css_selector` is specified
- **THEN** it SHALL apply to each URL independently
- **AND** if `main_content_only` is true, the selector SHALL be evaluated against the main content for each page

#### Scenario: Optional input — main content only

- **WHEN** `main_content_only` is specified
- **THEN** it SHALL default to `true`
- **AND** each page's output SHALL be limited to `<body>` content when true

#### Scenario: Optional input — session reuse

- **WHEN** `session_id` is provided (from a prior `open_session` call)
- **THEN** the engine SHALL reuse the existing browser session
- **AND** browser-level parameters (headless, proxy, locale, etc.) SHALL be ignored (set at session creation time)
- **AND** this enables batch operations across multiple sequential bulk-fetch calls

#### Scenario: Optional input — browser parameters

- **WHEN** `session_id` is NOT provided
- **THEN** a new browser instance SHALL be launched with the following optional parameters:
  - `headless` (boolean, default `true`): run in headless mode
  - `disable_resources` (boolean, default `false`): drop non-essential resource requests
  - `useragent` (string, optional): custom user agent; otherwise auto-generated
  - `cookies` (array, optional): Playwright-format cookie objects
  - `network_idle` (boolean, default `false`): wait for network idle before capture
  - `timeout` (integer, default `30000`): timeout in milliseconds for all operations
  - `wait` (integer, default `0`): additional wait in milliseconds after page load
  - `wait_selector` (string, optional): CSS selector to wait for before capture
  - `wait_selector_state` (enum, default `attached`): state to wait for the selector
  - `timezone_id` (string, optional): timezone override
  - `locale` (string, optional): locale override
  - `proxy` (string or object, optional): proxy configuration
  - `extra_headers` (object, optional): additional HTTP headers
  - `real_chrome` (boolean, default `false`): use locally installed Chrome
  - `cdp_url` (string, optional): connect to existing browser via CDP
  - `google_search` (boolean, default `true`): set Google referer header

#### Scenario: Optional input — single URL behavior

- **WHEN** the `urls` array contains exactly one URL
- **THEN** the engine SHALL still return a bulk-formatted response (array with one entry)
- **AND** this ensures consistent output format regardless of URL count

### Requirement: Output contract — per-URL response structure

The system SHALL define the output structure for scrapling-bulk-fetch.

Each URL in the input SHALL produce a response entry containing:

| Field | Type | Presence | Description |
|-------|------|----------|-------------|
| `status` | integer | always | HTTP status code (e.g., 200, 403) |
| `content` | array | always | Two-element array: `[extracted_body_string, ""]`; second element is a placeholder for per-item error messages |
| `url` | string | always | Final URL after all redirects |

#### Scenario: Successful batch response

- **WHEN** scrapling-bulk-fetch retrieves two URLs successfully
- **THEN** the output SHALL contain two response entries
- **AND** each entry SHALL have `status: 200`, a non-empty `content[0]` body string, and the final URL

#### Scenario: Partial failure response

- **WHEN** one URL succeeds and another fails (e.g., timeout, 403)
- **THEN** the output SHALL still contain both entries
- **AND** the failed entry SHALL have a non-200 `status` and may have an empty `content[0]`
- **AND** the second element of `content` (index 1) MAY contain an error message for the failed URL

#### Scenario: Content extraction fidelity

- **WHEN** `extraction_type` is `"markdown"` or `"text"`
- **THEN** the extracted `content[0]` SHALL preserve DOM reading order for each page independently
- **AND** inline image URLs SHALL be preserved at their original positions using Markdown image syntax when `extraction_type` is `"markdown"`

### Requirement: Error contract — batch failure modes

The system SHALL define error handling for scrapling-bulk-fetch.

#### Scenario: All URLs timeout

- **WHEN** all URLs in the batch timeout (engine-level timeout, not per-URL)
- **THEN** the engine SHALL return an error response indicating timeout
- **AND** the error category SHALL be `timeout`
- **AND** the recommended next action SHALL be: increase `timeout` parameter or reduce batch size

#### Scenario: Partial network failure

- **WHEN** some URLs are unreachable while others succeed
- **THEN** the unreachable URLs SHALL have `status` reflecting the network error (e.g., 0 or appropriate error code)
- **AND** successful URLs SHALL still return their content
- **AND** the error category for the failed URLs SHALL be `network`

#### Scenario: Browser crash during batch

- **WHEN** the browser instance crashes or becomes unresponsive during batch processing
- **THEN** the engine SHALL report a `browser` error
- **AND** the recommended next action SHALL be: retry with a fresh session
- **AND** any URLs processed before the crash MAY be included in the response

#### Scenario: Blocked during batch

- **WHEN** one or more URLs are blocked (403, WAF challenge, CAPTCHA)
- **THEN** the blocked URLs SHALL have their HTTP status code recorded
- **AND** `content[0]` SHALL contain the block page content (challenge page, error page)
- **AND** the error category SHALL be `block`
- **AND** the recommended next action SHALL be: retry with `scrapling-stealthy-fetch` or `scrapling-bulk-stealthy-fetch`

#### Scenario: Parse failure for individual URL

- **WHEN** a URL loads successfully but content extraction fails (e.g., malformed HTML)
- **THEN** the output SHALL have `status: 200` but `content[0]` may be empty or truncated
- **AND** the error category SHALL be `parse`
- **AND** the recommended next action SHALL be: try `extraction_type: "html"` for raw HTML access

### Requirement: Smoke-check

The system SHALL provide a smoke-check scenario to validate scrapling-bulk-fetch.

#### Scenario: Smoke-check

- **WHEN** scrapling-bulk-fetch is used with `urls: ["https://example.com", "https://httpbin.org/get"]`, `extraction_type: "text"`, `main_content_only: false`, `timeout: 30000`, `retries: 1`
- **THEN** the output SHALL contain two response entries
- **AND** both entries SHALL have `status: 200`
- **AND** the `content[0]` for https://example.com SHALL contain the text "Example Domain"
- **AND** the `content[0]` for https://httpbin.org/get SHALL contain JSON response data
- **AND** both entries SHALL have their respective final URLs in the `url` field
