# site-strategy-schema — Spec

## Purpose

Defines the structured schema for site strategy files: YAML frontmatter fields (domain, description, protection_level, anti_crawl_refs, structure, extraction), page hierarchy with per-page anti_crawl_refs, controlled vocabularies for page_type and protection_level, pagination patterns, registry.json index format, _attachments directory usage, and governance constraints.

## Requirements

### Requirement: 目录存放结构

The system SHALL organize site strategy files by domain, using a folder-per-domain structure.

Each site strategy directory SHALL contain:
- `strategy.md` — the site strategy file with YAML frontmatter + Markdown body
- `_attachments/` — optional directory for operational artifacts (scripts, configs, progress files)

#### Scenario: 策略文件存放位置

- **WHEN** a site strategy for domain `fanbox.cc` is created
- **THEN** it SHALL be stored at `sites/strategies/fanbox.cc/strategy.md`
- **AND** operational artifacts (scripts, configs) SHALL be stored at `sites/strategies/fanbox.cc/_attachments/`

#### Scenario: 无附件的站点

- **WHEN** a site has no operational artifacts
- **THEN** the `_attachments/` directory MAY be absent
- **AND** `strategy.md` alone SHALL be sufficient

### Requirement: YAML frontmatter 必填字段

The system SHALL define a mandatory YAML frontmatter schema for all site strategy files.

Each `strategy.md` SHALL include the following fields in its YAML frontmatter:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | yes | Primary domain (e.g., `fanbox.cc`, `mp.weixin.qq.com`) |
| `description` | string | yes | One-sentence summary of scraping scope |
| `protection_level` | enum | yes | `low`, `medium`, `high`, `authenticated`, or `variable` |
| `anti_crawl_refs` | string[] | yes | References to `anti-crawl/` strategy IDs; empty array if none |
| `structure` | object | yes | Page hierarchy and connectivity (see Structure requirement) |
| `extraction` | object | no | Globally useful selectors, image handling, and cleanup rules |

#### Scenario: 必填字段完整性

- **WHEN** a site strategy file is created
- **THEN** it SHALL contain all required frontmatter fields
- **AND** missing any required field SHALL be treated as an incomplete strategy

#### Scenario: anti_crawl_refs 为空

- **WHEN** a site has no protection mechanisms
- **THEN** `anti_crawl_refs` SHALL be `[]` (empty array)
- **AND** this SHALL be explicitly stated, not omitted

### Requirement: Structure 页面层级与连接

The system SHALL define the `structure` object to describe all page types within a site, their dynamic behavior, pagination patterns, and navigation connectivity.

The `structure` object SHALL contain:
- `pages`: array of page objects, each with:
  - `id`: stable identifier for the page type (kebab-case, e.g., `creator_posts_list`)
  - `label`: human-readable name
  - `url_pattern`: URL pattern with `:param` placeholders (e.g., `/@:creatorId/posts`)
  - `url_example`: concrete example URL used for validation
  - `type`: page type from the controlled vocabulary (see Page Type Vocabulary)
  - `anti_crawl_refs`: optional override of per-file `anti_crawl_refs` for this page only; when absent, inherits from file-level `anti_crawl_refs`
  - `content_type`: what content this page produces (`post_card`, `article_body`, `article_with_attachments`, `search_results`, `binary_file`, `list`, `auth_gate`)
  - `pagination`: pagination configuration (see Pagination requirement)
  - `links_to`: array of navigation targets reachable from this page
  - `requires_auth`: boolean, whether this page type requires authentication
- `entry_points`: array of page IDs that start a crawl

#### Scenario: 单页面站点

- **WHEN** a site has only one page type (e.g., WeChat article)
- **THEN** `structure.pages` SHALL contain one entry with `type: static_article`
- **AND** `pagination` SHALL be `none`
- **AND** `links_to` SHALL be `[]`

#### Scenario: 多页面站点含线性导航

- **WHEN** a site has sequential page types (e.g., fanbox.cc: post_list → post_detail → file_download)
- **THEN** `links_to` SHALL capture the navigation target and selector for each hop
- **AND** `entry_points` SHALL be `[post_list_page_id]`

#### Scenario: 同域多入口站点

- **WHEN** a domain has structurally different entry points (e.g., x.com: public tweet vs hashtag search)
- **THEN** `structure.pages` SHALL list both page types
- **AND** `entry_points` SHALL list all valid starting pages
- **AND** per-page `anti_crawl_refs` SHALL differentiate protection per entry point when applicable

### Requirement: Page Type 受控词汇表

The system SHALL define a controlled vocabulary for `structure.pages[].type`.

| Value | Description |
|-------|-------------|
| `static_page` | Static HTML page, no JS required for content |
| `static_article` | Static article detail page (e.g., WeChat public article) |
| `dynamic_list` | JS-rendered list of items (e.g., post list with pagination) |
| `dynamic_content` | JS-rendered content detail page with interactive elements |
| `search_results` | Search/form-results page with dynamic filtering |
| `binary_file` | Direct file download endpoint |
| `auth_gate` | Authentication/login gate page |

New types SHALL be added via openspec change to this spec.

#### Scenario: 类型扩展

- **WHEN** a new page behavior is encountered that does not fit existing types
- **THEN** a new openspec change SHALL be created to add the type to this vocabulary
- **AND** the rationale for the new type SHALL be documented in the change's proposal

### Requirement: Pagination 分页模式

The system SHALL define pagination configuration for list pages.

