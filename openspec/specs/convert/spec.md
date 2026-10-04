# Specification: convert

## Purpose

convert 能力负责把抓取到的原始内容（HTML / MediaWiki wikitext）转换为结构化 Markdown 产出。内核统一为 `lib/extraction/converter.py`（`HtmlToMarkdownConverter` class + `convert_html_to_markdown` / `convert_page_full` / `apply_post_conversion_ops` 函数入口），所有 B 轴执行路径（explore 采样、pipeline 生产、cdp 通用）通过镜像委托内核，禁止并行实现。策略差异经 `extraction` 配置驱动，不在代码层 hardcode。

## Capability 对齐

- Capability: `convert`
- 4 维坐标: `(capability=convert, execution_path=shared, strategy_variant=config_driven, input_format=html_mediawiki|html_generic)`
- 共享内核: `scripts/lib/extraction/converter.py` — `HtmlToMarkdownConverter` (selectolax)
- 变体机制: 站点特定行为通过 `strategy.md` 的 `extraction.cleanup` / `extraction.image_filtering` 配置驱动，**永不建 `*_html_to_markdown.py`**

## 架构声明

```
Convert 能力
├── kernel: converter.py (selectolax) — 唯一 HTML→MD 实现
│   ├── 入口: convert_page_full() — 5 步编排
│   ├── 入口: convert_html_to_markdown() — 独立转换
│   └── wiki_domain="" 支持 generic HTML
├── mirrors (薄壳，委托 kernel):
│   ├── pipeline: scripts/pipeline/pipeline/phases/convert.py
│   ├── pipeline(cdp): scripts/pipeline/pipeline/phases/convert_html.py
│   └── explore: scripts/explore/sample_converter.py → convert_page_full()
├── format_converter (D 轴 split):
│   └── wikitext_to_md.py — 输入格式=wikitext
└── 等价证明: tests/test_convert_equivalence.py (B 轴 golden snapshot)
```

## 已有行为规范

本 spec 的能力声明引用以下已有规范：

| 规范 | 内容 |
|------|------|
| `openspec/specs/pipeline-converters/spec.md` | HtmlToMarkdownConverter 表渲染、链接处理、块标签完整性 |
| `openspec/specs/pipeline-convert-phase/spec.md` | 增量写、跳过已转换、输出格式 |
| `openspec/specs/convert-target-conflict-detection/spec.md` | 转换目标冲突检测 |

冲突时以 `openspec/specs/pipeline-converters/spec.md` 为行为真源。
## Requirements
### Requirement: unify-html-converter-kernel

`scripts/lib/extraction/converter.py` (selectolax) SHALL be the sole HTML-to-Markdown implementation. No `*_html_to_markdown.py` files SHALL exist as forks or alternate implementations.

#### Scenario: only-one-converter-exists
- **WHEN** checking the codebase for HTML-to-MD implementations
- **THEN** only `converter.py` SHALL implement HTML→Markdown logic
- **AND** no `html_to_markdown.py` or `fandom_html_to_markdown.py` SHALL exist

### Requirement: mirror-equivalence-golden-snapshot
Self-contained tests in `tests/test_convert_equivalence.py` SHALL prove shared-core byte equivalence for matching HTML, rules and rendering context across CV3/CV4 and generic CV5. They SHALL strip only declared path wrappers (pipeline YAML/title/card-stat wrapping), never infobox or shared post-ops. Existing coverage of wiki links, row/col spans, pipe cells, asterisks, parenthesized/apostrophe titles, image/link adjacency, tooltip pairs and preprocessing-only footer removal SHALL remain. Tests SHALL enable real post-op keys and include an enabled infobox with unique field labels and values.

#### Scenario: cv3-explore-mirror-matches-kernel
- **WHEN** an embedded fixture is converted by explore and the shared entry with the same context
- **THEN** core Markdown SHALL be byte-identical.

#### Scenario: cv4-pipeline-mirror-matches-kernel
- **WHEN** the public `convert_single_page` entry and shared core convert the same fixture with matching context
- **THEN** core Markdown SHALL be byte-identical after removing only declared wrappers.

#### Scenario: cv5-generic-mirror-matches-kernel
- **WHEN** CV5 and the full-page entry convert generic HTML with empty rules and domain
- **THEN** outputs SHALL remain byte-identical.

#### Scenario: infobox-canary
- **WHEN** the fixture has `Seed Chance` and a unique value solely inside an enabled infobox
- **THEN** both production and shared output SHALL retain the field/value once under `## Infobox`, and a mirror omitting extraction/prepend SHALL fail.

#### Scenario: fixture-discriminates-preprocessing
- **WHEN** a mirror omits preprocessing of the fixture footer
- **THEN** equivalence SHALL fail.

#### Scenario: test-never-skips
- **WHEN** the checkout lacks external caches
- **THEN** all embedded-fixture proofs SHALL execute without network or skip.

