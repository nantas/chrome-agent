# anti-crawl-schema — Spec

## Purpose

Defines the structured schema for anti-crawl strategy files: YAML frontmatter fields (id, protection_type, sites, detection, engine_sequence, success_signals, failure_signals), detection signal structure, engine sequence rules, default strategy definition, success/failure signals, registry.json index format, and governance constraints.

## Requirements

### Requirement: 目录存放结构

The system SHALL organize anti-crawl strategy files as flat files in `sites/anti-crawl/`, named by protection mechanism rather than target site.

Each anti-crawl file SHALL be:
- Located at `sites/anti-crawl/<mechanism-slug>.md` (kebab-case)
- Named by what protection it defeats, not which site it was discovered on
- Referenced by site strategies via the `anti_crawl_refs` field

#### Scenario: 按机制命名

- **WHEN** a Cloudflare Turnstile bypass strategy is created
- **THEN** it SHALL be named `cloudflare-turnstile.md` NOT `wiki.supercombo.gg.md`
- **AND** site strategies that use it SHALL add `cloudflare-turnstile` to their `anti_crawl_refs`

#### Scenario: 多站点共用

- **WHEN** a new site encounters login-wall-redirect behavior
- **THEN** it SHALL reference the existing `login-wall-redirect` anti-crawl file via `anti_crawl_refs`
- **AND** the `sites` field in `login-wall-redirect.md` SHALL be updated to include the new domain

### Requirement: YAML frontmatter 必填字段

The system SHALL define a mandatory YAML frontmatter schema for all anti-crawl strategy files.

Each anti-crawl file SHALL include the following fields in its YAML frontmatter:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (kebab-case), must match filename without `.md` |
| `protection_type` | enum | yes | From the controlled vocabulary (see Protection Type Vocabulary) |
| `sites` | string[] | yes | Domains where this protection has been observed; empty array for `default` |
| `detection` | object | yes | Detection signals that identify this protection (see Detection requirement) |
| `engine_sequence` | array | yes | Ordered list of engines to try, each with optional config (see Engine Sequence requirement) |
| `success_signals` | object | yes | Conditions indicating the protection was bypassed |
| `failure_signals` | object | yes | Conditions indicating the bypass attempt failed |

#### Scenario: 必填字段完整性

- **WHEN** an anti-crawl strategy file is created
- **THEN** it SHALL contain all required frontmatter fields
- **AND** `id` SHALL match the filename stem (e.g., `cloudflare-turnstile.md` → `id: cloudflare-turnstile`)

#### Scenario: 默认策略 sites 字段

- **WHEN** the default strategy is defined
- **THEN** `sites` SHALL be `[]` (empty array)
- **AND** `protection_type` SHALL be `none`

### Requirement: Protection Type 受控词汇表

The system SHALL define a controlled vocabulary for `protection_type`.

| Value | Description |
|-------|-------------|
| `none` | No protection; for the default strategy |
| `cloudflare_turnstile` | Cloudflare Turnstile challenge (checkbox or invisible) |
| `cloudflare_challenge` | Cloudflare JS challenge / interstitial (non-Turnstile) |
| `login_wall` | Redirects unauthenticated users to a login page |
| `cookie_auth` | Requires a specific session cookie for access |
| `rate_limit` | API or page rate limiting with cooldown period |
| `waf_generic` | Generic WAF blocking (non-Cloudflare) |
| `captcha` | Traditional CAPTCHA (reCAPTCHA, hCaptcha) |
| `ip_block` | IP-based blocking or geo-restriction |

New types SHALL be added via openspec change to this spec.

#### Scenario: 类型扩展

- **WHEN** a new protection mechanism is encountered that does not fit existing types
- **THEN** a new openspec change SHALL be created to add the type to this vocabulary
- **AND** the rationale for the new type SHALL be documented in the change's proposal

### Requirement: Detection 检测信号

The system SHALL define the `detection` object to describe signals that identify this protection mechanism.

The `detection` object SHALL contain:
- `http` (optional):
  - `status_codes`: array of HTTP status codes that suggest this protection (e.g., `[403]`)
- `page_content` (optional):
  - `titles`: array of page title patterns (exact match or prefix with `!@` for "does NOT contain", e.g., `"Just a moment"`, `"!@Just a moment"`)
  - `dom_markers`: array of CSS selectors or string literals present in the DOM (e.g., `"cf-turnstile"`, `"#challenge-form"`)
  - `url_patterns`: array of URL patterns that indicate redirect (e.g., `"/i/flow/login"`)
  - `has_content`: boolean indicating whether protected page loads meaningful body content (`true`) or only a protection shell (`false`)
- `network` (optional):
  - `empty_api_entities`: json path that should be empty when blocked (e.g., `"window.__INITIAL_STATE__.tweets.entities"`)

#### Scenario: Cloudflare Turnstile 检测

- **WHEN** a page returns 403 and contains "Just a moment" in its title
- **THEN** the `cloudflare-turnstile` anti-crawl strategy SHALL be a candidate

#### Scenario: 登录墙检测

- **WHEN** a page redirects to `/i/flow/login`
- **THEN** the `login-wall-redirect` anti-crawl strategy SHALL be a candidate
- **AND** `detection.page_content.has_content` SHOULD be `false`

### Requirement: Engine Sequence 引擎序列

The system SHALL define the `engine_sequence` field as an ordered list of engines to try for this protection, with optional per-engine configuration.

Each entry in `engine_sequence` SHALL contain:
- `engine`: engine identifier from the canonical engine list (must match values in `engine-contracts` spec: `scrapling-get`, `scrapling-fetch`, `scrapling-stealthy-fetch`, `chrome-devtools-mcp`, `chrome-cdp`)
- `config` (optional): engine-specific configuration override (e.g., `solve_cloudflare: true`, `network_idle: true`, `timeout: 60000`)
- `purpose` (optional): one of `primary`, `fallback`, `diagnostic`

