# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-get-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——Phase 2 为 5 个引擎创建契约，每个引擎含 input/output/error 三维 + smoke-check scenario。get 引擎 evidence: 微信公开文章

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — URL and request parameters

The system SHALL define the accepted input parameters for Scrapling get, which uses HTTP impersonation for static and low-protection pages.

#### Scenario: Required parameter — url

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL require a `url` parameter of type string, supporting HTTP and HTTPS schemes
- **AND** the URL SHALL be a fully-formed valid URL

#### Scenario: Optional parameter — extraction_type

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `extraction_type` with values `markdown` (default), `text`, or `html`
- **AND** the default output format SHALL be markdown

#### Scenario: Optional parameter — main_content_only

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `main_content_only` boolean, defaulting to `true`
- **AND** when `true`, the extraction SHALL target only the content inside `<body>`

#### Scenario: Optional parameter — css_selector

- **WHEN** `css_selector` is provided
- **THEN** extraction SHALL target only the elements matching the selector
- **AND** if applied to `main_content_only=true`, the selector SHALL be executed on the main content region

#### Scenario: Optional parameter — impersonate

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `impersonate` parameter controlling browser fingerprint impersonation, defaulting to `chrome`
- **AND** supported values SHALL include `chrome`, `safari`, `firefox`, `edge` and their versioned variants

#### Scenario: Optional parameter — timeout

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `timeout` in seconds (number), defaulting to 30
- **AND** the fetch SHALL abort if the request does not complete within the timeout

#### Scenario: Optional parameter — retries

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `retries` (integer), defaulting to 3
- **AND** `retry_delay` SHALL default to 1 second between attempts

#### Scenario: Optional parameter — headers and cookies

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `headers` dictionary of custom HTTP headers
- **AND** it SHALL accept optional `cookies` for per-request cookie values
- **AND** `stealthy_headers` SHALL default to `true`, generating real browser headers and Google referer

#### Scenario: Optional parameter — proxy

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL accept optional `proxy` as a string URL or dictionary with server/username/password keys
- **AND** when a proxy is configured, all requests SHALL be routed through it

#### Scenario: Session mode

- **WHEN** Scrapling get is invoked
- **THEN** it SHALL operate in single-shot mode by default (no persistent session)
- **AND** bulk usage SHALL be through the separate `bulk_get` variant, not `get`

#### Scenario: Authentication boundary

- **WHEN** Scrapling get is used
- **THEN** it SHALL target public, non-authenticated pages by default
- **AND** any use with authenticated cookies SHALL require explicit user approval and remain read-only

### Requirement: Output contract — response structure and format

The system SHALL define the structure and content of a successful Scrapling get response.

#### Scenario: Response format

- **WHEN** Scrapling get completes successfully
- **THEN** the output SHALL include a response object containing the extracted content in the requested `extraction_type` format
- **AND** the default markdown output SHALL convert HTML body to GitHub-flavored Markdown

#### Scenario: Metadata fields

- **WHEN** Scrapling get completes successfully
- **THEN** the response SHALL include metadata: page title, final URL (after redirects), and response timestamp
- **AND** the response SHALL indicate the fetcher path used (e.g., `scrapling-get`)

#### Scenario: Image handling

- **WHEN** Scrapling get extracts article-style content with images
- **THEN** inline image URLs SHALL be preserved in the output using Markdown image syntax `![alt](url)`
- **AND** image source SHALL prefer `data-src` over `src` when both are present
- **AND** image URLs SHALL retain their original positions in DOM reading order
- **AND** images SHALL NOT be replaced with generic placeholders

#### Scenario: Main content extraction

- **WHEN** `main_content_only` is `true` (default)
- **THEN** extraction SHALL target the `<body>` element content
- **AND** navigation elements, sidebars, and footer content SHALL be excluded where possible

#### Scenario: Content ordering

- **WHEN** article-style content is extracted
- **THEN** the output SHALL preserve the DOM reading order of text blocks and images
- **AND** plain `innerText` SHALL NOT be relied upon as the sole extraction method when images are present

### Requirement: Error contract — failure classification

The system SHALL define error categories and recommended actions for Scrapling get failures.

#### Scenario: Error categories

- **WHEN** Scrapling get fails
- **THEN** the error SHALL be classified into one of: network, timeout, block, parse

| Error Category | Description |
|---------------|-------------|
| network | DNS resolution failure, connection refused, TLS error |
| timeout | Request exceeded configured timeout duration |
| block | HTTP 4xx/5xx status, Cloudflare/IAP challenge page, IP-based access denial |
| parse | HTML parsing failure, selector not found, empty content despite successful HTTP status |

#### Scenario: Error response structure

- **WHEN** an error occurs
- **THEN** the error response SHALL include: error category, HTTP status code (if available), final URL reached, human-readable error message, and diagnostic context (response headers, page title, key body excerpt when available)

#### Scenario: Recommended next action per network error

- **WHEN** a network error occurs
- **THEN** the recommended next action SHALL be: retry with backoff up to max retries; if persistent, report as unreachable

#### Scenario: Recommended next action per timeout error

- **WHEN** a timeout error occurs
- **THEN** the recommended next action SHALL be: increase timeout parameter and retry; if persistent, escalate to `scrapling-fetch` for JS-heavy pages

#### Scenario: Recommended next action per block error

- **WHEN** a block error occurs (HTTP 403, CF challenge)
- **THEN** the recommended next action SHALL be: escalate to `scrapling-stealthy-fetch` if the block is anti-bot related; escalate to `chrome-devtools-mcp` for diagnostic evidence; escalate to `chrome-cdp` if an authenticated session is required

#### Scenario: Recommended next action per parse error

- **WHEN** a parse error occurs
- **THEN** the recommended next action SHALL be: verify the page is not an SPA requiring JS rendering; if SPA, escalate to `scrapling-fetch`; if content is available but selector wrong, adjust `css_selector` and retry

### Requirement: Smoke-check scenario — WeChat public article

The system SHALL validate the Scrapling get contract against a known public target.

#### Scenario: WeChat article extraction

- **WHEN** Scrapling get is tested against a public WeChat article at `https://mp.weixin.qq.com/s/<article-id>`
- **THEN** the extraction SHALL return: page title (from `#activity-name` or document title), article body content in DOM order, and inline image URLs preserved with Markdown syntax
- **AND** the response SHALL include `final_url` and `fetcher_path: scrapling-get`
- **AND** `#js_content` SHALL be the primary extraction root for the article body
