# Engines Domain: Engine Registry & Contracts — Merged Spec

> **Merged from**: `engine-registry`, `engine-contracts`, `extension-api`, `scrapling-get-contract`, `obscura-fetch-contract`, `scrapling-fetch-contract`, `scrapling-bulk-fetch-contract`, `cloakbrowser-fetch-contract`, `scrapling-stealthy-fetch-contract`, `chrome-devtools-mcp-contract`, `chrome-cdp-contract`
> **Purpose**: Complete reference for all registered engines, their contracts (input/output/error), cross-engine concerns, extension governance, and smoke-check inventory.

---

## Part 1 — Registry & Cross-Engine Concerns

### Source: `engine-registry`

#### Requirement: 注册索引位置与格式

The system SHALL maintain `configs/engine-registry.json` with an `engines` array. Each entry contains: `id`, `type`, `characteristics` (efficiency/stability/adaptability), `composite_score`, `default_rank`, `best_for`, `contract_spec`, `status`.

#### Requirement: 引擎特性评分维度

Three dimensions scored 0.00-1.00:
1. **efficiency**: Speed/resource cost
2. **stability**: Reliability for target scenarios
3. **adaptability**: Range of scenarios handled

#### Requirement: Composite Score 推导公式

`composite_score = round((adaptability × 0.50 + stability × 0.30 + efficiency × 0.20) × 100)`

#### Requirement: Default Rank 推导规则

- Rank 1: first engine to try for unknown URLs (`scrapling-get`)
- CDP-lightweight ranks between HTTP and full Playwright
- Within Scrapling: lighter before heavier (`scrapling-get` → `scrapling-fetch` → `cloakbrowser-fetch`)
- Within CDP: `chrome-devtools-mcp` before `chrome-cdp`

#### Requirement: 引擎生命周期状态

| State | Meaning |
|-------|---------|
| `draft` | Not fully validated |
| `frozen` | Validated and stable |
| `superseded` | Replaced; retained for reference |

#### Requirement: obscura-fetch engine entry

```json
{
  "id": "obscura-fetch", "type": "cdp_lightweight",
  "composite_score": 62, "default_rank": 2, "status": "draft"
}
```

#### Requirement: cloakbrowser-fetch engine entry

```json
{
  "id": "cloakbrowser-fetch", "type": "playwright_stealth",
  "composite_score": 62, "default_rank": 4, "status": "draft"
}
```

#### Requirement: scrapling-stealthy-fetch engine status update

`scrapling-stealthy-fetch` SHALL have `status: "superseded"`. Replacement: `cloakbrowser-fetch`.

#### Requirement: engine-registry-api-type

Registry SHALL include `mediawiki-api` with type `"api"` and default rank `0`.

---

### Source: `engine-contracts`

#### Requirement: Engine selection mapping

Priority sources:
1. Site strategy `engine_preference`
2. Anti-crawl strategy `engine_priority`
3. Engine `default_rank` from registry

Scrapling-first rule with `cdp_lightweight` between HTTP and Playwright.

#### Requirement: Cross-engine error contract consistency

| Category | scrapling-get | obscura-fetch | scrapling-fetch | cloakbrowser-fetch | scrapling-bulk-fetch | chrome-devtools-mcp | chrome-cdp |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| network | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| timeout | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| block | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| parse | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| browser | — | ✓ | ✓ | ✓ | ✓ | — | — |
| challenge | — | — | — | ✓ | — | — | — |
| binary | — | — | — | ✓ | — | — | — |
| license | — | — | — | ✓ | — | — | — |
| connection | — | — | — | — | — | ✓ | ✓ |
| navigation | — | — | — | — | — | ✓ | — |
| selector | — | — | — | — | — | ✓ | — |
| evaluation | — | — | — | — | — | ✓ | — |
| auth_redirect | — | — | — | — | — | — | ✓ |
| session_loss | — | — | — | — | — | — | ✓ |
| rate_limit | — | — | — | — | — | — | ✓ |

#### Requirement: Escalation chain

