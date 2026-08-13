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
│   ├── 入口: convert_page_full() — 4 步编排
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

A golden snapshot test SHALL verify that explore, pipeline, and pipeline(cdp) convert paths produce byte-identical Markdown from the same HTML input as the shared kernel (`convert_page_full`). The proof SHALL be a self-contained test with an embedded HTML fixture that exercises the recurring troublemakers (MediaWiki `/wiki/` links, rowspan/colspan tables, pipe characters in table cells, literal asterisks, parenthesized/apostrophe page titles, image+link concatenation, tooltip link pairs) so it never skips due to a missing external cache.

Mirrors add declared path-specific wrapping around the conversion core (config-driven post-ops in explore; YAML frontmatter + title heading in pipeline). The snapshot SHALL strip that declared wrapping before comparison, so the assertion targets the conversion core, not the wrapping.

The proof SHALL live in `tests/test_convert_equivalence.py`.

#### Scenario: cv3-explore-mirror-matches-kernel
- **WHEN** the embedded fixture is converted via explore (`sample_converter._apply_extraction` with the minimal ruleset) and via the kernel (`convert_page_full` with the same ruleset)
- **THEN** the two outputs SHALL be byte-identical

#### Scenario: cv4-pipeline-mirror-matches-kernel
- **WHEN** the embedded fixture is converted via the pipeline entry (`convert_single_page`) and via the kernel (`convert_page_full`)
- **THEN** the pipeline output, after stripping the declared YAML frontmatter + conditional title heading, SHALL be byte-identical to the kernel output

#### Scenario: cv5-generic-mirror-matches-kernel
- **WHEN** the embedded fixture is converted via the generic CDP path (`convert_html_to_markdown` with `wiki_domain=""`) and via the kernel invoked with empty rules (`convert_page_full` with `{}`)
- **THEN** the two outputs SHALL be byte-identical

#### Scenario: fixture-discriminates-preprocessing
- **WHEN** a mirror skips `preprocess_html` (e.g. a future regression in the pipeline path)
- **THEN** the test SHALL fail, because the embedded fixture contains a `#catlinks` element removed only by `preprocess_html` (under `cleanup: ["strip_footer"]`), not by the converter kernel

#### Scenario: test-never-skips
- **WHEN** the test runs on a fresh checkout without `.cache/`
- **THEN** it SHALL execute (not skip), because the HTML fixture is embedded in the test file

### Requirement: standalone-orchestrator-delegates-to-cv4-mirror

The standalone orchestrator (`standalone.py::fetch_and_convert`) SHALL be a thin shell variant of the CV4 mirror (`convert.py::convert_single_page`). For HTML-mode conversion it SHALL construct a `raw` content dict (`{"html", "images", "content_acquisition": "html_rendered"}`) and a `page_info` dict, then delegate to `convert_single_page` for the full conversion core (preprocess → convert → frontmatter → card stats), rather than reimplementing that orchestration. This guarantees the three standalone-backed subcommands (`fetch`, `reprocess`, `reconvert` via source_url re-fetch) produce output byte-equivalent to the `pipeline` subcommand for the same page and config.

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

The convert shared kernel (`lib/extraction/converter.py`) SHALL expose public entry points with declared purposes: (1) `HtmlToMarkdownConverter` class — implementation layer, the only entry carrying instance state (`build_link_index`, `source_dir`-aware rendering), used directly by CV4 for link-index resolution; (2) `convert_html_to_markdown()` function — stateless convenience entry, used by CV5 and `test_runner.py`; (3) `convert_page_full()` function — the declared single full-page orchestration kernel entry (CV1), used by CV3; (4) `apply_post_conversion_ops(md, extraction_rules)` function — the single source of truth for config-driven markdown-layer post-conversion transforms (text normalization, url conversion, youtube cleanup, escape-artifact cleanup, and the markdown-layer cleanup ops `strip_empty_parens`/`fix_separators`/`normalize_internal`).

