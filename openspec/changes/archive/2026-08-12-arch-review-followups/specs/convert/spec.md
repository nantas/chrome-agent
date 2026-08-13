# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 仅 convert（Modified）；fanbox 不归属任何能力，仅作 tasks 实现记录

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: mirror-equivalence-golden-snapshot

A golden snapshot test SHALL verify that explore, pipeline, and pipeline(cdp) convert paths produce byte-identical Markdown from the same HTML input as the shared kernel (`convert_page_full`). The proof SHALL be a self-contained test with an embedded HTML fixture that exercises the recurring troublemakers (MediaWiki `/wiki/` links, rowspan/colspan tables, pipe characters in table cells, literal asterisks, parenthesized/apostrophe page titles, image+link concatenation, tooltip link pairs) so it never skips due to a missing external cache.

Mirrors add declared path-specific wrapping around the conversion core (config-driven post-ops in explore; YAML frontmatter + title heading in pipeline). The snapshot SHALL strip that declared wrapping before comparison, so the assertion targets the conversion core, not the wrapping.

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
