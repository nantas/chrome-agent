# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-stealthy-fetch-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——stealthy-fetch 引擎契约 + Cloudflare Turnstile smoke check（evidence: wiki.supercombo.gg）。stealthy-fetch = fetch + 指纹伪装 + CF 挑战处理

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — stealth-enhanced parameters

The system SHALL define the accepted input parameters for Scrapling stealthy-fetch, which extends Scrapling fetch with fingerprint spoofing and anti-bot bypass capabilities.

#### Scenario: Inherited fetch parameters

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept all parameters defined in `scrapling-fetch-contract` input contract (url, headless, wait, wait_selector, network_idle, disable_resources, real_chrome, cdp_url, extraction_type, css_selector, main_content_only, useragent, timezone_id, locale, extra_headers, proxy, cookies, timeout, session_id)
- **AND** browser-level params SHALL be ignored when a `session_id` is provided

#### Scenario: Anti-bot bypass — solve_cloudflare

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept optional `solve_cloudflare` boolean, defaulting to `false`
- **AND** when `true`, the engine SHALL attempt to solve Cloudflare Turnstile/Interstitial challenges before returning the response

#### Scenario: Fingerprint spoofing — hide_canvas

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept optional `hide_canvas` boolean, defaulting to `false`
- **AND** when `true`, the engine SHALL add random noise to canvas operations to prevent fingerprinting

#### Scenario: Privacy protection — block_webrtc

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept optional `block_webrtc` boolean, defaulting to `false`
- **AND** when `true`, WebRTC SHALL respect proxy settings to prevent local IP address leak

#### Scenario: WebGL configuration — allow_webgl

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept optional `allow_webgl` boolean, defaulting to `true`
- **AND** WebGL SHALL remain enabled by default as many WAFs check WebGL availability

#### Scenario: Advanced customization — additional_args

- **WHEN** Scrapling stealthy-fetch is invoked
- **THEN** it SHALL accept optional `additional_args` dictionary for extra Playwright context settings
- **AND** `additional_args` SHALL take higher priority than Scrapling's default settings

#### Scenario: Session mode

- **WHEN** `open_session` is used with `session_type: stealthy`
- **THEN** the stealthy session SHALL support `max_pages` for concurrent browse operations, defaulting to 5
- **AND** the session SHALL persist stealthy configurations (hide_canvas, block_webrtc, solve_cloudflare) set at creation time

#### Scenario: Authentication boundary

- **WHEN** Scrapling stealthy-fetch is used with authenticated context
- **THEN** the same read-only and approval rules from `scrapling-fetch-contract` SHALL apply
- **AND** if anti-bot bypass succeeds but content requires login, the workflow SHALL escalate to `chrome-cdp`

### Requirement: Output contract — response structure

The system SHALL define the structure of a successful Scrapling stealthy-fetch response, with additional context for anti-bot bypass events.

#### Scenario: Post-bypass extraction

- **WHEN** Scrapling stealthy-fetch completes successfully after solving an anti-bot challenge
- **THEN** the output SHALL contain the underlying page content (not the challenge page shell)
- **AND** the response metadata SHALL indicate whether `solve_cloudflare` was engaged and whether a challenge was detected and solved

#### Scenario: Inherited output structure

- **WHEN** Scrapling stealthy-fetch completes successfully
- **THEN** the response SHALL include all fields defined in `scrapling-fetch-contract` output contract: page title, final URL, extraction format, content in DOM order, inline image URLs preserved
- **AND** the response SHALL indicate `fetcher_path: scrapling-stealthy-fetch`

### Requirement: Error contract — failure classification

The system SHALL define error categories for Scrapling stealthy-fetch, extending fetch contract with anti-bot-specific errors.

#### Scenario: Error categories

- **WHEN** Scrapling stealthy-fetch fails
- **THEN** the error SHALL be classified into one of: network, timeout, block, parse, browser, challenge

| Error Category | Description |
|---------------|-------------|
| network | DNS failure, connection refused, TLS error |
| timeout | Page load or wait condition exceeded timeout |
| block | HTTP 4xx/5xx despite stealth measures |
| parse | Extraction failed despite successful navigation |
| browser | Playwright launch failure, CDP connection failure |
| challenge | Cloudflare challenge detected but `solve_cloudflare` failed or timed out; challenge loop stuck |

#### Scenario: Recommended next action per challenge error

- **WHEN** a challenge error occurs (CF Turnstile not solved or stuck in loop)
- **THEN** the recommended next action SHALL be: retry with `solve_cloudflare=true` if not set; increase timeout if solve timed out; escalate to `chrome-devtools-mcp` for challenge page diagnostic evidence; as last resort, escalate to `chrome-cdp` if user has an approved live Chrome session

#### Scenario: Recommended next action per block error

- **WHEN** a block error persists despite stealth measures
- **THEN** the recommended next action SHALL be: verify that `solve_cloudflare`, `hide_canvas`, and `block_webrtc` are enabled; add proxy configuration; escalate to `chrome-devtools-mcp` for WAF page diagnostics; escalate to `chrome-cdp` for an approved live session

### Requirement: Smoke-check scenario — Cloudflare-protected page

The system SHALL validate the Scrapling stealthy-fetch contract against a known Cloudflare-protected target.

#### Scenario: wiki.supercombo.gg extraction

- **WHEN** Scrapling stealthy-fetch is tested against `https://wiki.supercombo.gg/w/Street_Fighter_6` with `solve_cloudflare=true`
- **THEN** the Cloudflare Turnstile challenge SHALL be solved
- **AND** the extraction SHALL return the article content (page title containing "Street Fighter 6", article body text)
- **AND** the response SHALL NOT contain only the challenge shell (e.g., page title "Just a moment..." or "请稍候…")
- **AND** the response SHALL indicate `fetcher_path: scrapling-stealthy-fetch`
