# Specification Delta: site-strategy-slaythespire

## Capability 对齐（已确认）

- Capability: `site-strategy-slaythespire`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认更新站点策略以支持 HTML 渲染配置和新的输出结构

## 规范真源声明

- 本文件是 `site-strategy-slaythespire` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: content-acquisition-configuration
The site strategy SHALL declare `content_acquisition: html_rendered` in its API content profile.

#### Scenario: strategy-declares-html-rendered
- **WHEN** the strategy frontmatter contains `api.content_profile.content_acquisition: html_rendered`
- **THEN** the pipeline SHALL use HTML-rendered acquisition for all pages
- **AND** the strategy SHALL include `html_parse` in its `capabilities` list

### Requirement: namespace-coverage-configuration
The site strategy SHALL declare all target namespaces in its API configuration.

#### Scenario: strategy-declares-all-namespaces
- **WHEN** the strategy frontmatter contains `api.namespaces: [0, 3000, 14]`
- **THEN** discovery SHALL cover StS1 (ns=0), StS2 (ns=3000), and categories (ns=14)
- **AND** the Board Game namespace (ns=3010) SHALL NOT be included

### Requirement: taxonomy-update-for-cross-namespace
The site strategy taxonomy SHALL be updated to support both StS1 and StS2 content classification.

#### Scenario: taxonomy-includes-sts1-and-sts2
- **WHEN** the taxonomy contains `page_categories` mapping
- **THEN** it SHALL include categories that apply to both ns=0 and ns=3000 pages
- **AND** classification SHALL use the `CategoryMembersDiscoveryStrategy.classify_page` logic with namespace-aware directory prefixing

### Requirement: output-configuration-update
The site strategy output configuration SHALL support the new link format and directory structure.

#### Scenario: output-config-standard-markdown-links
- **WHEN** generating output with `html_rendered` strategy
- **THEN** internal links SHALL be generated as standard Markdown `[text](path.md)` format
- **AND** NOT as Obsidian-style `[[wikilink]]` format

### Requirement: filename-replacements
The site strategy filename configuration SHALL specify replacements for filesystem-safe naming.

#### Scenario: filename-safe-characters
- **WHEN** the strategy contains `api.filename.replacements`
- **THEN** it SHALL map `:` to `_`, `/` to `_`, and ` ` to `_`
- **AND** these replacements SHALL be applied before slugification

## ADDED Requirements

### Requirement: category-page-generation-configuration
The site strategy SHALL include configuration for category page generation.

#### Scenario: category-generation-enabled
- **WHEN** the strategy contains `api.category_page_generation: true`
- **THEN** the pipeline SHALL generate `index.md` files for all ns=14 pages
- **AND** combine `action=parse` description with `categorymembers` member lists

### Requirement: image-filtering-configuration
The site strategy SHALL specify image filtering rules for list pages.

#### Scenario: base-image-only-filter
- **WHEN** the strategy contains `api.image_filtering.list_pages: base_only`
- **THEN** the HTML cleaner SHALL remove all images inside `display:none` containers
- **AND** only the base (visible) card images SHALL be preserved in the Markdown output

## REMOVED Requirements

### Requirement: sts2-exclusive-output-prefix
**Reason**: The original strategy hardcoded `StS2/` prefix for ns=3000 pages and `StS1/` prefix for ns=0 pages in `classify_page`. With semantic-directory-mapping, namespace-based directory containers are handled uniformly by the mapping function.
**Migration**: Remove the namespace prefix logic from `classify_page` and rely on `semantic-directory-mapping` for directory assignment.
