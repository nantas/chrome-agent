# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认采用模型 C（Anti-Crawl 参数模板 + Site Strategy 引用并本地覆盖）；MediaWiki API pipeline 的 Phase B rate limit 章节更新为策略驱动，硬编码参数全部移除

## 规范真源声明

- 本文件是 `mediawiki-api-extraction` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Rate Limit 配置解析

The system SHALL resolve the final rate limit configuration for the MediaWiki API pipeline using a four-layer override priority before executing Phase B.

The four layers, from highest to lowest priority, SHALL be:
1. **CLI arguments**: `--concurrency`, `--batch-delay-ms`, `--max-retries`, `--backoff-multiplier`, `--jitter`
2. **Site Strategy local overrides**: `api.rate_limit.{concurrency, batch_delay_ms, retry.*}`
3. **Anti-Crawl tier template**: The `rate_limit_tiers` tier referenced by `api.rate_limit.tier` from the matching anti-crawl strategy
4. **Code safe defaults**: `concurrency=1`, `batch_delay_ms=1000`, `retry.max_retries=5`, `retry.initial_delay_sec=1.0`, `retry.backoff_multiplier=2.0`, `retry.max_delay_sec=60.0`, `retry.jitter=true`

The resolution SHALL be performed once at pipeline startup and the resulting configuration SHALL be passed to both the `ApiClient` and `Phase B` executor. The `ApiClient` SHALL use the retry/backoff/jitter parameters for its `_request` method. The Phase B executor SHALL use the `concurrency` and `batch_delay_ms` parameters for its `ThreadPoolExecutor` and batch delay insertion.

#### Scenario: 配置解析在 pipeline 启动时完成

- **WHEN** the pipeline starts with a valid site strategy and optional CLI arguments
- **THEN** the system SHALL resolve the final rate limit configuration before Phase A execution
- **AND** the resolved configuration SHALL be logged at INFO level
- **AND** the same configuration object SHALL be passed to both `ApiClient` and `run_phase_b`

#### Scenario: 无策略配置时使用安全默认值

- **WHEN** the pipeline runs against a site strategy with no `api.rate_limit` field and no CLI overrides
- **THEN** the system SHALL use code safe defaults for all rate limit parameters
- **AND** Phase B SHALL execute with `concurrency=1` and `batch_delay_ms=1000`

## MODIFIED Requirements

### Requirement: Phase B — 内容提取

The system SHALL extract content from each discovered page using the MediaWiki parse API.

For each page, the system SHALL:
1. Fetch wikitext via `action=parse&page={title}&prop=wikitext&format=json`
2. Extract infobox template parameters for YAML frontmatter
3. Convert wiki links to Markdown relative paths
4. Expand template calls to inline Markdown
5. Convert image references to absolute URL inline Markdown

Phase B SHALL support concurrent execution with **configurable concurrency** (resolved via the four-layer priority; safe default: 1).

After each batch of completed futures, the system SHALL insert a **configurable delay** (resolved via the four-layer priority; safe default: 1000ms) before submitting the next batch, to avoid triggering rate limits.

HTTP 429 responses SHALL trigger exponential backoff with **configurable retry parameters** (resolved via the four-layer priority; safe default: max 5 retries, initial delay 1.0s, multiplier 2.0, max delay 60.0s, with jitter). The backoff delay for each retry attempt SHALL be calculated as:

```
delay = min(initial_delay * (multiplier ^ attempt), max_delay)
if jitter: delay = delay * (1 + random(-0.2, +0.2))
```

#### Scenario: Wikitext fetch with strategy-driven rate limiting

- **WHEN** Phase B executes with resolved configuration `concurrency=1`, `batch_delay_ms=800`
- **THEN** at most 1 API request SHALL be in-flight simultaneously
- **AND** an 800ms delay SHALL be inserted between completed request batches
- **AND** failed fetches SHALL be retried with exponential backoff using the resolved retry parameters

#### Scenario: 429 触发指数退避

- **WHEN** an API request returns HTTP 429
- **AND** the resolved retry configuration is `max_retries=5`, `initial_delay_sec=1.0`, `backoff_multiplier=2.5`, `max_delay_sec=60.0`, `jitter=true`
- **THEN** the first retry SHALL wait approximately 1.0s (±20% jitter)
- **AND** the second retry SHALL wait approximately 2.5s (±20% jitter)
- **AND** the third retry SHALL wait approximately 6.25s (±20% jitter)
- **AND** delays SHALL cap at 60.0s regardless of further multiplications

#### Scenario: 并发配置生效

- **WHEN** the resolved concurrency is `5`
- **THEN** the `ThreadPoolExecutor` SHALL use `max_workers=5`
- **AND** up to 5 requests MAY be in-flight simultaneously
- **AND** the batch delay SHALL still be applied between completion checkpoints

#### Scenario: Partial failure during extraction

- **WHEN** some pages fail to fetch after all retries
- **THEN** the system SHALL continue processing remaining pages
- **AND** failed pages SHALL be recorded with their error reason in the crawl manifest
- **AND** the final result SHALL be `partial_success` if any pages succeeded

### Requirement: Concurrency and rate limiting

**（本 requirement 被以下更新后的完整版本替代，原 spec 中的版本作废）**

The system SHALL control concurrent API requests and inter-batch delays using the resolved rate limit configuration.

The Phase B executor SHALL:
1. Create a `ThreadPoolExecutor` with `max_workers` equal to the resolved `concurrency`
2. Submit page processing futures to the executor
3. After each completion checkpoint (or after each batch of completions), sleep for `batch_delay_ms / 1000.0` seconds before continuing
4. Ensure that the batch delay is applied regardless of whether the completed requests succeeded or failed

The `ApiClient` SHALL:
1. On HTTP 429 or `requests.RequestException`, enter the retry loop
2. Calculate the wait time using the resolved retry parameters
3. Apply jitter if `jitter` is true
4. Sleep for the calculated delay before the next attempt
5. Raise `RuntimeError` only after exhausting all retries

#### Scenario: 批次延迟在成功和失败后都生效

- **WHEN** a batch of 5 requests completes with 3 successes and 2 failures
- **THEN** the system SHALL wait for the resolved `batch_delay_ms` before processing the next batch
- **AND** the wait SHALL NOT be skipped because some requests failed

## REMOVED Requirements

（无）

## RENAMED Requirements

（无）
