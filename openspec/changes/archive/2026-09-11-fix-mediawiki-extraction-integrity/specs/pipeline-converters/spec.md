# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 用户授权“按照你建议的方案创建 change”。
- 变更类型: modified
- 用户确认摘要: 落实已讨论的抽取完整性修复范围；不自动恢复全站抓取。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 以此为依据，页面回写不得替代 spec delta。

## ADDED Requirements

### Requirement: monotonic-wikitable-scanning
The wikitext table converter SHALL scan complete top-level tables in document order, including a table at offset zero. Every iteration SHALL advance beyond the consumed span or terminate. It SHALL preserve surrounding and trailing text, preserve supported cell content, and SHALL NOT reprocess an already consumed table.

#### Scenario: table-at-start-with-tail
- **WHEN** input starts with a complete wikitable followed by prose and no other table
- **THEN** conversion SHALL terminate, convert the table once and retain the prose.

#### Scenario: table-at-start-and-second-table
- **WHEN** input starts with a table followed by prose and a second table
- **THEN** both tables SHALL be converted once in source order and neither complete top-level table SHALL remain as raw `{|` markup.

#### Scenario: table-after-prose
- **WHEN** a table starts after introductory prose
- **THEN** both introduction and table content SHALL be retained.

#### Scenario: malformed-or-nested-table
- **WHEN** input contains an unclosed table or supported nested table syntax
- **THEN** scanning SHALL terminate without rescanning a consumed span, preserve unconsumed malformed text, and retain existing supported nested-table behavior.


## MODIFIED Requirements

### Requirement: infobox-link-source-dir-passthrough
`extract_infobox()` SHALL pass `source_dir` to inline render callbacks in both selectolax and BS4 paths. The shared full-page entry and `HtmlToMarkdownConverter._render_infobox_table()` SHALL preserve the caller's link-index and source-directory context.

#### Scenario: infobox-link-uses-correct-relative-path
- **WHEN** `bosses/Ultra_Greed.md` links to `endings/index.md` from an infobox
- **THEN** the link SHALL be `[Ending 18](../endings/index.md)`.

#### Scenario: infobox-link-same-directory
- **WHEN** an infobox links to a page in the same output directory
- **THEN** its relative link SHALL have no directory prefix.

#### Scenario: bs4-context-preserved
- **WHEN** full-page extraction uses BS4 with a supplied inline renderer
- **THEN** field handlers and ordinary fields SHALL preserve that renderer's source directory and link targets.