Standard: `scrapling-get → obscura-fetch → scrapling-fetch → cloakbrowser-fetch → chrome-devtools-mcp`
Live-session: `scrapling-fetch/cloakbrowser-fetch (session reuse fail) → chrome-cdp`

#### Requirement: Smoke-check inventory

| Engine | Target | Expected Outcome |
|--------|--------|-----------------|
| scrapling-get | mp.weixin.qq.com/s/... | 文章标题 + DOM 顺序正文 + 内联图片 |
| obscura-fetch | news.ycombinator.com | "Hacker News" + ≥20 entries + ≤5000ms |
| scrapling-fetch | x.com/.../status/... | SPA 推文内容 |
| cloakbrowser-fetch | wiki.supercombo.gg | CF Turnstile auto-resolve + 20K+ chars |
| cloakbrowser-fetch | scrapingbee.com/blog/ | TLS bypass + 140+ links |
| scrapling-bulk-fetch | [example.com, httpbin.org/get] | 双 URL status 200 |
| chrome-devtools-mcp | x.com/hashtag/... | 诊断证据 |
| chrome-cdp | fanbox.cc/@.../posts | 认证页面 visit + 帖子列表 |

---

### Source: `extension-api`

#### Requirement: 新引擎接入 artifact checklist

1. Contract Spec: `openspec/specs/<engine-id>-contract/spec.md`
2. Registry Entry in `configs/engine-registry.json`
3. Engine-Contracts Integration
4. Strategy Integration (if applicable)
5. Decision Record: `docs/decisions/YYYY-MM-DD-<engine-id>-addition.md`
6. Smoke-Check Evidence

#### Requirement: 引擎命名规范

Kebab-case, `<tool-prefix>-<capability>`, unique, no reuse of superseded identifiers.

#### Requirement: 接入验证要求

Draft → Frozen requires: smoke-check passed, evidence recorded, contract reviewed, registry consistent, error matrix updated, strategy files updated.

---

## Part 2 — Individual Engine Contracts

### Source: `scrapling-get-contract` (type: `http`, rank: 1)

#### Input: `url` (required), `extraction_type` (markdown|text|html), `main_content_only`, `css_selector`, `impersonate`, `timeout` (30s), `retries` (3), `headers`, `cookies`, `proxy`. Single-shot mode. Public pages by default.
#### Output: Extracted content in requested format, metadata (title, final URL, timestamp), images as `![alt](url)` preserving DOM order, main content targets `<body>`.
#### Error: `network`, `timeout`, `block`, `parse`. Block → escalate to stealthy-fetch or devtools-mcp.
#### Smoke-check: WeChat public article — title + body + inline images.

---

### Source: `obscura-fetch-contract` (type: `cdp_lightweight`, rank: 2)

#### Input: `url`, `wait_until` (load|domcontentloaded|networkidle0|networkidle2), `selector`, `timeout` (30s), `stealth` (false), `extract_format` (html|text|markdown), `eval`, `user_agent`, `proxy`, `obey_robots` (false).
#### Output: `url`, `title`, `content`, `content_type`, `status_code`, `redirect_chain`, `links`, `timing_ms`, `network_events`. Markdown supports h1-h6, links, images, tables.
#### Performance: ≤15MB idle RSS, ≤50MB peak, ≤200ms startup, ≤3s SPA load, ≤80MB binary.
#### CDP compatibility: Target, Page, Runtime, DOM, Network, Fetch, Storage, Input, LP.getMarkdown domains.
#### Error: `network`, `timeout`, `block`, `parse`, `browser`.
#### Known Limitations: Heavy JS animations may hang, SPA hydration may fail, stealth mode experimental (use cloakbrowser-fetch instead), macOS arm64 build may fail with stealth features.
#### Smoke-check: Hacker News — title "Hacker News" + ≥20 entries + ≤5000ms.

---

### Source: `scrapling-fetch-contract` (type: `playwright`, rank: 3)

