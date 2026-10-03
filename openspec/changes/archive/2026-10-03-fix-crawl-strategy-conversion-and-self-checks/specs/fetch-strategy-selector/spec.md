# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-strategy-selector`
- 来源: `proposal.md` / P-1 共享转换路由的必要契约同步
- 变更类型: modified
- 用户确认摘要: 已匹配策略的 crawl 使用共享转换，失败不降级；独立 fetch 不扩大范围。

## 规范真源声明

本文件更新旧 selector-only 契约；design/tasks/verification SHALL 引用本文件。

## MODIFIED Requirements

### Requirement: strategy-content-selector-passthrough
For standalone `fetch` using Scrapling-family Markdown conversion, the system SHALL obtain a nonempty content selector from the matched strategy and pass it as `-s <selector>` rather than `--ai-targeted`. For crawl with a matched strategy, the system SHALL instead pass complete extraction rules to the shared HTML conversion entry as specified by `convert`; it SHALL NOT require Scrapling selector-only conversion for normal, prefetched or cached HTML. Selectors SHALL remain configuration-driven. MediaWiki acquisition SHALL retain its strategy-path context; acquisition SHALL NOT masquerade as Markdown conversion.

#### Scenario: fetch-with-strategy-content-selector
- **WHEN** standalone fetch uses Scrapling and the strategy declares a content selector
- **THEN** it SHALL send that selector as a discrete -s argument without --ai-targeted.

#### Scenario: crawl-with-strategy-content-selector
- **WHEN** crawl has a matched strategy and admitted HTML, including prefetched or cached HTML
- **THEN** the shared kernel SHALL consume the strategy selector and full extraction configuration, regardless of the original acquisition engine.

#### Scenario: selector-source-is-strategy-not-hardcoded
- **WHEN** a selector is applied by either path
- **THEN** its value SHALL come from strategy configuration, never a hardcoded site selector.

### Requirement: ai-targeted-fallback-when-no-selector
The existing Scrapling generic conversion route SHALL use --ai-targeted when it has no usable selector. This applies to standalone fetch and available unmatched-strategy generic crawl routes. Matched-strategy crawl SHALL use shared conversion even when its selector is absent or empty and SHALL NOT downgrade to generic conversion after failure.

#### Scenario: fetch-strategy-without-content-selector
- **WHEN** standalone fetch lacks a usable strategy content selector
- **THEN** the existing Scrapling --ai-targeted behavior SHALL remain.

#### Scenario: fetch-no-strategy-match
- **WHEN** standalone fetch matches no strategy
- **THEN** the existing Scrapling --ai-targeted behavior SHALL remain.

#### Scenario: crawl-matched-without-selector
- **WHEN** crawl has a matched strategy with no usable content selector
- **THEN** it SHALL use shared conversion with the remaining rules and shared default scope, not generic fallback.

### Requirement: shared-arg-builder-helper
The system SHALL retain one shared helper for acquisition/generic Scrapling argument construction where those arguments are needed. For mediawiki-api it SHALL preserve the strategy-path argument; for Scrapling generic conversion it SHALL return a configured selector or --ai-targeted; for CloakBrowser it SHALL return no Scrapling-only flags. Matched-strategy crawl shared conversion SHALL not be required to call this helper for Markdown rendering and SHALL pass extraction configuration through its application bridge instead. Callers SHALL NOT duplicate selector decision logic.

#### Scenario: helper-encapsulates-selector-decision
- **WHEN** standalone fetch or a generic route constructs Scrapling conversion arguments
- **THEN** it SHALL use the shared helper and discrete argv elements.

#### Scenario: helper-preserves-mediawiki-api-path
- **WHEN** a mediawiki-api acquisition needs its strategy context
- **THEN** the helper SHALL preserve strategy.path independent of content selector presence.

#### Scenario: cloakbrowser-acquires-only
- **WHEN** matched-strategy crawl acquires HTML via CloakBrowser
- **THEN** no -s or --ai-targeted flag SHALL be sent to that engine, and its HTML SHALL subsequently enter shared conversion.

### Requirement: selector-injection-safety
Where selectors are passed to Scrapling, the system SHALL use discrete argv elements without shell interpolation. Where extraction configuration crosses the application bridge, the system SHALL use structured serialization, not interpolate selector/config values into shell commands or executable Python source.

#### Scenario: selector-with-special-characters
- **WHEN** a selector contains quotes, brackets or spaces
- **THEN** it SHALL reach the selected consumer unchanged as data and SHALL NOT be interpreted by a shell.