`pagination` SHALL be one of:
- `none` — single page, no pagination (for non-list pages)
- `url_parameter`: `{ mechanism: "url_parameter", parameter: "<name>", start: <int> }`
- `cursor_based`: `{ mechanism: "cursor_based", field: "<name>" }`
- `scroll_infinite`: `{ mechanism: "scroll_infinite", trigger: "<description>" }`
- `click_next`: `{ mechanism: "click_next", selector: "<css-selector>" }`

#### Scenario: URL 参数分页

- **WHEN** a list page uses `?page=N` for pagination
- **THEN** `pagination` SHALL be `{ mechanism: "url_parameter", parameter: "page", start: 1 }`

#### Scenario: 非列表页

- **WHEN** a page is not a list (static article, detail page, etc.)
- **THEN** `pagination` SHALL be `none`

### Requirement: Extraction 提取配置

The system SHALL define the `extraction` object for globally useful selectors, image handling, and cleanup rules.

`extraction` SHALL contain:
- `selectors` (optional): map of semantic field names to CSS selectors (e.g., `title: "#activity-name"`)
- `image_handling` (optional):
  - `attribute`: image source attribute to prefer (e.g., `data-src`)
  - `fallback`: fallback attribute (e.g., `src`)
  - `output_format`: `markdown_inline` | `url_list` | `skip`
- `cleanup` (optional): array of cleanup rule identifiers (e.g., `strip_lead_in_promo`)

#### Scenario: 文章页提取选择器

- **WHEN** an article page has known DOM selectors for title, author, body
- **THEN** `extraction.selectors` SHALL map semantic field names to their CSS selectors

#### Scenario: 无提取选择器

- **WHEN** no globally useful selectors are known
- **THEN** `extraction` MAY be omitted from frontmatter entirely

### Requirement: Markdown body 推荐章节

The system SHALL recommend the following Markdown body sections for site strategy files. These sections are advisory, not mandatory.

Recommended sections:
1. **Overview** — what this site is, scraping goals it serves
2. **Page Structure** — detailed narrative walkthrough of each page type with visual description
3. **Extraction Flow** — step-by-step extraction procedure
4. **Known Issues** — observed failure modes, rate limits, edge cases
5. **Evidence** — links to reports, dates of validated runs

#### Scenario: Body 章节补充 frontmatter

- **WHEN** a site strategy body provides operational details
- **THEN** it SHALL NOT duplicate frontmatter fields
- **AND** it SHALL expand on what the frontmatter summarizes

### Requirement: _attachments 目录用途

The system SHALL define the `_attachments/` directory for operational artifacts that belong to a site strategy.

`_attachments/` SHALL contain:
- Scripts (batch download, extraction helpers)
- Configuration files
- Progress tracking files
- Any run-specific operational artifacts

`_attachments/` SHALL NOT contain:
- Strategy description (that belongs in `strategy.md`)
- Duplicated content from `strategy.md`

#### Scenario: 附件示例

- **WHEN** fanbox.cc has a batch download script
- **THEN** it SHALL be stored at `sites/strategies/fanbox.cc/_attachments/fanbox-download-videos.mjs`

### Requirement: Registry.json 索引格式

The system SHALL maintain a `sites/strategies/registry.json` index for fast machine querying of site strategies.

`registry.json` SHALL be an object with a single key `entries` containing an array of entry objects. Each entry SHALL contain fields sufficient for strategy matching without reading the full strategy file:

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Site domain |
| `description` | string | One-sentence summary |
| `protection_level` | string | From controlled vocabulary |
| `page_types` | string[] | All page types present in `structure.pages[].type` |
| `pagination` | string[] | All pagination mechanisms present (deduplicated) |
| `entry_points` | string[] | Entry point page IDs |
| `anti_crawl_refs` | string[] | Referenced anti-crawl strategy IDs |
| `file` | string | Relative path to `strategy.md` |

#### Scenario: Registry 可查询

- **WHEN** an agent encounters an unknown site with page types and pagination mechanism
- **THEN** it SHALL be able to scan `registry.json` entries for structural similarity without reading individual strategy files

#### Scenario: Registry 一致性

- **WHEN** a site strategy file's YAML frontmatter is updated
- **THEN** `registry.json` SHALL be updated to reflect the changes
- **AND** if inconsistency is detected, the frontmatter SHALL be considered authoritative

### Requirement: protection_level 受控词汇表

The system SHALL define a controlled vocabulary for `protection_level`.

| Value | Description |
|-------|-------------|
| `low` | No anti-bot protection; static HTML is accessible |
| `medium` | JS required for rendering but no explicit anti-bot challenge |
| `high` | Active anti-bot protection (Cloudflare, WAF, CAPTCHA) |
| `authenticated` | Requires valid session credentials |
| `variable` | Different pages within the site have different protection levels |

#### Scenario: 保护级别分配

- **WHEN** a site has no anti-bot protection and no auth requirement
- **THEN** `protection_level` SHALL be `low`
- **AND** `anti_crawl_refs` SHALL be `[]` or reference only informational strategies

### Requirement: 新增策略的治理约束

The system SHALL enforce through AGENTS.md that any new site strategy creation SHALL include a registry.json update.

#### Scenario: 注册表更新

- **WHEN** a new `strategy.md` file is added under `sites/strategies/<domain>/`
- **THEN** the operator SHALL add a corresponding entry to `sites/strategies/registry.json`
- **AND** the operator SHALL verify that `domain`, `page_types`, and `file` fields are correct
