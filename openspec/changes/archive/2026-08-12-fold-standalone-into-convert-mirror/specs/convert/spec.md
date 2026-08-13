# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 已确认 capabilities（用户确认「合并，仅 convert」）
- 变更类型: `modified`
- 用户确认摘要: C5（standalone 折叠）+ C3（三层接口声明）合并为单一 change；仅 convert 一个能力，Modified

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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
- **THEN** it SHALL continue routing through `convert_wikitext_to_markdown` unchanged (out of scope for this change)

### Requirement: convert-kernel-three-layer-interface

The convert shared kernel (`lib/extraction/converter.py`) exposes three public entry points, each with a declared purpose. The layers are intentional, not drift:

1. `HtmlToMarkdownConverter` (class) — implementation layer; the only entry that carries instance state (`build_link_index`, `source_dir`-aware rendering). Used directly by CV4 (`convert.py`) because pipeline conversion needs link-index state and source-directory context.
2. `convert_html_to_markdown(html, wiki_domain, extraction_config)` (function) — stateless convenience entry; constructs a converter and calls `convert_body`. Used by CV5 (CDP generic path) and `test_runner.py`.
3. `convert_page_full(html, extraction_rules)` (function) — the declared single full-page orchestration kernel entry (infobox → preprocess → convert → prepend). Used by CV3 (explore `sample_converter`) and declared as CV1.

A mirror MAY use the class entry directly when it needs instance state; this is not a violation of the single-kernel contract provided an equivalence proof covers the path. `tests/test_convert_equivalence.py` SHALL remain the proof for CV3/CV4/CV5 against `convert_page_full`.

#### Scenario: cv4-class-entry-is-declared-and-proven
- **WHEN** a future review inspects CV4's direct use of `HtmlToMarkdownConverter`
- **THEN** `00-target-architecture.md` §3.1 SHALL declare it as the class entry (intentional, for link-index state), and `tests/test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel` SHALL prove equivalence to the kernel
