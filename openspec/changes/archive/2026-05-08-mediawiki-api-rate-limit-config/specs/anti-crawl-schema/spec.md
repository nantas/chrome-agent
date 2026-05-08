# Specification Delta

## Capability 对齐（已确认）

- Capability: `anti-crawl-schema`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认采用模型 C（Anti-Crawl 参数模板 + Site Strategy 引用并本地覆盖）；anti-crawl 策略负责定义分级化的 rate limit 参数模板，site strategy 引用 tier 并可本地覆盖

## 规范真源声明

- 本文件是 `anti-crawl-schema` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Rate Limit Tiers 参数模板

The system SHALL define an optional `rate_limit_tiers` object in the anti-crawl strategy YAML frontmatter for protection types that involve API or page rate limiting.

The `rate_limit_tiers` object SHALL contain one or more named tiers. Each tier SHALL be a key-value pair where the key is the tier identifier (kebab-case, e.g., `default`, `strict`, `very-strict`) and the value is a `rate_limit_config` object.

Each `rate_limit_config` object SHALL contain:
- `concurrency` (optional, int): Maximum number of concurrent in-flight requests. Default when absent: `1`.
- `batch_delay_ms` (optional, int): Milliseconds to wait between completed request batches. Default when absent: `500`.
- `retry` (optional, object):
  - `max_retries` (optional, int): Maximum retry attempts per failed request. Default when absent: `5`.
  - `initial_delay_sec` (optional, float): Initial backoff delay in seconds. Default when absent: `1.0`.
  - `backoff_multiplier` (optional, float): Exponential backoff multiplier. Default when absent: `2.0`.
  - `max_delay_sec` (optional, float): Maximum backoff delay cap in seconds. Default when absent: `60.0`.
  - `jitter` (optional, boolean): Whether to apply ±20% random jitter to each backoff delay. Default when absent: `true`.

The system SHALL NOT require `rate_limit_tiers` for protection types that do not involve rate limiting. Its absence SHALL NOT invalidate the anti-crawl strategy file.

When `rate_limit_tiers` is present, the system SHALL require at least one tier. The `default` tier SHOULD be provided as the baseline recommendation.

#### Scenario: Anti-crawl 策略定义 rate limit 模板

- **WHEN** an anti-crawl strategy for `rate_limit` protection type defines:
  ```yaml
  rate_limit_tiers:
    default:
      concurrency: 2
      batch_delay_ms: 500
      retry:
        max_retries: 3
        jitter: true
    strict:
      concurrency: 1
      batch_delay_ms: 800
      retry:
        max_retries: 5
        initial_delay_sec: 1.0
        backoff_multiplier: 2.5
        max_delay_sec: 60.0
        jitter: true
  ```
- **THEN** the system SHALL recognize both `default` and `strict` as valid tier identifiers
- **AND** each tier SHALL be resolvable to a complete `rate_limit_config` by applying field-level defaults for absent keys

#### Scenario: 非 rate limit 保护类型无需 tiers

- **WHEN** an anti-crawl strategy for `cloudflare_turnstile` does not define `rate_limit_tiers`
- **THEN** the strategy SHALL remain fully valid and complete
- **AND** the absence of `rate_limit_tiers` SHALL NOT trigger any validation error

#### Scenario: 缺失 default tier 仅触发警告

- **WHEN** an anti-crawl strategy defines `rate_limit_tiers` without a `default` tier
- **THEN** the system SHALL emit a warning recommending the addition of `default`
- **AND** the strategy SHALL still be accepted as valid

## MODIFIED Requirements

### Requirement: YAML frontmatter 必填字段

The system SHALL define a mandatory YAML frontmatter schema for all anti-crawl strategy files.

Each anti-crawl file SHALL include the following fields in its YAML frontmatter:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (kebab-case), must match filename without `.md` |
| `protection_type` | enum | yes | From the controlled vocabulary (see Protection Type Vocabulary) |
| `sites` | string[] | yes | Domains where this protection has been observed; empty array for `default` |
| `detection` | object | yes | Detection signals that identify this protection (see Detection requirement) |
| `engine_priority` | array | yes | Ordered list of engines to try, each with `rank`, `engine`, and optional `config` |
| `success_signals` | object | yes | Conditions indicating the protection was bypassed |
| `failure_signals` | object | yes | Conditions indicating the bypass attempt failed |
| `rate_limit_tiers` | object | no | **(新增)** Parameter templates for rate-limiting protection types (see Rate Limit Tiers requirement) |

#### Scenario: 完整 frontmatter 包含可选 rate_limit_tiers

- **WHEN** a rate-limit anti-crawl strategy file is created with all required fields plus `rate_limit_tiers`
- **THEN** validation SHALL pass
- **AND** `rate_limit_tiers` SHALL be available for downstream consumers (e.g., MediaWiki API pipeline) to resolve rate limit configuration

## REMOVED Requirements

（无）

## RENAMED Requirements

（无）