### Requirement: standalone-orchestrator-delegates-to-cv4-mirror

The standalone orchestrator (`standalone.py::fetch_and_convert`) SHALL be a thin shell variant of the CV4 mirror (`convert.py::convert_single_page`). For HTML-mode conversion it SHALL construct a `raw` content dict (`{"html", "images", "content_acquisition": "html_rendered"}`) and a `page_info` dict, then delegate to `convert_single_page` for the full conversion core (convert_page_full 五步核心 → frontmatter → card stats), rather than reimplementing that orchestration. This guarantees the three standalone-backed subcommands (`fetch`, `reprocess`, `reconvert` via source_url re-fetch) produce output byte-equivalent to the `pipeline` subcommand for the same page and config.

#### Scenario: fetch-subcommand-applies-preprocess
- **WHEN** the `fetch` subcommand converts a page whose HTML contains an element removed by `preprocess_html` (e.g. `#catlinks` under `cleanup: ["strip_footer"]`) and `extraction_config` carries that cleanup op
- **THEN** the output Markdown SHALL NOT contain the removed element, matching the `pipeline` subcommand's behavior

#### Scenario: reconvert-without-source-url-uses-kernel-entry
- **WHEN** `reconvert_file` is called on a file whose frontmatter lacks `source_url` (the in-place body-reconvert branch)
- **THEN** it SHALL convert the body via the kernel full-orchestration entry `convert_page_full(body, {})`, not via direct `clean_html` + `convert` calls

#### Scenario: wikitext-mode-unchanged
- **WHEN** `fetch_and_convert` is called with `mode="wikitext"`
- **THEN** it SHALL continue routing through `convert_wikitext_to_markdown` unchanged

### Requirement: convert-kernel-three-layer-interface
The shared kernel SHALL retain four public entry points: the stateful `HtmlToMarkdownConverter` implementation class, the stateless `convert_html_to_markdown()` convenience function, the single full-page `convert_page_full()` orchestration function, and `apply_post_conversion_ops()` as the sole Markdown post-transform implementation. The full-page function SHALL remain compatible with existing two-argument callers and SHALL accept optional stateful converter and source-directory context.

The full-page sequence SHALL be extract infobox → preprocess HTML → convert body → prepend extracted infobox → apply post-ops exactly once. CV3 SHALL delegate to this entry. CV4 SHALL build its link-index/redirect state and supply that converter to the same entry, keeping frontmatter, heading and card-stat wrapping outside the core. It SHALL NOT independently repeat or omit those five steps. CV5 SHALL retain generic empty-domain behavior. Extraction rules supplied to the full-page entry and the converter SHALL agree; conflicting contexts SHALL be rejected.

The shared entry SHALL resolve infobox URL context from configured image base URL first, then supplied converter domain, then empty string. It SHALL preserve the supplied link index and source directory in both infobox and body link rendering. No caller-specific domain derivation SHALL duplicate this rule.

#### Scenario: cv4-stateful-full-page-entry
- **WHEN** CV4 converts a page with an existing link index and source directory
- **THEN** the full-page core SHALL use that state for both infobox and body without rebuilding an empty converter.

#### Scenario: post-ops-have-one-implementation-in-kernel
- **WHEN** any path applies text normalization, URL conversion, YouTube cleanup, escape cleanup or Markdown cleanup operations
- **THEN** it SHALL use `apply_post_conversion_ops`, once after infobox prepend in the full-page flow, without mirrored transform logic.

#### Scenario: legacy-two-argument-call
- **WHEN** `convert_page_full(html, rules)` is called without context
- **THEN** it SHALL retain stateless behavior, including configured base URL or generic empty-domain handling.

#### Scenario: contextual-infobox-links
- **WHEN** a page in `bosses/` links from its infobox to a manifest page in `endings/`
- **THEN** the link SHALL resolve relative to `bosses/`, using the same link index as body links.

#### Scenario: conflicting-converter-rules
- **WHEN** the provided converter has extraction rules inconsistent with the full-page request
- **THEN** conversion SHALL reject the conflicting context rather than apply two different rule sets.

#### Scenario: escape-artifact-cleanup-is-uniform-safety-net
- **WHEN** Markdown contains backslash-escape artifacts
- **THEN** the shared post-op safety net SHALL clean them uniformly, including when no optional normalization keys are configured.

#### Scenario: convert-page-full-includes-post-op-step
- **WHEN** `convert_page_full(html, extraction_rules)` returns
- **THEN** shared post-ops SHALL have run after infobox prepend, including unconditional escape cleanup and configured optional transforms.

#### Scenario: cv3-and-cv4-honor-same-post-ops-for-real-strategies
- **WHEN** rules enable text normalization, URL conversion, YouTube cleanup or Markdown cleanup
- **THEN** both CV3 and CV4 SHALL obtain the identical transforms through the shared full-page entry, as proven by an enabled-key fixture.


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

