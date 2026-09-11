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

## Requirements

#### Scenario: convert-page-full-includes-post-op-step
- **WHEN** `convert_page_full(html, extraction_rules)` returns
- **THEN** shared post-ops SHALL have run after infobox prepend, including unconditional escape cleanup and configured optional transforms.

#### Scenario: cv3-and-cv4-honor-same-post-ops-for-real-strategies
- **WHEN** rules enable text normalization, URL conversion, YouTube cleanup or Markdown cleanup
- **THEN** both CV3 and CV4 SHALL obtain the identical transforms through the shared full-page entry, as proven by an enabled-key fixture.
