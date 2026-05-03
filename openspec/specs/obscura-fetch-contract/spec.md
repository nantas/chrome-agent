# Specification

## Capability

- **Capability ID:** `obscura-fetch-contract`
- **Version:** `1.0.0`
- **Status:** `draft`
- **Engine ID:** `obscura-fetch`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## Requirements

### Requirement: Input contract

The system SHALL support the following input parameters for obscura-fetch.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | yes | — | Target page URL (http/https only) |
| `wait_until` | enum | no | `load` | Page lifecycle wait condition: `load`, `domcontentloaded`, `networkidle0`, `networkidle2` |
| `selector` | string | no | — | CSS selector to wait for before considering page loaded |
| `timeout` | integer | no | 30 | Maximum wait time in seconds |
| `stealth` | boolean | no | false | Enable anti-detection mode (TLS fingerprint impersonation + tracker blocking) |
| `extract_format` | enum | no | `html` | Output format: `html`, `text`, `markdown` |
| `eval` | string | no | — | JavaScript expression to evaluate and return as result |
| `user_agent` | string | no | Chrome 145 Linux | Custom User-Agent header |
| `proxy` | string | no | — | Proxy URL (http/https/socks5) |
| `obey_robots` | boolean | no | false | Respect robots.txt before fetching |

The engine SHALL accept a single URL per invocation. Bulk/parallel operations are out of scope for this contract.

#### Scenario: Basic dynamic page fetch

- **WHEN** obscura-fetch is invoked with `url: "https://news.ycombinator.com"` and `wait_until: "load"`
- **THEN** the engine SHALL return rendered HTML containing story titles, scores, and comment counts
- **AND** the output SHALL include the page title "Hacker News"

#### Scenario: JS evaluation

- **WHEN** obscura-fetch is invoked with `eval: "document.title"`
- **THEN** the engine SHALL return the evaluated JavaScript result as a string
- **AND** the result SHALL match the page's `<title>` content

#### Scenario: Stealth mode

- **WHEN** obscura-fetch is invoked with `stealth: true`
- **THEN** the engine SHALL use TLS fingerprint impersonation (Chrome 145 via wreq)
- **AND** the engine SHALL block requests to known tracker domains (3,520+ domains)
- **AND** the engine SHALL set `navigator.webdriver` to `undefined`
- **AND** stealth mode SHALL NOT guarantee bypass of advanced anti-bot challenges (Cloudflare Turnstile, DataDome)

#### Scenario: robots.txt compliance

- **WHEN** obscura-fetch is invoked with `obey_robots: true`
- **THEN** the engine SHALL fetch and parse the target domain's `robots.txt` before navigation
- **AND** if the target path is disallowed, the engine SHALL return a `block` error

### Requirement: Output contract

The system SHALL define the output structure for obscura-fetch.

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Final URL after redirects |
| `title` | string | Page title (from `<title>` or JS-evaluated `document.title`) |
| `content` | string | Extracted content in the requested format |
| `content_type` | enum | Format of content: `html`, `text`, `markdown` |
| `status_code` | integer | HTTP status code of the final response |
| `redirect_chain` | string[] | List of intermediate redirect URLs |
| `links` | object[] | Extracted links with `href` and `text` (when `extract_format: links`) |
| `timing_ms` | integer | Total wall time for the fetch operation |
| `network_events` | object[] | Recorded network requests with url, method, type, status, size |

#### Scenario: HTML output

- **WHEN** obscura-fetch is invoked with `extract_format: "html"`
- **THEN** `content` SHALL contain the full rendered HTML after JS execution
- **AND** `content_type` SHALL be `"html"`

#### Scenario: Text output

- **WHEN** obscura-fetch is invoked with `extract_format: "text"`
- **THEN** `content` SHALL contain human-readable text extracted from the DOM
- **AND** script and style content SHALL be excluded
- **AND** block-level elements SHALL be separated by newlines

