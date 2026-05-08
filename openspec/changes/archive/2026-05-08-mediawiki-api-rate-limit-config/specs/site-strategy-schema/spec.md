# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-schema`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认采用模型 C（Anti-Crawl 参数模板 + Site Strategy 引用并本地覆盖）；site strategy 的 `api` 块新增 `rate_limit` 字段，支持引用 anti-crawl tier 并提供本地数值覆盖

## 规范真源声明

- 本文件是 `site-strategy-schema` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: API Rate Limit 配置

The system SHALL define an optional `rate_limit` object within the `api` block of the site strategy YAML frontmatter for sites that require configurable request frequency control during MediaWiki API extraction.

The `api.rate_limit` object SHALL contain:
- `tier` (optional, string): The identifier of the anti-crawl tier to use as the baseline template. When specified, the system SHALL resolve the tier from the anti-crawl strategy referenced in `anti_crawl_refs` that defines `rate_limit_tiers`. When absent or when no matching anti-crawl strategy provides tiers, the system SHALL fall back to code-level safe defaults.
- `concurrency` (optional, int): Override for the tier's `concurrency` value.
- `batch_delay_ms` (optional, int): Override for the tier's `batch_delay_ms` value.
- `retry` (optional, object): Override for the tier's retry configuration. Each sub-field is optional and overrides only the corresponding tier field:
  - `max_retries` (optional, int)
  - `initial_delay_sec` (optional, float)
  - `backoff_multiplier` (optional, float)
  - `max_delay_sec` (optional, float)
  - `jitter` (optional, boolean)

The system SHALL apply the following four-layer override priority when resolving the final rate limit configuration for the MediaWiki API pipeline:
1. **CLI arguments** (highest priority): `--concurrency`, `--batch-delay-ms`, `--max-retries`, etc.
2. **Site Strategy local overrides**: Non-null values in `api.rate_limit.{concurrency,batch_delay_ms,retry.*}`
3. **Anti-Crawl tier template**: The resolved tier from the matching anti-crawl strategy's `rate_limit_tiers`
4. **Code safe defaults** (lowest priority): `concurrency=1`, `batch_delay_ms=1000`, `retry.max_retries=5`, `retry.initial_delay_sec=1.0`, `retry.backoff_multiplier=2.0`, `retry.max_delay_sec=60.0`, `retry.jitter=true`

Local overrides in the site strategy SHALL be partial: only explicitly provided fields override the tier template; absent fields SHALL inherit from the tier. The `tier` field itself SHALL be optional.

#### Scenario: Site strategy 引用 anti-crawl tier 并本地覆盖

- **WHEN** a site strategy specifies:
  ```yaml
  anti_crawl_refs:
    - rate-limit-api
  api:
    rate_limit:
      tier: strict
      batch_delay_ms: 800
      retry:
        max_retries: 5
        backoff_multiplier: 2.5
  ```
- **AND** `rate-limit-api.md` defines:
  ```yaml
  rate_limit_tiers:
    strict:
      concurrency: 1
      batch_delay_ms: 500
      retry:
        max_retries: 3
        initial_delay_sec: 1.0
        backoff_multiplier: 2.0
        max_delay_sec: 60.0
        jitter: true
  ```
- **THEN** the resolved configuration SHALL be:
  - `concurrency: 1` (inherited from strict tier)
  - `batch_delay_ms: 800` (overridden by site strategy)
  - `retry.max_retries: 5` (overridden by site strategy)
  - `retry.initial_delay_sec: 1.0` (inherited from strict tier)
  - `retry.backoff_multiplier: 2.5` (overridden by site strategy)
  - `retry.max_delay_sec: 60.0` (inherited from strict tier)
  - `retry.jitter: true` (inherited from strict tier)

#### Scenario: Site strategy 不提供 rate_limit 时的安全默认值

- **WHEN** a site strategy has no `api.rate_limit` field
- **THEN** the MediaWiki API pipeline SHALL use code safe defaults:
  - `concurrency: 1`
  - `batch_delay_ms: 1000`
  - `retry.max_retries: 5`
  - `retry.initial_delay_sec: 1.0`
  - `retry.backoff_multiplier: 2.0`
  - `retry.max_delay_sec: 60.0`
  - `retry.jitter: true`

#### Scenario: CLI 参数覆盖一切

- **WHEN** the pipeline is invoked with `--concurrency 3 --batch-delay-ms 200`
- **AND** the site strategy has `api.rate_limit.concurrency: 1`
- **THEN** the final concurrency SHALL be `3`
- **AND** the final batch delay SHALL be `200`
- **AND** all other parameters SHALL still resolve through the four-layer priority for their respective fields

#### Scenario: 引用了 anti-crawl 但 tier 不存在

- **WHEN** a site strategy specifies `tier: very-strict`
- **AND** the referenced anti-crawl strategy does not define a `very-strict` tier
- **THEN** the system SHALL emit a warning
- **AND** fall back to code safe defaults for all rate limit parameters

## MODIFIED Requirements

### Requirement: API 提取配置

The system SHALL define an optional `api` object in the site strategy YAML frontmatter for sites that expose a CMS API for structured content extraction.

The `api` object SHALL contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform` | enum | yes | CMS platform identifier. Current valid value: `mediawiki` |
| `base_url` | string | no | API base URL. When absent, auto-detect via endpoint probing |
| `capabilities` | string[] | yes | List of supported API operations |
| `taxonomy` | object | no | Category-to-directory mapping rules |
| `filename` | object | no | Filename sanitization rules |
| `output` | object | no | Output configuration for Markdown generation |
| `rate_limit` | object | no | **(新增)** Request frequency control configuration (see API Rate Limit requirement) |

The `api` field SHALL remain optional. Its absence SHALL NOT invalidate the strategy file.

#### Scenario: 完整 api 块包含 rate_limit

- **WHEN** a site strategy for a MediaWiki site includes:
  ```yaml
  api:
    platform: mediawiki
    capabilities: [page_list, category_lookup, html_parse]
    rate_limit:
      tier: strict
      batch_delay_ms: 800
  ```
- **THEN** the strategy SHALL be valid and complete
- **AND** the MediaWiki API pipeline SHALL use the resolved rate limit configuration during Phase B

## REMOVED Requirements

（无）

## RENAMED Requirements

（无）
