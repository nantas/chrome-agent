# Strategy Domain: Schema — Merged Spec

> **Merged from**: `site-strategy-schema`, `anti-crawl-schema`, `pipeline-strategy-schema`
> **Purpose**: Complete schema reference for site strategy files (YAML frontmatter, structure, extraction, engine preference, API config), anti-crawl strategy files (detection signals, engine priority, rate limit tiers), and pipeline strategy schema (content_profile ID registry, extension protocol, validation rules).

---

## Part 1 — Source: `site-strategy-schema`

### Requirement: 目录存放结构

Strategy files at `sites/strategies/<domain>/strategy.md` with optional `_attachments/` directory.

### Requirement: YAML frontmatter 必填字段

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | yes | Primary domain |
| `description` | string | yes | One-sentence summary |
| `protection_level` | enum | yes | `low`/`medium`/`high`/`authenticated`/`variable` |
| `anti_crawl_refs` | string[] | yes | Anti-crawl strategy IDs; `[]` if none |
| `engine_preference` | object | no | `preferred` (string) + optional `reason` |
| `structure` | object | yes | Page hierarchy and connectivity |
| `extraction` | object | no | Selectors, image handling, cleanup rules |
| `backend` | string | no | Advisory backend family identifier |

### Requirement: Structure 页面层级与连接

`structure.pages[]` with: `id`, `label`, `url_pattern`, `url_example`, `type` (controlled vocab), `anti_crawl_refs` (per-page override), `engine_preference` (per-page override), `content_type`, `pagination`, `links_to`, `requires_auth`.

`entry_points`: array of page IDs.

### Requirement: Page Type 受控词汇表

| Value | Description |
|-------|-------------|
| `static_page` | Static HTML, no JS required |
| `static_article` | Static article detail page |
| `dynamic_list` | JS-rendered list |
| `dynamic_content` | JS-rendered content with interactive elements |
| `search_results` | Search/form-results page |
| `binary_file` | Direct file download |
| `auth_gate` | Authentication/login gate |

### Requirement: Engine Preference

`engine_preference.preferred` must match an engine `id` in registry. Can be file-level or per-page. Per-page overrides file-level. Fallback chain: per-page → file-level → anti-crawl → default_rank.

### Requirement: Pagination

`none`, `url_parameter`, `cursor_based`, `scroll_infinite`, `click_next`.

### Requirement: Extraction

`selectors` (map), `image_handling` (attribute/fallback/output_format), `cleanup` (array of rule IDs).

### Requirement: protection_level 受控词汇表

`low`, `medium`, `high`, `authenticated`, `variable`.

### Requirement: Registry.json 索引格式

`sites/strategies/registry.json` with `entries` array. Fields: `domain`, `description`, `protection_level`, `page_types`, `pagination`, `entry_points`, `anti_crawl_refs`, `file`, `backend`. Frontmatter is authoritative when inconsistent.

### Requirement: API 提取配置

Optional `api` object: `platform`, `base_url`, `capabilities`, `taxonomy`, `filename`, `output`, `rate_limit`.

### Requirement: API Capabilities 受控词汇表

`page_list`, `category_lookup`, `wikitext_parse`, `html_parse`.

### Requirement: API Rate Limit 配置

Four-layer override priority:
1. CLI arguments
2. Site Strategy local overrides
3. Anti-Crawl tier template
4. Code safe defaults

### Requirement: platform_variant 字段

`api.platform_variant`: `standard` (default), `fandom`, `wiki-gg`.

### Requirement: content_profile ID 引用完整性约束

All `api.content_profile` values must reference IDs in `_STRATEGY_REGISTRY` (located at `scripts/pipeline/pipeline/orchestrator.py`).

| Dimension | Valid IDs |
|-----------|----------|
| `discovery_strategy` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only`, `hybrid_wikitext_plus_rendered`, `html_rendered` |
| `link_resolver` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

---

## Part 2 — Source: `anti-crawl-schema`

### Requirement: 目录存放结构

Files at `sites/anti-crawl/<mechanism-slug>.md`, named by protection mechanism, not by site.

### Requirement: YAML frontmatter 必填字段

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Matches filename stem |
| `protection_type` | enum | yes | Controlled vocab |
| `sites` | string[] | yes | Domains where observed; `[]` for default |
| `detection` | object | yes | Detection signals |
| `engine_priority` | array | yes | Ordered engine list with `rank`, `engine`, optional `config` |
| `success_signals` | object | yes | Bypass confirmation conditions |
| `failure_signals` | object | yes | Bypass failure conditions |
| `rate_limit_tiers` | object | no | Rate-limit parameter templates |

### Requirement: Protection Type 受控词汇表

`none`, `cloudflare_turnstile`, `cloudflare_challenge`, `login_wall`, `cookie_auth`, `rate_limit`, `waf_generic`, `captcha`, `ip_block`.

### Requirement: Detection 检测信号

`detection` contains: `http.status_codes`, `page_content.titles/dom_markers/url_patterns/has_content`, `network.empty_api_entities`.

### Requirement: Engine Priority

Ordered list with `engine` (must exist in registry), `rank` (contiguous from 1), optional `config`. Must respect canonical chain order.

### Requirement: Rate Limit Tiers

Named tiers with `concurrency`, `batch_delay_ms`, `retry` (max_retries, initial_delay_sec, backoff_multiplier, max_delay_sec, jitter).

### Requirement: Default 默认策略

`default.md`: `id: default`, `protection_type: none`, `sites: []`. Scrapling-first chain: `scrapling-get` (1) → `scrapling-fetch` (2) → `scrapling-stealthy-fetch` (3) → `chrome-devtools-mcp` (4).

### Requirement: Registry.json 索引格式

`sites/anti-crawl/registry.json` with `entries` array. Fields: `id`, `protection_type`, `sites`, `detection_summary`, `primary_engine`, `file`.

---

## Part 3 — Source: `pipeline-strategy-schema`

### Requirement: 策略 ID 注册中心权威声明

`scripts/pipeline/pipeline/orchestrator.py` 中的 `_STRATEGY_REGISTRY` 是 pipeline 策略 ID 的唯一权威来源。

### Requirement: 策略文件 ID 引用完整性校验

Three validation paths:
1. **Pipeline startup**: Unknown ID → `EXIT_STRATEGY_ERROR` (hard-fail)
2. **bootstrap-strategy output**: Validate before writing
3. **Manual edits**: Agent must confirm registry exists

### Requirement: 扩展协议

Strict order: (1) Implement Strategy class → (2) Register in `_STRATEGY_REGISTRY` → (3) Reference in strategy file. Violating this order causes pipeline rejection.

### Requirement: Registry 变更约束

Delete/rename requires: scan all strategy files → update references → update templates. New IDs have no constraint.

### Requirement: homepage-exclude-categories-field

`api.homepage.exclude_categories: list[str]` — optional, for Phase discovery_homepage only. Absent = no filtering.

### Requirement: exclude-categories-backward-compatible

Existing strategies without `exclude_categories` remain fully valid and unchanged in behavior.
