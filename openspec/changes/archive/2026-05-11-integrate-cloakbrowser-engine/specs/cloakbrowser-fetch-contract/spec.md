# Specification

## Capability

- **Capability ID:** `cloakbrowser-fetch-contract`
- **Version:** `1.0.0`
- **Status:** `draft`
- **Engine ID:** `cloakbrowser-fetch`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## Requirements

### Requirement: Input contract

The system SHALL support the following input parameters for cloakbrowser-fetch.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | yes | — | Target page URL (http/https only) |
| `headless` | boolean | no | `true` | Run in headless mode |
| `wait_until` | enum | no | `domcontentloaded` | Page lifecycle wait condition: `load`, `domcontentloaded`, `networkidle` |
| `timeout` | integer | no | 30 | Maximum wait time in seconds |
| `proxy` | string | no | — | Proxy URL (http/https/socks5) |
| `stealth_args` | boolean | no | `true` | Include default stealth fingerprint args |
| `humanize` | boolean | no | `false` | Enable human-like mouse/keyboard/scroll behavior |
| `fingerprint_seed` | integer | no | random | Deterministic fingerprint seed for consistent identity |
| `timezone` | string | no | — | IANA timezone (e.g. `America/New_York`). Set via binary flag, not CDP emulation |
| `locale` | string | no | — | BCP 47 locale (e.g. `en-US`). Set via binary flag, not CDP emulation |
| `geoip` | boolean | no | `false` | Auto-detect timezone/locale from proxy IP. Requires `geoip2` |
| `persistent_context` | string | no | — | Path to persistent user data directory for cookie/session reuse |
| `extra_args` | string[] | no | — | Additional Chromium CLI arguments to pass |

#### Scenario: Basic stealth page fetch

- **WHEN** cloakbrowser-fetch is invoked with `url: "https://scrapingbee.com/blog"` and `wait_until: "domcontentloaded"`
- **THEN** the engine SHALL return rendered HTML containing blog article entries
- **AND** the output SHALL include 140+ `<a>` links and 4000+ characters of body text
- **AND** the page title SHALL be "ScrapingBee's Blog"
- **AND** `navigator.webdriver` SHALL be `false`
- **AND** `typeof window.chrome` SHALL be `"object"`

#### Scenario: Cloudflare Turnstile challenge resolution

- **WHEN** cloakbrowser-fetch is invoked with `url: "https://wiki.supercombo.gg"` and `wait_until: "domcontentloaded"`
- **THEN** the engine SHALL wait for Cloudflare Turnstile + JS challenge auto-resolution
- **AND** within 15 seconds, the engine SHALL return rendered wiki content (not challenge page)
- **AND** the output SHALL contain 20,000+ characters of body text
- **AND** the page title SHALL be "SuperCombo Wiki" (not "请稍候…" or "Just a moment...")

#### Scenario: reCAPTCHA v3 score

- **WHEN** cloakbrowser-fetch is invoked with a page that triggers reCAPTCHA v3
- **THEN** the engine SHALL produce a reCAPTCHA v3 score of 0.7 or higher (server-side verified)
- **AND** `navigator.webdriver` SHALL remain `false` throughout the session

#### Scenario: Proxy support

- **WHEN** cloakbrowser-fetch is invoked with `proxy: "socks5://user:pass@host:1080"`
- **THEN** the engine SHALL route all traffic through the specified SOCKS5 proxy
- **AND** SOCKS5 credentials SHALL be passed via `--proxy-server` Chrome CLI flag (not Playwright proxy dict)

#### Scenario: Persistent context

- **WHEN** cloakbrowser-fetch is invoked with `persistent_context: "/tmp/cloak-profile"`
- **THEN** the engine SHALL create a persistent Chromium profile directory at the specified path
- **AND** cookies, localStorage, and cached data SHALL survive across invocations using the same path
- **AND** the profile SHALL bypass incognito mode detection

