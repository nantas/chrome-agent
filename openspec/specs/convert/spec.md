# Specification: convert

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

## ADDED Requirements

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

The convert shared kernel (`lib/extraction/converter.py`) exposes three public entry points, each with a declared purpose: (1) `HtmlToMarkdownConverter` class — implementation layer, the only entry carrying instance state (`build_link_index`, `source_dir`-aware rendering), used directly by CV4; (2) `convert_html_to_markdown()` function — stateless convenience entry, used by CV5 and `test_runner.py`; (3) `convert_page_full()` function — the declared single full-page orchestration kernel entry, used by CV3 and declared as CV1. A mirror MAY use the class entry directly when it needs instance state; this is not a violation of the single-kernel contract provided an equivalence proof covers the path. `tests/test_convert_equivalence.py` SHALL remain the proof for CV3/CV4/CV5 against `convert_page_full`.

#### Scenario: cv4-class-entry-is-declared-and-proven
- **WHEN** a future review inspects CV4's direct use of `HtmlToMarkdownConverter`
- **THEN** `00-target-architecture.md` §3.1 SHALL declare it as the class entry (intentional, for link-index state), and `tests/test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel` SHALL prove equivalence to the kernel
