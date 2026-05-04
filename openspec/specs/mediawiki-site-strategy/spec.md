# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-site-strategy`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，为 vampire.survivors.wiki 创建 site strategy，使 crawl 命令可用；页面类型使用现有受控词汇表 static_page / static_article，无需扩展。

## 规范真源声明

- 本文件是 `mediawiki-site-strategy` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 策略文件创建

The system SHALL create a complete `sites/strategies/vampire.survivors.wiki/strategy.md` with valid YAML frontmatter and Markdown body.

#### Scenario: 必填 frontmatter 字段完整性

- **WHEN** the strategy file is created
- **THEN** it SHALL contain all mandatory fields per `site-strategy-schema`: `domain`, `description`, `protection_level`, `anti_crawl_refs`, `structure`, and optionally `extraction`
- **AND** `protection_level` SHALL be `low`
- **AND** `anti_crawl_refs` SHALL be `[]`
- **AND** `engine_preference.preferred` SHALL be `scrapling-get`

#### Scenario: 页面结构定义

- **WHEN** the strategy defines page structure
- **THEN** it SHALL declare at least two page types: `wiki_category` (type `static_page`) and `wiki_article` (type `static_article`)
- **AND** `wiki_category` SHALL define `links_to` targeting `wiki_article` with an appropriate CSS selector for MediaWiki internal links
- **AND** `entry_points` SHALL be `[wiki_category]`

#### Scenario: 提取配置

- **WHEN** the strategy defines extraction rules
- **THEN** `extraction.image_handling` SHALL specify `attribute: src`, `output_format: markdown_inline`
- **AND** `extraction.cleanup` SHALL list the applicable MediaWiki noise rule identifiers per `mediawiki-extraction-patterns`

### Requirement: 索引同步

The system SHALL update `sites/strategies/registry.json` with a new entry for `vampire.survivors.wiki`.

#### Scenario: Registry 一致性

- **WHEN** the site strategy is created
- **THEN** a corresponding entry SHALL be added to `registry.json`
- **AND** the entry SHALL include: `domain`, `description`, `protection_level`, `page_types`, `pagination`, `entry_points`, `anti_crawl_refs`, `file`
- **AND** `page_types` SHALL contain `static_page` and `static_article`
- **AND** `file` SHALL be `vampire.survivors.wiki/strategy.md`
