# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-schema`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: explore mode 中确认——新增 optional `engine_preference` 字段，可在文件级别和 per-page 级别设置，用于声明特定站点或页面的引擎优先级覆盖

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Engine Preference 引擎偏好

The system SHALL define an optional `engine_preference` field for site strategy YAML frontmatter.

The `engine_preference` object SHALL contain:
- `preferred` (required, string): Canonical engine identifier from `configs/engine-registry.json` that should be tried first for this site
- `reason` (optional, string): Human-readable justification for the preference (e.g., "All pages require JS rendering")

`engine_preference` MAY be specified at two levels:

1. **File level**: In the top-level YAML frontmatter, applies to all pages in the site unless overridden per-page
2. **Per-page level**: In `structure.pages[].engine_preference`, overrides the file-level preference for a specific page type

#### Scenario: 文件级别引擎偏好

- **WHEN** a site strategy specifies file-level `engine_preference`:
  ```yaml
  domain: x.com
  engine_preference:
    preferred: scrapling-fetch
    reason: "All pages require JS rendering for content"
  ```
- **THEN** `scrapling-fetch` SHALL be tried before any other engine for all pages in this site
- **AND** the engine's `default_rank` from `configs/engine-registry.json` SHALL be overridden for this site

#### Scenario: Per-page 引擎偏好覆盖

- **WHEN** a site has multiple page types with different engine needs:
  ```yaml
  structure:
    pages:
      - id: public_tweet
        type: dynamic_content
        engine_preference:
          preferred: scrapling-fetch
      - id: hashtag_search
        type: search_results
        engine_preference:
          preferred: scrapling-stealthy-fetch
  ```
- **THEN** `public_tweet` pages SHALL use `scrapling-fetch` first
- **AND** `hashtag_search` pages SHALL use `scrapling-stealthy-fetch` first
- **AND** pages without per-page `engine_preference` SHALL fall back to: (1) file-level preference, (2) anti-crawl strategy `engine_priority`, (3) engine `default_rank`

#### Scenario: 引擎偏好必须引用有效引擎

- **WHEN** `engine_preference.preferred` is specified
- **THEN** the value SHALL match an engine `id` in `configs/engine-registry.json`
- **AND** a reference to a non-existent engine SHALL be treated as a validation error

#### Scenario: 无引擎偏好

- **WHEN** a site strategy does not specify `engine_preference`
- **THEN** engine selection SHALL fall back to: (1) matching anti-crawl strategy `engine_priority`, (2) engine `default_rank`
- **AND** the site strategy is still valid and complete without this field

### Requirement: YAML frontmatter 必填字段（更新）

The system SHALL define a mandatory YAML frontmatter schema for all site strategy files.

The following field is ADDED to the existing schema:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `engine_preference` | object | no | Optional engine preference for this site; contains `preferred` (string) and optional `reason` (string) |

All previously defined required fields (`domain`, `description`, `protection_level`, `anti_crawl_refs`, `structure`) remain required and unchanged.

#### Scenario: 向前兼容

- **WHEN** an existing site strategy file created before Phase 4 does not contain `engine_preference`
- **THEN** it SHALL still be considered valid and complete
- **AND** the absence of `engine_preference` SHALL NOT cause any validation errors

### Requirement: Structure 页面层级（更新）

The system SHALL define the `structure.pages[]` array with the following ADDED optional field:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `engine_preference` | object | no | Per-page engine preference override; same structure as file-level `engine_preference` |

All previously defined fields in `structure.pages[]` (`id`, `label`, `url_pattern`, `url_example`, `type`, `anti_crawl_refs`, `content_type`, `pagination`, `links_to`, `requires_auth`) remain unchanged.

#### Scenario: Per-page preference overrides file-level

- **WHEN** a site has file-level `engine_preference: { preferred: scrapling-get }` and a specific page has `engine_preference: { preferred: scrapling-stealthy-fetch }`
- **THEN** that specific page SHALL use `scrapling-stealthy-fetch`
- **AND** all other pages SHALL use `scrapling-get` (file-level preference)