#### Scenario: 引擎序列必须尊重 canonical chain

- **WHEN** an `engine_sequence` is defined
- **THEN** the engines SHALL appear in the same order as the canonical escalation chain: `scrapling-get` → `scrapling-fetch` → `scrapling-stealthy-fetch` → `chrome-devtools-mcp` → `chrome-cdp`
- **AND** entries MAY be skipped (e.g., start at `scrapling-stealthy-fetch` for Cloudflare) but SHALL NOT be reordered

#### Scenario: Cloudflare 引擎序列

- **WHEN** a Cloudflare Turnstile protection is detected
- **THEN** `engine_sequence` SHALL start with `scrapling-stealthy-fetch` (skipping `scrapling-get` and `scrapling-fetch` which are ineffective)
- **AND** `chrome-devtools-mcp` SHALL follow as a diagnostic fallback with `purpose: diagnostic`

### Requirement: Default 默认策略

The system SHALL define a `default.md` anti-crawl strategy that serves as the fallback when no known protection signals are detected and no site strategy matches.

`default.md` SHALL:
- Have `id: default` and `protection_type: none`
- Have `sites: []` (not bound to any specific domain)
- Encode the Scrapling-first escalation chain: `scrapling-get` → `scrapling-fetch` → `scrapling-stealthy-fetch` → `chrome-devtools-mcp` (diagnostic)
- Serve as the behavior for simple, unprotected pages with no known site strategy

#### Scenario: 无匹配策略

- **WHEN** an agent encounters a URL with no matching site strategy and no detection signals match any anti-crawl strategy
- **THEN** the agent SHALL use the `default` strategy
- **AND** the default strategy SHALL try engines in Scrapling-first escalation order

#### Scenario: 默认策略失败

- **WHEN** the default strategy exhausts all engines without success
- **THEN** the agent SHALL enter the analysis flow (diagnose → attempt → extract)
- **AND** the agent SHOULD consider creating a new site strategy and/or anti-crawl strategy for future reuse

### Requirement: Success/Failure Signals

The system SHALL define success and failure signal schemas for anti-crawl strategies.

`success_signals` SHALL contain conditions indicating the protection was bypassed:
- `page_content.has_content`: true (meaningful body content is present)
- `page_content.titles`: array of title patterns that confirm the real page loaded (e.g., `"!@Just a moment"` for Cloudflare)

`failure_signals` SHALL contain conditions indicating the bypass attempt failed:
- `page_content.dom_markers`: array of protection markers still present (e.g., `["cf-turnstile"]` for Cloudflare)
- `http.status_codes`: array of HTTP status codes indicating failure (e.g., `[403]`)

#### Scenario: Cloudflare 成功信号

- **WHEN** `stealthy-fetch` with `solve_cloudflare: true` returns a page
- **THEN** the page title SHALL NOT contain "Just a moment" or "请稍候"
- **AND** the page body SHALL contain the expected article content

#### Scenario: Cloudflare 失败信号

- **WHEN** after the engine sequence the page still shows "Just a moment" or cf-turnstile elements
- **THEN** the bypass SHALL be considered failed
- **AND** the agent SHALL escalate to the next engine in the sequence or enter analysis flow

### Requirement: Markdown body 推荐章节

The system SHALL recommend the following Markdown body sections for anti-crawl strategy files. These sections are advisory.

Recommended sections:
1. **Overview** — what this protection looks like, when it triggers
2. **Engine Sequence Rationale** — why this engine order, what each contributes
3. **Known Quirks** — edge cases, things that were tried and failed
4. **Evidence** — links to reports and validated runs

#### Scenario: Body 不重复 frontmatter

- **WHEN** an anti-crawl strategy body provides operational details
- **THEN** it SHALL NOT duplicate frontmatter fields
- **AND** it SHALL expand on the rationale and evidence behind the frontmatter configuration

### Requirement: Registry.json 索引格式

The system SHALL maintain a `sites/anti-crawl/registry.json` index for fast machine querying of anti-crawl strategies.

`registry.json` SHALL be an object with a single key `entries` containing an array of entry objects. Each entry SHALL contain:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Strategy identifier |
| `protection_type` | string | From controlled vocabulary |
| `sites` | string[] | Domains where observed |
| `detection_summary` | string | Human-readable summary of key detection signals |
| `primary_engine` | string | First engine in `engine_sequence` |
| `file` | string | Relative path to the anti-crawl file |

#### Scenario: Registry 可查询

- **WHEN** an agent encounters protection signals (status code, page title, DOM markers)
- **THEN** it SHALL be able to scan `registry.json` entries to find matching anti-crawl strategies

#### Scenario: Registry 一致性

- **WHEN** an anti-crawl file's YAML frontmatter is updated
- **THEN** `registry.json` SHALL be updated to reflect the changes
- **AND** if inconsistency is detected, the frontmatter SHALL be considered authoritative

### Requirement: 新增策略的治理约束

The system SHALL enforce through AGENTS.md that any new anti-crawl strategy creation SHALL include a registry.json update.

#### Scenario: 注册表更新

- **WHEN** a new anti-crawl `.md` file is added under `sites/anti-crawl/`
- **THEN** the operator SHALL add a corresponding entry to `sites/anti-crawl/registry.json`
- **AND** the operator SHALL verify that `id`, `protection_type`, and `file` fields are correct
- **AND** if the strategy was discovered from a site, that site's domain SHALL be added to the `sites` array in the new file