#### Scenario: Markdown output

- **WHEN** obscura-fetch is invoked with `extract_format: "markdown"`
- **THEN** `content` SHALL contain DOM-to-Markdown conversion supporting: h1-h6, p, a, img, ul/ol/li, table, blockquote, code/pre, strong/em, hr
- **AND** links SHALL be rendered as `[text](href)`
- **AND** images SHALL be rendered as `![alt](src)` using original src URLs (no inline download)

#### Scenario: Image handling

- **WHEN** the page contains `<img>` elements
- **THEN** the markdown output SHALL preserve the original `src` URL
- **AND** the HTML output SHALL preserve the original `<img>` tags with all attributes
- **AND** images SHALL NOT be downloaded or base64-inlined by default

### Requirement: Error contract

The system SHALL define error handling for obscura-fetch.

The engine SHALL use the following error categories, consistent with the cross-engine error matrix in `engine-contracts`:

| Category | Description | Recommended Action |
|----------|-------------|-------------------|
| `network` | DNS resolution failure, connection refused, TLS error | Retry or escalate to scrapling-fetch |
| `timeout` | Page load or wait condition exceeded timeout | Increase timeout or simplify wait condition |
| `block` | Access denied (robots.txt, IP ban, HTTP 403) | Escalate to scrapling-stealthy-fetch |
| `parse` | HTML/JS parsing failure, malformed response | Escalate to scrapling-fetch |
| `browser` | V8 runtime crash or unrecoverable JS error | Escalate to scrapling-fetch |

#### Scenario: Network error

- **WHEN** the target host is unreachable
- **THEN** the engine SHALL return error category `network` with the underlying error message
- **AND** the recommended action SHALL be retry or escalate to scrapling-fetch

#### Scenario: Timeout

- **WHEN** page load exceeds the configured timeout
- **THEN** the engine SHALL return error category `timeout`
- **AND** the error SHALL include the timeout value and the last known lifecycle state

#### Scenario: robots.txt block

- **WHEN** `obey_robots: true` and the target path is disallowed
- **THEN** the engine SHALL return error category `block` with message indicating the robots.txt restriction
- **AND** the engine SHALL NOT escalate automatically

### Requirement: Performance characteristics

The system SHALL define expected performance boundaries for obscura-fetch.

- **Memory (idle RSS)**: ≤ 15 MB
- **Memory (peak, with V8 heap)**: ≤ 50 MB
- **Startup time (cold)**: ≤ 200 ms
- **Page load (static HTML)**: ≤ 200 ms
- **Page load (JS-rendered SPA)**: ≤ 3 s for typical dynamic pages
- **Binary size**: ≤ 80 MB

#### Scenario: Memory budget

- **WHEN** obscura-fetch is idle after serving a request
- **THEN** its RSS SHALL be ≤ 15 MB
- **AND** during active page rendering, peak RSS SHALL be ≤ 50 MB

#### Scenario: Performance comparison with scrapling-fetch

- **WHEN** obscura-fetch and scrapling-fetch are both used against the same JS-rendered page (e.g., news.ycombinator.com)
- **THEN** obscura-fetch SHALL complete in ≤ 50% of scrapling-fetch's wall time under equivalent network conditions

### Requirement: CDP compatibility

The system SHALL define the CDP protocol compatibility scope for obscura-fetch.

The engine's CDP server SHALL implement the following domains sufficiently for Puppeteer and Playwright basic connectivity:

| Domain | Key Methods |
|--------|------------|
| Target | createTarget, closeTarget, attachToTarget |
| Page | navigate, getFrameTree, addScriptToEvaluateOnNewDocument, lifecycleEvents |
| Runtime | evaluate, callFunctionOn, getProperties, addBinding |
| DOM | getDocument, querySelector, querySelectorAll, getOuterHTML |
| Network | enable, setCookies, getCookies, setExtraHTTPHeaders |
| Fetch | enable, continueRequest, fulfillRequest, failRequest |
| Storage | getCookies, setCookies, deleteCookies |
| Input | dispatchMouseEvent, dispatchKeyEvent |
| LP | getMarkdown (DOM-to-Markdown conversion) |

