# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-converter-path-update`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 更新转换器架构文档中过时的文件路径引用

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: converter-path-in-docs

The document `docs/architecture/05-converter-architecture.md` SHALL reference the current file path for `HtmlToMarkdownConverter`.

The converter file path SHALL be updated from `scripts/pipeline/converters/html_to_markdown.py` to `scripts/lib/extraction/converter.py` in all references.

#### Scenario: module-inventory-updated

- **WHEN** reading the "Pipeline Converters" module inventory table (§2.2)
- **THEN** `html_to_markdown.py` SHALL be listed under `scripts/lib/extraction/` (not `scripts/pipeline/converters/`)
- **AND** a cross-reference SHALL be preserved for the `scripts/pipeline/converters/` directory (which now contains only fandom_html_to_markdown.py, card_stats.py, link_fixer.py, wikitext_to_md.py)

#### Scenario: converter-location-explanation-updated

- **WHEN** reading §2.3 "Design Decision: html_to_markdown.py Location"
- **THEN** the explanation SHALL reflect the current location in `scripts/lib/extraction/converter.py`
- **AND** the rationale (pipeline coupling, selectolax dependency, conversion vs extraction boundary) MAY be updated to match the actual state

#### Scenario: data-flow-diagram-updated

- **WHEN** viewing the "Data Flow Diagram" in §6
- **THEN** paths SHALL reference `scripts/lib/extraction/converter.py` where the converter module is the endpoint
- **AND** `pipeline/converters/html_to_markdown.py` SHALL NOT appear as an endpoint

#### Scenario: no-stale-paths

- **WHEN** the document is fully updated
- **THEN** `grep "pipeline/converters/html_to_markdown\.py" docs/architecture/05-converter-architecture.md` SHALL return zero matches
- **AND** `grep "scripts/lib/extraction/converter\.py" docs/architecture/05-converter-architecture.md` SHALL return matches where the converter is referenced
