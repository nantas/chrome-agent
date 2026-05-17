# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: 策略文件的 `api.platform` 字段获得完整的管线消费链路

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: api-platform-consumed-by-engine-selection

The strategy's `api.platform` field SHALL be consumed by the engine selection layer (`selectFetcher()` and `main.py`) to determine the content retrieval engine.

#### Scenario: engine-selection-reads-api-platform
- **WHEN** `selectFetcher()` evaluates the strategy
- **THEN** it SHALL read `strategy.document.api.platform`
- **THEN** a value of `"mediawiki"` or `"mediawiki-fandom"` SHALL trigger `"mediawiki-api"` engine selection
- **THEN** the value SHALL NOT be read and discarded without effect

#### Scenario: no-action-when-no-api
- **WHEN** a strategy has no `api` block or no `api.platform` field
- **THEN** the engine selection SHALL continue with scrapling-based evaluation
- **THEN** no error or warning SHALL be raised

### Requirement: rate-limit-api-engine-priority-update

The `rate-limit-api` anti-crawl strategy (`sites/anti-crawl/rate-limit-api.md`) SHALL list `mediawiki-api` as the highest-priority engine for MediaWiki sites.

#### Scenario: engine-priority-lists-api-first
- **WHEN** the `rate-limit-api` anti-crawl strategy is loaded
- **THEN** `engine_priority` SHALL include an entry with `engine: "mediawiki-api"` and `rank: 0`
- **THEN** the existing `scrapling-fetch` entry SHALL be demoted to `rank: 1`

#### Scenario: api-engine-ranked-above-scrapling
- **WHEN** the engine priority list is evaluated for a MediaWiki site with rate limiting
- **THEN** `mediawiki-api` SHALL be considered before `scrapling-fetch`
- **THEN** scrapling-based engines SHALL only be used as fallback when API is unavailable
