# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 用户确认 P-1～P-4 合并修复
- 变更类型: modified（为既有能力增加 crawl 契约）
- 用户确认摘要: crawl 接入共享内核；已匹配策略转换失败时明确失败，禁止通用降级。

## 规范真源声明

本文件是本 change 的 convert 行为真源；design/tasks/verification SHALL 引用本文件，项目页面不替代 delta。

## ADDED Requirements

### Requirement: crawl-strategy-html-shared-conversion
Crawl SHALL separate HTML acquisition from Markdown conversion and delegate conversion for every matched strategy to `convert_page_full` with that strategy's validated extraction rules. Absent extraction SHALL mean empty rules; malformed rules SHALL fail. The caller SHALL reuse the admitted matched strategy rather than independently look up a domain file. The same contract SHALL cover ordinary traversal, sitemap manifest extraction, prefetched/parallel HTML and cache-only conversion, regardless of the acquisition engine. Acquisition admission SHALL precede conversion. Engine environments SHALL only acquire HTML; shared conversion SHALL execute in the application Python environment.

#### Scenario: cloakbrowser-strategy-body
- **WHEN** CloakBrowser supplies a full page containing skin navigation and a strategy-selected body
- **THEN** crawl SHALL render the strategy-selected body through the shared entry, without skin navigation or selector flags sent to CloakBrowser.

#### Scenario: selector-is-not-full-extraction
- **WHEN** the strategy declares cleanup, infobox or post-ops and the HTML contains nested tables
- **THEN** crawl SHALL execute all shared full-page steps exactly once and preserve the shared kernel's table structure, rather than using selector-only Scrapling conversion.

#### Scenario: all-html-entry-paths
- **WHEN** identical admitted HTML, rules and rendering context enter any supported crawl HTML branch, including cached --phase convert
- **THEN** core Markdown SHALL be byte-identical to convert_page_full output; known cached/prefetched bytes SHALL be reused without a new fetch for conversion.

#### Scenario: absent-or-invalid-extraction
- **WHEN** a strategy has no extraction block
- **THEN** crawl SHALL use the shared entry with empty rules, and SHALL NOT treat the strategy as unmatched.
- **AND** a present invalid extraction block SHALL instead report a configuration failure.

#### Scenario: no-strategy-compatibility
- **WHEN** no strategy is matched and an existing generic conversion route is available
- **THEN** that route SHALL retain its existing behavior; the matched-strategy contract SHALL NOT synthesize a strategy.

### Requirement: crawl-strategy-conversion-fails-closed
Once a matched-strategy conversion is selected, dependency, bridge, configuration or conversion failure SHALL mark that exact URL failed with a reason and available evidence. It SHALL NOT fall back to Scrapling Markdown, JS regex conversion or whole-page success. No failed page SHALL enter current successful artifacts or merged output, including via a stale Markdown file from an earlier attempt. Mixed outcomes SHALL preserve exact URL identities rather than infer successes/failures from counts; all-failed conversion SHALL NOT report success.

#### Scenario: bridge-failure-with-stale-output
- **WHEN** conversion fails and an old destination Markdown file exists
- **THEN** the URL SHALL remain failed, old content SHALL NOT enter current output/merge, and a diagnostic reason SHALL be retained.

#### Scenario: prefetched-conversion-failure
- **WHEN** conversion of prefetched HTML for a matched strategy fails
- **THEN** crawl SHALL record failure without invoking its generic conversion fallback.

#### Scenario: interleaved-cache-results
- **WHEN** cache conversion succeeds for A and C but fails for B
- **THEN** success entries SHALL identify A and C, failure SHALL identify B, and assembly SHALL include only A and C.

### Requirement: crawl-mirror-equivalence-proof
Tests SHALL exercise real crawl orchestration and its application bridge, isolating only acquisition/external process boundaries where necessary. Self-contained fixtures SHALL compare core bytes against the shared entry before crawl link relativization/merge and separately verify those declared outer transforms. Tests SHALL NOT depend on local outputs, untracked strategies or network availability.

#### Scenario: nested-table-and-cleanup-canary
- **WHEN** a fixture has skin text outside the body, configured removable text, enabled infobox and nested table data
- **THEN** every covered crawl branch SHALL match shared output, retain the infobox once and preserve table data; bypassing shared preprocessing SHALL fail the proof.

#### Scenario: wrapper-aware-dd2-replay
- **WHEN** the six DD2 diagnostic samples are replayed during verification
- **THEN** comparison SHALL distinguish core conversion from declared title/source/trailing-newline wrappers and crawl link transforms, and SHALL check images, headings, links and table structure.
