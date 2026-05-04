# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-extraction-patterns`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，创建通用 MediaWiki 提取模式参考文档，覆盖 4 类噪音集群；balatrowiki.org 验证确认 79% 规则复用率，2 个差异点纳入通用文档。

## 规范真源声明

- 本文件是 `mediawiki-extraction-patterns` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 噪音分类学

The system SHALL define a taxonomy of MediaWiki content extraction noise organized into four clusters: navigation, template, link, and table.

#### Scenario: Navigation 噪音

- **WHEN** extracting content from a Weird Gloop MediaWiki page
- **THEN** the following elements SHALL be identified as navigation noise:
  - Footer sections (Tools, Privacy, About, Disclaimers)
  - Section edit links (`[edit]`, `[edit source]`)
  - Skip links (`Jump to navigation`, `Jump to search`)
  - "Navigation menu" heading (when present, depends on skin)

#### Scenario: Template 噪音

- **WHEN** extracting content from a Weird Gloop MediaWiki page
- **THEN** the following elements SHALL be identified as template noise:
  - DPL wikitext artifacts exposed from `metadata-dpl` spans (e.g., `{{hl|orange|Blind}}`, `{{Chips|+5}}`)
  - Scribunto JSON data rows
  - Empty parentheses `()` from empty template data
  - Inline `<style>` blocks with `data-mw-deduplicate` attributes (when present in raw HTML)

#### Scenario: Link 噪音

- **WHEN** extracting content from a Weird Gloop MediaWiki page
- **THEN** the following elements SHALL be identified as link noise:
  - Nested image links: `[![](thumb)](page)` pattern
  - Internal link title residue: `"title")` trailing artifacts
  - Category links: `[[Category:...]]` lines

#### Scenario: Table 噪音

- **WHEN** extracting content from a Weird Gloop MediaWiki page
- **THEN** the following elements SHALL be identified as table noise:
  - Infobox tables with many empty columns (detect: `len(cells) > 5 && non_empty <= 2`)
  - Missing Markdown table separator rows after headers

### Requirement: 通用模式文档

The system SHALL create `docs/patterns/mediawiki-extraction.md` as a reusable reference for all MediaWiki scraping tasks.

#### Scenario: 文档结构

- **WHEN** the pattern document is created
- **THEN** it SHALL contain the following sections:
  1. **Platform Taxonomy** — Weird Gloop vs self-hosted, version considerations
  2. **Noise Taxonomy** — the four clusters with known variants per site
  3. **Cleanup Pipeline** — rule ordering rationale and cluster execution flow
  4. **Cross-site Reuse** — checklist for adapting patterns to new MediaWiki sites

#### Scenario: 跨站点复用指南

- **WHEN** a new Weird Gloop MediaWiki site is encountered
- **THEN** the operator SHALL be able to use the cross-site reuse checklist to:
  1. Verify the site is MediaWiki (generator meta, DOM structure)
  2. Run `scrapling-get` to assess protection level
  3. Compare Scrapling output against the noise taxonomy
  4. Select the appropriate site profile for cleanup
  5. Identify any site-specific noise not covered by existing clusters
