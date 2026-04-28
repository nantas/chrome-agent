# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-bulk-fetch-contract`
- 来源: `phase-4-engine-extension-governance` proposal
- 变更类型: new

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — batch URL fetching

The system SHALL define the input parameters for scrapling-bulk-fetch, a Playwright-based batch webpage fetching engine that retrieves multiple URLs in a single browser session.

#### Scenario: Required input — URLs array

- **WHEN** scrapling-bulk-fetch is invoked
- **THEN** the `urls` parameter SHALL be a non-empty array of fully-formed absolute HTTPS URLs
- **AND** each URL SHALL be a valid absolute URL string

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

- **WHEN** `session_id` is provided from a prior `open_session` call
- **THEN** the engine SHALL reuse the existing browser session
- **AND** browser-level parameters SHALL be ignored because they were set at session creation time

#### Scenario: Optional input — browser parameters

- **WHEN** `session_id` is NOT provided
- **THEN** a new browser instance SHALL be launched with the documented optional parameters: `headless`, `disable_resources`, `useragent`, `cookies`, `network_idle`, `timeout`, `wait`, `wait_selector`, `wait_selector_state`, `timezone_id`, `locale`, `proxy`, `extra_headers`, `real_chrome`, `cdp_url`, and `google_search`

#### Scenario: Optional input — single URL behavior

- **WHEN** the `urls` array contains exactly one URL
- **THEN** the engine SHALL still return a bulk-formatted response with one entry
- **AND** this SHALL preserve output shape consistency

### Requirement: Output contract — per-URL response structure

The system SHALL define the output structure for scrapling-bulk-fetch.

Each URL in the input SHALL produce a response entry containing:

| Field | Type | Presence | Description |
|-------|------|----------|-------------|
| `status` | integer | always | HTTP status code |
| `content` | array | always | Two-element array `[extracted_body_string, ""]`; the second slot is reserved for per-item error text |
| `url` | string | always | Final URL after redirects |

#### Scenario: Successful batch response

- **WHEN** scrapling-bulk-fetch retrieves two URLs successfully
- **THEN** the output SHALL contain two response entries
- **AND** each entry SHALL have `status: 200`, a non-empty `content[0]`, and the final URL

#### Scenario: Partial failure response

- **WHEN** one URL succeeds and another fails
- **THEN** the output SHALL still contain both entries
- **AND** the failed entry SHALL have a non-200 `status` and MAY have an empty `content[0]`
- **AND** `content[1]` MAY contain an error message for the failed URL

#### Scenario: Content extraction fidelity

- **WHEN** `extraction_type` is `"markdown"` or `"text"`
- **THEN** the extracted `content[0]` SHALL preserve DOM reading order for each page independently
- **AND** inline image URLs SHALL be preserved using Markdown image syntax when `extraction_type` is `"markdown"`

### Requirement: Error contract — batch failure modes

The system SHALL define error handling for scrapling-bulk-fetch.

#### Scenario: All URLs timeout

- **WHEN** all URLs in the batch timeout
- **THEN** the engine SHALL return a timeout error response
- **AND** the error category SHALL be `timeout`
- **AND** the recommended next action SHALL be to increase `timeout` or reduce batch size

#### Scenario: Partial network failure

- **WHEN** some URLs are unreachable while others succeed
- **THEN** the unreachable URLs SHALL surface a `network` error condition
- **AND** successful URLs SHALL still return their content

#### Scenario: Browser crash during batch

- **WHEN** the browser instance crashes or becomes unresponsive during batch processing
- **THEN** the engine SHALL report a `browser` error
- **AND** the recommended next action SHALL be to retry with a fresh session

#### Scenario: Blocked during batch

- **WHEN** one or more URLs are blocked by a challenge or WAF
- **THEN** the blocked URLs SHALL record their HTTP status code and block-page content
- **AND** the error category SHALL be `block`
- **AND** the recommended next action SHALL be to retry with a stealth-capable bulk engine

#### Scenario: Parse failure for individual URL

- **WHEN** a URL loads successfully but content extraction fails
- **THEN** the entry MAY still have `status: 200` with empty or truncated `content[0]`
- **AND** the error category SHALL be `parse`
- **AND** the recommended next action SHALL be to retry with `extraction_type: "html"`

### Requirement: Smoke-check

The system SHALL provide a smoke-check scenario to validate scrapling-bulk-fetch.

#### Scenario: Smoke-check

- **WHEN** scrapling-bulk-fetch is used with `urls: ["https://example.com", "https://httpbin.org/get"]`, `extraction_type: "text"`, `main_content_only: false`, and `timeout: 30000`
- **THEN** the output SHALL contain two response entries
- **AND** both entries SHALL have `status: 200`
- **AND** the `content[0]` for `https://example.com` SHALL contain `Example Domain`
- **AND** the `content[0]` for `https://httpbin.org/get` SHALL contain JSON response data
- **AND** both entries SHALL include their final URLs in the `url` field