### Requirement: tooltip-normalization-preserves-dom
Tooltip normalization SHALL use structural DOM operations, unwrap only targeted tooltip/icon-size containers, and preserve unrelated elements and their nesting. It SHALL NOT globally delete closing span tags. Icon/text link merging SHALL retain image identity and visible text, merge only adjacent compatible links with the same destination, and leave different-target links distinct. Shared conversion SHALL retain block boundaries following ordinary, empty and nested spans without requiring site-specific nowrap cleanup.

#### Scenario: ordinary-span-before-block
- **WHEN** an ordinary or nowrap span containing an image precedes a heading and table
- **THEN** the heading SHALL remain a standalone heading and table rows SHALL remain separate, with or without the nowrap cleanup setting.

#### Scenario: nested-tooltip-and-links
- **WHEN** targeted tooltip containers coexist with nested ordinary spans and same-target icon/text links
- **THEN** only targeted wrappers SHALL be unwrapped and compatible links SHALL merge without losing image/text content or affecting surrounding block structure.

#### Scenario: distinct-link-targets
- **WHEN** adjacent icon and text links have different destinations
- **THEN** both destinations SHALL remain distinct.

### Requirement: wrapped-list-items-preserved
The configured unwrap_list_item_wrappers cleanup SHALL preserve list items hidden behind supported presentation wrappers, item order, images, and genuine nested list ownership. It SHALL handle arbitrary finite wrapper depth without a fixed three-pass limit, terminate by structurally removing wrappers, and leave ordinary inline content within list items intact. It SHALL NOT flatten child lists into parent siblings.

#### Scenario: wrapped-reward-list
- **WHEN** ul contains big wrapping li with reward images
- **THEN** full conversion SHALL retain every item and image once, as proven by the Shambler four-image regression.

#### Scenario: deep-wrappers-and-nested-numbering
- **WHEN** more than three presentation wrappers surround list items containing nested ordered lists
- **THEN** conversion SHALL retain outer order, inner numbering and hierarchy without duplication or loss.

### Requirement: configured-semantic-heading-pairs
Full conversion SHALL normalize explicitly configured pairs of a semantic heading containing hidden label text and its adjacent visible group label into one heading with the source heading level and source identifier, preserving visible label text/assets. Pair matching SHALL require the configured selectors, same parent and next element sibling, and equal nonempty normalized labels or an explicitly configured exact label_aliases correspondence. Visible label images and links SHALL be retained once. Unmatched or ambiguous pairs SHALL remain unchanged with diagnostic evidence; unrelated hidden content SHALL remain excluded. Repeated preprocessing SHALL NOT duplicate headings.

#### Scenario: enemies-group-headings
- **WHEN** DD2 declares matching hidden h3 and visible group-label pairs
- **THEN** the 14 DD2 and 3 Kingdoms group labels SHALL render once each as level-three headings, with following content in original order.

#### Scenario: mismatched-or-unconfigured-pair
- **WHEN** labels differ, selectors are absent, or the visible label is not the next element sibling
- **THEN** no heading pair SHALL be synthesized and no unrelated hidden element SHALL be exposed.

#### Scenario: repeat-normalization
- **WHEN** already normalized content is preprocessed again
- **THEN** heading count, order, identifiers and visible assets SHALL remain unchanged.

### Requirement: cleanup-workarounds-require-conversion-evidence
The change SHALL evaluate strip_empty_inline_tags, strip_empty_paragraphs and unwrap_nowrap_spans independently after the tooltip root fix, using real full conversion. A workaround without demonstrated independent benefit SHALL be removed from this site's active configuration; removal of a registered operation SHALL require a reference audit and compatibility decision. Retained operations SHALL preserve meaningful empty anchor identifiers and media. Structure-only cleanup tests SHALL NOT be treated as proof of conversion correctness.

#### Scenario: fallen-templar-ablation
- **WHEN** each combination of the three cleanup settings is evaluated after the root fix
- **THEN** the evidence SHALL identify which, if any, has independent benefit, and Skills SHALL remain a standalone heading without the nowrap workaround.

#### Scenario: anchor-and-media-safety
- **WHEN** cleanup encounters empty a elements with id/name or elements containing meaningful media
- **THEN** valid anchor information and media SHALL NOT be discarded as empty noise.

### Requirement: structural-fix-shared-entry-proof
Self-contained tests SHALL exercise convert_page_full through existing mirrors and assert content structure as well as byte equivalence under equal rules/context. Fixtures SHALL cover image and link retention, headings, lists and tables without external caches or network. DD2 replay SHALL remain supplemental evidence rather than a formal-suite dependency.

#### Scenario: mirror-and-loss-canaries
- **WHEN** the structural fixtures traverse shared, explore, pipeline and matched-strategy crawl paths
- **THEN** core outputs SHALL be equivalent after only declared wrappers, while deliberate item/image/heading loss SHALL fail independent assertions.