#### Scenario: Puppeteer connect

- **WHEN** Puppeteer connects to `ws://127.0.0.1:<port>/devtools/browser`
- **THEN** basic page navigation, DOM querying, and script evaluation SHALL work
- **AND** `page.goto()`, `page.evaluate()`, and `page.$$eval()` SHALL return expected results

#### Scenario: LP.getMarkdown

- **WHEN** `LP.getMarkdown` is called via CDP on a loaded page
- **THEN** the response SHALL contain a `markdown` field with the DOM-to-Markdown conversion
- **AND** the conversion SHALL cover h1-h6, p, a, img, ul/ol/li, table, blockquote, code/pre, strong/em, hr

### Requirement: Smoke-check

The system SHALL provide a smoke-check scenario to validate obscura-fetch.

#### Scenario: Smoke-check

- **WHEN** obscura-fetch is used against `https://news.ycombinator.com` with `wait_until: "load"` and `extract_format: "html"`
- **THEN** the output SHALL contain the page title "Hacker News"
- **AND** the output SHALL contain at least 20 story entries identifiable by `<a>` links within `<span class="titleline">` elements
- **AND** the status SHALL be HTTP 200
- **AND** `timing_ms` SHALL be ≤ 5000 ms
- **AND** no errors SHALL be returned

### Requirement: Known Limitations

The system SHALL document the following verified limitations of obscura-fetch v0.1.0.

#### JS Complexity and Runtime Stability

- **GIVEN** a page that uses heavy JavaScript animation libraries (e.g., GSAP, complex CSS transform animations)
- **WHEN** obscura-fetch attempts to render the page
- **THEN** the V8 runtime MAY throw unhandled exceptions (e.g., `TypeError: Cannot read properties of null (reading 'replace')`)
- **AND** the page load MAY hang indefinitely, exceeding the configured timeout
- **THEREFORE** the caller SHOULD set conservative timeouts (≤ 10 s) for unverified sites
- **AND** the caller SHOULD escalate to `scrapling-fetch` if JS errors or timeouts recur

#### SPA Hydration

- **GIVEN** a JavaScript-rendered SPA that hydrates content asynchronously after initial paint
- **WHEN** obscura-fetch returns the HTML output
- **THEN** the `<body>` MAY contain only inline styles, preload tags, or empty placeholder elements
- **AND** the dynamically hydrated content MAY be missing
- **THEREFORE** obscura-fetch is NOT RECOMMENDED for SPAs that rely on client-side hydration for primary content
- **AND** the caller SHOULD escalate to `scrapling-fetch` for such pages

#### Stealth Mode Effectiveness

- **GIVEN** `--stealth` is enabled (TLS fingerprint impersonation + tracker blocking)
- **WHEN** tested against Cloudflare challenge pages and heavy-JS anti-bot sites
- **THEN** stealth mode has NOT demonstrated measurable differences from plain mode in verified scenarios
- **AND** stealth mode does NOT bypass Cloudflare Turnstile, DataDome, or similar advanced anti-bot challenges
- **THEREFORE** `--stealth` is considered experimental; `scrapling-stealthy-fetch` remains the recommended engine for high-protection targets

#### Build Constraints

- **GIVEN** building from source with `--features stealth`
- **WHEN** compiling on macOS arm64 with Rust ≥ 1.75
- **THEN** the build MAY fail at the link stage due to `boring-sys2` (BoringSSL bindings) missing symbols
- **AND** `cmake` is required but may not resolve the linker errors on all platforms
- **THEREFORE** precompiled release binaries are the preferred distribution method
- **AND** stealth-dependent features are considered platform-conditional
