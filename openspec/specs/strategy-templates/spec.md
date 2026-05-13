# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-templates`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: 新增平台类型驱动的策略模板系统

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: template-directory

The system SHALL maintain a `sites/templates/` directory containing platform-specific strategy skeleton files.

#### Scenario: template-structure
- **WHEN** the system is initialized or updated
- **THEN** `sites/templates/` SHALL exist with the following structure:
  - `mediawiki.yaml` — generic MediaWiki (no protection)
  - `mediawiki-fandom.yaml` — Fandom-hosted MediaWiki (Cloudflare)
  - `mediawiki-wiki-gg.yaml` — wiki.gg-hosted MediaWiki
  - `wordpress.yaml` — WordPress REST API (skeleton, partial in v1)
  - `static-site.yaml` — plain static HTML
  - `registry.json` — template index

### Requirement: template-content

Each template SHALL contain the platform's base extraction rules, known anti-crawl references, and a skeleton YAML frontmatter.

#### Scenario: template-yaml-frontmatter
- **WHEN** a template is used to generate a strategy scaffold
- **THEN** the frontmatter SHALL populate the following fields from deep discovery results:
  - `domain`
  - `description`
  - `protection_level` (from anti-crawl registry reference)
  - `anti_crawl_refs` (list of anti-crawl strategy IDs)
  - `structure.pages[]` (populated from discovery)
  - `structure.entry_points`
  - `api` (if detected)
  - `extraction.selectors`
  - `extraction.cleanup` (template defaults + platform specifics)
  - `extraction.text_normalization`

#### Scenario: template-cleanup-defaults
- **WHEN** a template is selected
- **THEN** the extraction cleanup list SHALL include platform-appropriate defaults, e.g.:
  - `mediawiki-fandom.yaml`: `fix_lazyload_images`, `strip_fandom_infobox_tables`, `convert_ambox_to_text`, `unwrap_image_wrappers`
  - `mediawiki.yaml`: `strip_edit_sections`, `strip_toc`
  - `static-site.yaml`: minimal (assume clean HTML)

### Requirement: template-selection

The system SHALL select the appropriate template based on platform type detected during deep discovery.

#### Scenario: auto-select-matching-template
- **WHEN** deep discovery identifies an API type (e.g., MediaWiki) and a CDN (e.g., Cloudflare)
- **THEN** the system SHALL select the best-matching template (e.g., `mediawiki-fandom.yaml`)
- **THEN** if no match is found, the system SHALL fall back to `custom.yaml`

### Requirement: registry-index

The system SHALL maintain `sites/templates/registry.json` for template discovery.

#### Scenario: registry-format
- **WHEN** a new template is added
- **THEN** `registry.json` SHALL contain an entry with: `id`, `platform`, `protection_level`, `file`