#### Scenario: Headless mode stealth

- **WHEN** cloakbrowser-fetch is invoked with `headless: true`
- **THEN** the engine SHALL NOT leak headless detection signals
- **AND** `navigator.plugins.length` SHALL be ≥ 5
- **AND** `navigator.userAgent` SHALL NOT contain "HeadlessChrome"

### Requirement: Stealth capabilities

The cloakbrowser-fetch engine SHALL provide source-level stealth via its patched Chromium binary.

#### Scenario: Source-level fingerprint patches

- **WHEN** the patched Chromium binary is launched
- **THEN** the following detection vectors SHALL be patched at the C++ level (not via JS injection):
  - Canvas fingerprint noise (consistent with target platform)
  - WebGL renderer and vendor strings
  - Audio context fingerprinting
  - Font enumeration
  - GPU and hardware reporting
  - Screen and window dimensions
  - WebRTC IP address handling
  - Network timing normalization
  - Automation signal removal (`navigator.webdriver = false`)
  - CDP input behavior mimicking

#### Scenario: Fingerprint seed management

- **WHEN** no `fingerprint_seed` is provided
- **THEN** a random seed (10000-99999) SHALL be auto-generated for each invocation
- **WHEN** `fingerprint_seed` is provided
- **THEN** the same seed SHALL produce the same fingerprint across invocations

#### Scenario: Platform-aware fingerprint profile

- **WHEN** running on macOS (darwin-arm64/darwin-x64)
- **THEN** the engine SHALL use a native macOS fingerprint profile by default
- **WHEN** running on Linux (linux-x64/linux-arm64)
- **THEN** the engine SHALL spoof as a Windows fingerprint profile by default (more common fingerprint)
- **AND** the wrapper SHALL pass `--fingerprint-platform=windows` on Linux

### Requirement: Error contract

The cloakbrowser-fetch engine SHALL define the following error categories.

| Error Category | Description | Typical Cause |
|----------------|-------------|---------------|
| `network` | Connection failure, DNS resolution failure, SSL/TLS error | Unreachable host, network outage |
| `timeout` | Page did not finish loading within the specified timeout | Slow page, infinite loading, challenge pending |
| `block` | Target returned a block page (CAPTCHA, challenge, WAF) | Anti-bot detection, IP reputation |
| `browser` | Chromium process crashed or became unresponsive | Binary corruption, resource exhaustion |
| `binary` | Patched Chromium binary not found or failed to launch | Binary not downloaded, platform not supported |
| `license` | Binary license restriction triggered | Unauthorized redistribution attempt |
| `challenge` | Cloudflare/DataDome/Kasada challenge not resolved within timeout | Aggressive anti-bot, headed mode required |

#### Scenario: Challenge escalation

- **WHEN** cloakbrowser-fetch returns a `challenge` error
- **THEN** the recommended fallback SHALL be `chrome-devtools-mcp` for diagnostic evidence collection
- **AND** if diagnostic evidence suggests headed mode would bypass, recommend headed mode with Xvfb

### Requirement: Smoke-check

The cloakbrowser-fetch engine SHALL define a smoke-check scenario for verification.

#### Scenario: Smoke-check — Cloudflare Turnstile auto-resolution

- **WHEN** cloakbrowser-fetch smoke-check is executed against `https://wiki.supercombo.gg/`
- **THEN** the engine SHALL auto-resolve the Cloudflare Turnstile + JS challenge within 15 seconds
- **AND** return rendered wiki content (20,000+ characters)
- **AND** the page title SHALL be "SuperCombo Wiki"

#### Scenario: Smoke-check — TLS fingerprint evasion

- **WHEN** cloakbrowser-fetch smoke-check is executed against `https://scrapingbee.com/blog/`
- **THEN** the engine SHALL return full page content with no empty body
- **AND** the response SHALL include 100+ links and 4000+ characters