#### Input: `url`, `headless` (true), `real_chrome`, `cdp_url`, `disable_resources`, `wait` (ms), `wait_selector`, `wait_selector_state`, `network_idle`, `extraction_type`, `css_selector`, `main_content_only`, `useragent`, `timezone_id`, `locale`, `extra_headers`, `timeout` (30s), `proxy`, `cookies`, `session_id`. Persistent session via `session_id`.
#### Output: Post-render content after JS execution and wait conditions, metadata, images as Markdown, SPA content detection via wait strategy.
#### Error: `network`, `timeout`, `block`, `parse`, `browser`. Browser error → retry with `real_chrome=true` or escalate to devtools-mcp.
#### Smoke-check: Twitter public tweet — author + text + media via `network_idle`.

---

### Source: `scrapling-bulk-fetch-contract` (type: `playwright_bulk`, rank: 4)

#### Input: `urls` array (required), `extraction_type`, `css_selector`, `main_content_only`, `session_id`, browser parameters.
#### Output: Per-URL entries with `status`, `content` ([extracted_body_string, ""]), `url`. Partial failure supported.
#### Error: `timeout` (all URLs), `network` (partial), `browser` (crash), `block`, `parse` (per-URL).
#### Smoke-check: [example.com, httpbin.org/get] — dual status 200.

---

### Source: `cloakbrowser-fetch-contract` (type: `playwright_stealth`, rank: 4)

#### Input: `url`, `headless` (true), `wait_until` (domcontentloaded), `timeout` (30s), `proxy`, `stealth_args` (true), `humanize` (false), `fingerprint_seed`, `timezone`, `locale`, `geoip` (false), `persistent_context`, `extra_args`.
#### Stealth: 57 C++ patches for Canvas, WebGL, Audio, Font, GPU, Screen, WebRTC, Network timing, Automation signal, CDP input. Fingerprint seed management. Platform-aware profiles (macOS native, Linux→Windows spoof).
#### Output: Rendered HTML with stealth. `navigator.webdriver=false`, `navigator.plugins.length ≥ 5`.
#### Error: `network`, `timeout`, `block`, `browser`, `binary`, `license`, `challenge`.
#### Smoke-check: wiki.supercombo.gg — CF Turnstile auto-resolve + 20K+ chars; scrapingbee.com/blog — TLS bypass + 140+ links.

---

### Source: `scrapling-stealthy-fetch-contract` (status: **superseded** by `cloakbrowser-fetch`)

#### Input: All `scrapling-fetch` params plus `solve_cloudflare`, `hide_canvas`, `block_webrtc`, `allow_webgl`, `additional_args`.
#### Output: Same as fetch + metadata about challenge bypass.
#### Error: Same as fetch plus `challenge` category.
#### Note: Retained for historical reference. Active replacement: `cloakbrowser-fetch-contract`.

---

### Source: `chrome-devtools-mcp-contract` (type: `cdp_managed`, rank: 5)

#### Input: Navigation (`url`, `timeout`, `initScript`), diagnostics (`take_snapshot`, `take_screenshot`, `list_network_requests`, `list_console_messages`, `performance_start_trace`, `evaluate_script`), interaction (`click`, `fill`, `hover`, etc.), wait (`wait_for`).
#### Output: Accessibility tree snapshot, screenshot image, network request list, console message list, performance trace with Core Web Vitals, script evaluation result. **Diagnostic evidence, NOT content extraction.**
#### Error: `connection`, `navigation`, `selector`, `evaluation`, `page_limit`.
#### Smoke-check: x.com hashtag page — diagnostic evidence including login redirect detection.

---

### Source: `chrome-cdp-contract` (type: `cdp_live`, rank: 6)

#### Input: Live Chrome with remote debugging already running. User-approved target page required. Navigation, DOM queries, cookie extraction. 20-minute inactivity auto-exit. Fallback only after Scrapling-first attempted.
#### Output: Page title, URL, text content, media URLs, cookie metadata, session-state metadata, download operation output.
#### Error: `connection`, `auth_redirect`, `session_loss`, `rate_limit`, `extraction`, `permissions`. Auth redirect → stop immediately. Rate limit → stop + 3h cooldown.
#### Smoke-check: fanbox.cc authenticated posts + x.com authenticated search session continuity.
