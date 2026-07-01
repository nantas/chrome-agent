# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-convert-phase`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: convert change Stage 3 drift 1-3：CDP 路径切到 selectolax 内核 + 镜像等价测试

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: cdp-path-uses-shared-kernel

The CDP execution path (`scripts/pipeline/pipeline/phases/convert_html.py`) SHALL use `scripts.lib.extraction.converter.convert_html_to_markdown()` with `wiki_domain=""` (empty string) for generic HTML-to-Markdown conversion. It SHALL NOT import or use `scripts.lib.extraction.html_to_markdown`.

The shared kernel (`scripts.lib.extraction.converter`) SHALL accept an empty `wiki_domain` and skip wiki-specific link handling (absolutization, `/wiki/` path resolution) when `wiki_domain` is empty.

#### Scenario: cdp-path-calls-converter
- **WHEN** `convert_html.py` converts an HTML page from the chrome-cdp cache
- **THEN** the conversion SHALL go through `HtmlToMarkdownConverter(wiki_domain="")`
- **AND** SHALL NOT go through `html_to_markdown()` (regex-based)
- **AND** no wiki-specific link resolution (no `/wiki/` prefixing, no host-based absolutization) SHALL be applied

#### Scenario: kernel-rejects-non-string-domain
- **WHEN** `HtmlToMarkdownConverter.__init__` receives `wiki_domain=None`
- **THEN** it SHALL raise `TypeError`
- **AND** `convert_html_to_markdown()` SHALL accept `wiki_domain=""` as a valid generic HTML signal

#### Scenario: cdp-converted-output-equivalent-to-pipeline
- **WHEN** the same HTML sample is converted via pipeline path (`convert.py` → `HtmlToMarkdownConverter`)
- **AND** also converted via CDP path (`convert_html.py` → `HtmlToMarkdownConverter`)
- **THEN** the two `.md` outputs SHALL be identical

### Requirement: mirror-equivalence-golden-snapshot

A golden snapshot test SHALL exist that verifies convert output equivalence across B-axis execution paths. The test SHALL select an existing cached page HTML, pass it through both the pipeline convert path and the explore convert path, and assert the resulting Markdown is byte-identical.

#### Scenario: golden-snapshot-diff-is-zero
- **WHEN** the golden snapshot test runs in CI
- **AND** no convert logic has been modified
- **THEN** the diff between pipeline and explore convert output SHALL be empty

#### Scenario: golden-snapshot-fails-on-drift
- **WHEN** a future change introduces different behavior between pipeline and explore convert paths
- **THEN** the golden snapshot test SHALL fail
- **AND** the failure SHALL indicate which path diverged

## MODIFIED Requirements

_None — existing `conversion-output-format` and `incremental-page-write` requirements unchanged._

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
