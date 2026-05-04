# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-cleanup-script`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，创建基于 site-strategy 分流的噪音清洗脚本，支持 vampire-survivors、balatro、generic-mediawiki 三个 profile；噪音按 navigation / template / link / table 四类聚类。

## 规范真源声明

- 本文件是 `mediawiki-cleanup-script` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Site-Strategy 分流

The system SHALL provide a cleanup script that accepts a site identifier and applies the corresponding rule profile.

#### Scenario: 显式指定站点

- **WHEN** the user runs `clean-mediawiki.sh --site vampire-survivors < input.md`
- **THEN** the script SHALL apply the `vampire-survivors` profile
- **AND** it SHALL enable only rules registered for that profile

#### Scenario: 通用缺省 profile

- **WHEN** the user runs `clean-mediawiki.sh --site generic-mediawiki < input.md`
- **THEN** the script SHALL apply the `generic-mediawiki` profile
- **AND** it SHALL enable all available rules (safe superset)
- **AND** it SHALL print a warning listing rules that may be overly aggressive for unknown sites

#### Scenario: 自动检测（可选）

- **WHEN** the script is run without `--site`
- **THEN** it SHALL default to `generic-mediawiki` profile
- **AND** it SHALL print a message indicating generic mode with a suggestion to specify `--site` for better results

### Requirement: 噪音规则聚类

The system SHALL organize cleanup rules into four clusters, each containing specific rules that can be independently enabled or disabled per profile.

#### Scenario: Navigation 集群

- **WHEN** the navigation cluster is enabled for a profile
- **THEN** the following rules SHALL be available:
  - `strip_footer` — remove footer sections (Tools, Privacy, Terms, etc.)
  - `strip_edit_links` — remove `[edit]` and `[edit source]` lines
  - `strip_skip_links` — remove "Jump to navigation" and "Jump to search" lines

#### Scenario: Template 集群

- **WHEN** the template cluster is enabled for a profile
- **THEN** the following rules SHALL be available:
  - `strip_dpl_wikitext` — remove lines containing exposed DPL template calls (e.g., `{{hl|...}}`, `{{Chips|...}}`, `{{Mult|...}}`)
  - `strip_json_data` — remove JSON data rows from Scribunto templates
  - `strip_empty_parens` — remove isolated empty parentheses `()` artifacts

#### Scenario: Link 集群

- **WHEN** the link cluster is enabled for a profile
- **THEN** the following rules SHALL be available:
  - `convert_nested_images` — transform `[![](thumb)](page)` into `![](url)`
  - `normalize_internal` — clean `"title")` residue and namespace prefixes from internal links
  - `strip_category_links` — remove `[[Category:...]]` lines and standalone Category references

#### Scenario: Table 集群

- **WHEN** the table cluster is enabled for a profile
- **THEN** the following rules SHALL be available:
  - `normalize_infobox` — detect infobox rows with many empty columns and convert to `| key | value |` format
  - `fix_separators` — insert `| --- |` separator rows after Markdown table headers when missing

### Requirement: 站点 Profile 映射

The system SHALL define a mapping from site identifiers to enabled rule clusters and individual rules.

#### Scenario: vampire-survivors profile

- **WHEN** the `vampire-survivors` profile is active
- **THEN** the following rules SHALL be enabled:
  - navigation: `strip_footer`, `strip_skip_links`
  - template: `strip_json_data`, `strip_empty_parens`
  - link: `convert_nested_images`, `normalize_internal`, `strip_category_links`
  - table: `normalize_infobox`, `fix_separators`

#### Scenario: balatro profile

- **WHEN** the `balatro` profile is active
- **THEN** the following rules SHALL be enabled:
  - navigation: `strip_footer`, `strip_edit_links`, `strip_skip_links`
  - template: `strip_dpl_wikitext`, `strip_empty_parens`
  - link: `convert_nested_images`, `normalize_internal`, `strip_category_links`
  - table: `normalize_infobox`, `fix_separators`

#### Scenario: generic-mediawiki profile

- **WHEN** the `generic-mediawiki` profile is active
- **THEN** ALL rules from all clusters SHALL be enabled
- **AND** the script SHALL process rules in a safe order: navigation → template → link → table
