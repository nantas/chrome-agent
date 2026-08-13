# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选定 Modified `convert`——在既有 `convert-kernel-three-layer-interface` requirement 上声明第 4 个公开入口 `apply_post_conversion_ops`（markdown 层 post-conversion 变换的唯一实现）+ 强化等价证明覆盖分歧 key。kernel 落点 lib/extraction/converter.py 属 convert 能力。explore spec 的 `apply-extraction-uses-shared-lib` 被动精简作为本 change 的后果在 design/tasks 记录，不单独开 capability。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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