`convert_page_full()` SHALL run `apply_post_conversion_ops()` as a declared step after infobox prepend (the full pipeline is now: extract infobox → preprocess HTML → convert to Markdown → prepend infobox → apply post-conversion ops). CV3 (`sample_converter._apply_extraction`) obtains post-ops automatically via `convert_page_full()` and SHALL NOT inline any post-conversion transform logic (honors `00-target-architecture.md` invariant I2: a mirror orchestrates, contains no transform logic). CV4 (`pipeline convert _process_html_page`) uses the class entry directly (for link-index state) and SHALL call `apply_post_conversion_ops()` explicitly after `convert_body()`, so that both B-axis execution paths honor the identical set of config-driven markdown post-ops for the same strategy.

A mirror MAY use the class entry directly when it needs instance state; this is not a violation of the single-kernel contract provided an equivalence proof covers the path. `tests/test_convert_equivalence.py` SHALL remain the proof for CV3/CV4/CV5 against `convert_page_full`, and SHALL include at least one fixture that enables the divergent config keys (`text_normalization`, `url_conversion`, `youtube_cleanup`, and at least one markdown-layer `cleanup` op) so that equivalence is bound for real strategies, not only for a fixture where the post-ops are inert.

#### Scenario: cv4-class-entry-is-declared-and-proven
- **WHEN** a future review inspects CV4's direct use of `HtmlToMarkdownConverter`
- **THEN** `00-target-architecture.md` §3.1 SHALL declare it as the class entry (intentional, for link-index state), and `tests/test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel` SHALL prove equivalence to the kernel

#### Scenario: post-ops-have-one-implementation-in-kernel
- **WHEN** any code path (CV3 explore, CV4 pipeline, future CV5 variant) needs to apply config-driven markdown-layer post-conversion transforms (text normalization, url conversion, youtube cleanup, escape-artifact cleanup, markdown-layer cleanup ops)
- **THEN** it SHALL call `convert.apply_post_conversion_ops(md, extraction_rules)` from the kernel
- **AND** SHALL NOT inline a parallel implementation of those transforms
- **AND** `sample_converter._apply_extraction` SHALL contain no markdown-transform logic beyond delegating to `convert_page_full()` (invariant I2 honored)

#### Scenario: convert-page-full-includes-post-op-step
- **WHEN** `convert_page_full(html, extraction_rules)` is invoked
- **THEN** the returned Markdown SHALL have `apply_post_conversion_ops` applied as the final step (after infobox prepend)
- **AND** for a strategy with no divergent keys configured, the output SHALL be byte-identical to the pre-change kernel output (post-ops are config-gated no-ops)

#### Scenario: cv3-and-cv4-honor-same-post-ops-for-real-strategies
- **WHEN** a strategy configures any of `text_normalization` / `url_conversion` / `youtube_cleanup` / markdown-layer `cleanup` ops (`strip_empty_parens`, `fix_separators`, `normalize_internal`)
- **THEN** both CV3 (`convert_page_full`) and CV4 (`convert_body` + explicit `apply_post_conversion_ops`) SHALL apply the identical transform set to the converted Markdown
- **AND** `tests/test_convert_equivalence.py` SHALL assert CV3 ≡ CV4 ≡ kernel for a fixture that enables these keys (not only for an inert fixture)

#### Scenario: escape-artifact-cleanup-is-uniform-safety-net
- **WHEN** the converted Markdown contains backslash-escape artifacts (e.g. `\*\*\*`, `\*+`)
- **THEN** `apply_post_conversion_ops` SHALL clean them unconditionally (not config-gated)
- **AND** because both CV3 and CV4 route through `apply_post_conversion_ops`, the cleanup SHALL be uniform across execution paths; the prior "CV3-only unconditional cleanup as divergence canary" is subsumed by the byte-equality equivalence proof

