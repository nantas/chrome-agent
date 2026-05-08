# Specification Delta: html-to-markdown-converter

## Capability 对齐（已确认）

- Capability: `html-to-markdown-converter`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认融合 wiki.gg 项目的 HTML 解析经验，实现 HTML→Markdown 转换，保留图片和排版

## 规范真源声明

- 本文件是 `html-to-markdown-converter` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: html-cleaning-rules
The system SHALL clean the raw HTML from `action=parse` by removing wiki UI noise while preserving primary content structure.

#### Scenario: remove-edit-sections
- **WHEN** processing HTML containing `.mw-editsection` elements
- **THEN** all such elements SHALL be removed

#### Scenario: remove-toc
- **WHEN** processing HTML containing `#toc` or `.toc` elements
- **THEN** all such elements SHALL be removed

#### Scenario: remove-hatnotes
- **WHEN** processing HTML containing `.hatnote` elements
- **THEN** all such elements SHALL be removed

#### Scenario: remove-display-none-elements
- **WHEN** processing HTML containing elements with `style="display:none"` (e.g., upgraded/beta card images in list pages)
- **THEN** all such elements and their descendants SHALL be removed
- **AND** this SHALL prevent hidden card variants from appearing in Markdown output

#### Scenario: preserve-infobox
- **WHEN** processing HTML containing DRUID infobox containers
- **THEN** the infobox structure SHALL be preserved in the cleaned HTML
- **AND** it SHALL be converted to a Markdown-compatible representation

### Requirement: image-link-preservation
The system SHALL convert all `<img>` elements to Markdown image syntax, with absolute URLs.

#### Scenario: convert-wiki-images
- **WHEN** an image has `src="/images/thumb/StS2_Ironclad-Bash.png/150px-StS2_Ironclad-Bash.png?fd8171"`
- **THEN** it SHALL be converted to `![StS2 Ironclad-Bash](https://slaythespire.wiki.gg/images/thumb/StS2_Ironclad-Bash.png/150px-StS2_Ironclad-Bash.png?fd8171)`
- **AND** the `alt` attribute SHALL be derived from the filename or `alt`/`title` attribute

#### Scenario: convert-external-images
- **WHEN** an image has a protocol-relative URL (`src="//example.com/img.png"`)
- **THEN** it SHALL be converted to `https://example.com/img.png`

#### Scenario: skip-display-none-images
- **WHEN** an image is inside an element with `style="display:none"`
- **THEN** it SHALL be skipped entirely (removed during cleaning phase)

### Requirement: internal-link-conversion
The system SHALL convert wiki internal links (`<a href="/wiki/...">`) to standard Markdown relative links.

#### Scenario: convert-sts2-internal-link
- **WHEN** an anchor has `href="/wiki/Slay_the_Spire_2:Vulnerable"` and text "Vulnerable"
- **AND** the source page is `Slay_the_Spire_2/Bash.md`
- **THEN** it SHALL be converted to `[Vulnerable](Vulnerable.md)`

#### Scenario: convert-cross-namespace-link
- **WHEN** an anchor has `href="/wiki/Bash"` and text "Bash"
- **AND** the source page is `Slay_the_Spire_2/Bash.md`
- **THEN** it SHALL be converted to `[Bash](../Bash.md)`
- **AND** the relative path SHALL be computed from source to target using semantic-directory-mapping

#### Scenario: convert-anchor-link
- **WHEN** an anchor has `href="#Interactions"`
- **THEN** it SHALL be preserved as `[Interactions](#Interactions)`

#### Scenario: skip-external-links
- **WHEN** an anchor has `href="https://..."` (non-wiki domain)
- **THEN** it SHALL be preserved as a standard external Markdown link

#### Scenario: skip-non-exportable-links
- **WHEN** an anchor links to `File:`, `Category:`, `Template:`, `Talk:`, `Special:`, or `Help:` namespace
- **THEN** the link text SHALL be preserved but the href SHALL be removed or converted to plain text

### Requirement: block-element-rendering
The system SHALL convert HTML block elements to Markdown with faithful structure preservation.

#### Scenario: render-headings
- **WHEN** processing `<h2>`, `<h3>`, `<h4>`, etc.
- **THEN** they SHALL be converted to `##`, `###`, `####` respectively
- **AND** heading level 1 (`<h1>`) SHALL be treated as `##` to avoid conflict with page title

#### Scenario: render-lists
- **WHEN** processing `<ul>` and `<ol>` with nested structures
- **THEN** they SHALL be converted to `-` and `1.` Markdown lists with proper indentation

#### Scenario: render-tables
- **WHEN** processing `<table>` elements
- **THEN** simple tables SHALL be converted to Markdown pipe tables
- **AND** complex tables (with colspan/rowspan) SHALL fallback to a readable representation (key-value list or description list)

#### Scenario: render-blockquotes
- **WHEN** processing `<blockquote>` elements
- **THEN** they SHALL be converted to `>` prefixed lines

#### Scenario: render-code-blocks
- **WHEN** processing `<pre>` elements
- **THEN** they SHALL be converted to fenced code blocks (```)

### Requirement: inline-element-rendering
The system SHALL convert HTML inline elements to Markdown inline formatting.

#### Scenario: render-bold-italic
- **WHEN** processing `<strong>`, `<b>`, `<em>`, `<i>`
- **THEN** they SHALL be converted to `**text**` and `*text*` respectively

#### Scenario: render-inline-code
- **WHEN** processing `<code>`
- **THEN** it SHALL be converted to `` `text` ``

#### Scenario: render-line-breaks
- **WHEN** processing `<br>`
- **THEN** they SHALL be converted to newlines with proper paragraph handling
