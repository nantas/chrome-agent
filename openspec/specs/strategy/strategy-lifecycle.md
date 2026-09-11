# Strategy Domain: Lifecycle — Merged Spec

> **Merged from**: `site-strategy`, `bootstrap-strategy-cli`, `site-strategy-template`, `mediawiki-site-strategy`, `standalone-extraction`
> **Purpose**: Covers the full strategy lifecycle: creation (bootstrap, scaffold), validation (tier references, engine preference, platform variant, content_profile), template content profile recommendations, and standalone extraction utilities.

---

## Part 1 — Source: `site-strategy`

### Requirement: valid-tier-reference

站点策略文件的 `api.rate_limit.tier` 值 SHALL 引用在对应 anti-crawl 策略文件的 `rate_limit_tiers` 中已定义的 tier 名称。

### Requirement: anti-crawl-registry-site-coverage

`sites/anti-crawl/registry.json` 中每个 anti-crawl 策略条目的 `sites` 列表 SHALL 包含所有引用该 anti-crawl 策略的域名。

### Requirement: non-superseded-engine-preference

站点策略的 `engine_preference.preferred` SHOULD NOT 引用状态为 `superseded` 的引擎。

### Requirement: platform-variant-declaration

使用非标准 MediaWiki 平台变体的站点策略 SHALL 在 `api.platform_variant` 中声明其变体类型。

### Requirement: strategy-registry-sync

Registry metadata SHALL match the authoritative strategy frontmatter. Production lookup SHALL require a matching registry entry and a non-draft strategy that passes current validation; an unregistered file SHALL NOT become eligible merely because its marker is absent. Newly generated drafts SHALL retain explicit draft metadata until validated freeze and SHALL be excluded from production lookup. Previously frozen unmarked strategies MAY remain eligible subject to current schema validation; a legacy bootstrap marker SHALL be treated as draft regardless of existing registry membership. Re-freeze SHALL apply the same validations as first freeze rather than bypassing them based on marker shape.

#### Scenario: legacy-bootstrap-marker
- **WHEN** registry points to a strategy retaining a Bootstrapped or scaffold marker
- **THEN** production lookup SHALL reject its draft status until validated freeze.

#### Scenario: legacy-frozen-strategy
- **WHEN** an unmarked existing strategy passes current schema and has valid target identity
- **THEN** it SHALL remain usable without forcing a new site-analysis run.

### Requirement: content_profile ID 引用约束

`api.content_profile` 各字段的 value 必须在 `_STRATEGY_REGISTRY` 中注册。引用未注册 ID → pipeline 拒绝执行 (`EXIT_STRATEGY_ERROR`)。

### Requirement: infobox-field-handler-configuration

Strategy file's `extraction.infobox_field_handlers` map defines how each portable infobox `data-source` field should be extracted.

Supported handlers: `text`, `image`, `count_images`, `extract_cur_id`, `dedup_pools`, `simplify_collection`, `extract_tags`.

### Requirement: extraction-config-propagation

`infobox_field_handlers` SHALL be propagated to `HtmlToMarkdownConverter` at construction time via `extraction_config`.

### Requirement: api-platform-consumed-by-engine-selection

`api.platform` field SHALL be consumed by `selectFetcher()` and `main.py`. `"mediawiki"` or `"mediawiki-fandom"` → `"mediawiki-api"` engine.

### Requirement: rate-limit-api-engine-priority-update

`rate-limit-api` anti-crawl strategy SHALL list `mediawiki-api` as highest-priority engine for MediaWiki sites.

---

## Part 2 — Source: `bootstrap-strategy-cli`

### Requirement: 命令接口

```
chrome-agent bootstrap-strategy <url> --from <existing-domain> [--profile <cleanup-profile>]
```

### Requirement: 参考策略验证

`--from` domain must exist in `registry.json`. Target domain must NOT already have a strategy.

### Requirement: 字段适配规则

Bootstrap SHALL inherit only explicitly allowed reusable platform settings: validated API platform/variant/content-profile identifiers, rate limits, protection/engine references and schema-valid platform extraction defaults. It SHALL derive domain and API/image base URLs from the target, and SHALL NOT copy the source topic, version, labels, page patterns/examples, entry points, taxonomy or site-specific filters/field handlers as verified target facts. Site-specific values SHALL be absent or marked as pending validation in draft metadata. Known generic patterns MAY be supplied from a platform template with provenance, never claimed as site verification. Profile overrides SHALL resolve to supported operations and pass schema validation.

#### Scenario: cross-game-bootstrap
- **WHEN** a Fandom target is bootstrapped from another game
- **THEN** its URLs SHALL use the target domain, description SHALL not claim the reference game/version, and target page/taxonomy identities SHALL remain unverified until filled and validated.

#### Scenario: invalid-reference-extraction
- **WHEN** reusable source extraction or profile override violates the shared schema
- **THEN** bootstrap SHALL fail with diagnostics rather than copying invalid rules into a registered strategy.

### Requirement: Markdown body 生成

Body SHALL contain: header comment (bootstrapped from ref + date), Overview, Page Structure, Extraction Flow, Known Issues, Evidence sections.

### Requirement: Registry 索引更新

Bootstrap SHALL emit an explicitly marked draft and SHALL NOT add it as a production-eligible registry entry. Freeze SHALL validate schema, required target identities/entry points, capability references and recorded review evidence before atomically publishing the strategy and registry metadata. Failed validation or publication SHALL leave the strategy draft and prior registry state intact and return failure diagnostics.

#### Scenario: bootstrap-draft-not-routable
- **WHEN** bootstrap successfully creates a draft
- **THEN** production strategy lookup SHALL not route crawl/fetch to it.

#### Scenario: failed-freeze-preserves-draft
- **WHEN** freeze validation or publication fails
- **THEN** scaffold/draft markers SHALL remain and registry production state SHALL not change.

### Requirement: 输出与结果格式

Successful bootstrap SHALL return success for draft creation, include its strategy artifact, declare draft status and unresolved target fields, and recommend review/validation/freeze before production. It SHALL NOT report a production registry update or recommend immediate crawl unless the strategy is already validated and frozen through the lifecycle.

#### Scenario: draft-success-is-explicit
- **WHEN** bootstrap completes
- **THEN** the result SHALL distinguish generated draft from production readiness and list unresolved target fields.

## Part 3 — Source: `site-strategy-template`

### Requirement: template-content-profile-recommendations

| 模板 | discovery | acquisition | link_resolver | template_processor | assembler |
|------|-----------|-------------|---------------|--------------------|-----------|
| `mediawiki.yaml` | `allpages` | `wikitext_only` | `exact_title_match` | `simple_substitution` | `frontmatter_driven` |
| `mediawiki-fandom.yaml` | `category_members` | `html_rendered` | `short_name_with_cross_namespace` | `fandom_infobox` | `hybrid_frontmatter_and_rendered` |
| `mediawiki-wiki-gg.yaml` | `allpages` | `html_rendered` | `exact_title_match` | `structured_with_lua_fallback` | `hybrid_frontmatter_and_rendered` |

### Requirement: template-rate-limit-defaults

`mediawiki-fandom.yaml` and `mediawiki-wiki-gg.yaml` → `rate_limit.tier: "strict"`. `mediawiki.yaml` → no rate limit.

### Requirement: template-no-static-capabilities

Templates SHALL NOT contain `capabilities`. Generated by `derive_capabilities()`.

### Requirement: template-image-filtering

`mediawiki-wiki-gg.yaml` includes `extraction.image_filtering.skip_patterns`.

### Requirement: template-extraction-cleanup-selectors

`mediawiki-wiki-gg.yaml` includes default `extraction.cleanup_selectors`.

### Requirement: template-infobox-field-handlers-default

Templates SHALL NOT include `infobox_field_handlers`. These are site-specific.

---

## Part 4 — Source: `mediawiki-site-strategy`

### Requirement: 策略文件创建

Example: vampire.survivors.wiki strategy with `protection_level: low`, `engine_preference.preferred: scrapling-get`, page types `wiki_category` (static_page) and `wiki_article` (static_article).

### Requirement: content_profile 字段定义

Optional `api.content_profile` with 5 dimensions. Absent → all defaults. Partial → specified dimensions only.

### Requirement: capabilities 字段引用

`api.capabilities` is checked by `validate_api_config` against union of `required_capabilities` from composed strategies.

### Requirement: api-homepage-config-block

Optional `api.homepage` with: `page_title`, `category_sections`, `categories`, `category_page_types`, `assignment_priority`, `manual_assignments`.

### Requirement: structure-category-page-type

`type: category` is valid for `structure.pages[].type`. Default discovery: `categorymembers`.

---

## Part 5 — Source: `standalone-extraction`

### Requirement: single-page-fetch-and-convert

`fetch_and_convert(url, domain, output, mode, manifest_pages)` — fetch single URL via API, convert to Markdown. Modes: `html`, `wikitext`.

### Requirement: reconvert-existing-file

`reconvert_file(filepath, domain, manifest_pages)` — reconvert existing HTML/Markdown file.

### Requirement: cli-fetch-subcommand

`python3 -m scripts.pipeline fetch <url> --domain <d> --mode html --output <file>`. Failure → exit code 10.

### Requirement: fandom-extraction-configuration-migration

The Fandom template and Neon Abyss strategy SHALL use supported extraction configuration, translating lazyload rules to lazyload config, edit/TOC removal to supported cleanup/selectors, normalization to supported normalizer names, and removing dead descriptive pipeline fields. Migration SHALL preserve intended supported behavior through sample evidence, not mechanically turn every dictionary key into an operation string. Source changes SHALL NOT regenerate or mutate historical manifests, Markdown or downstream ingests.

#### Scenario: migrated-fandom-template
- **WHEN** target-specific fields are filled in the Fandom template
- **THEN** shared schema and Gate SHALL accept its cleanup/lazyload/normalization configuration.

#### Scenario: neon-behavior-regression
- **WHEN** Neon Abyss sample conversion runs with migrated configuration
- **THEN** supported lazyload/edit/TOC/ambox/image-wrapper and normalization behavior SHALL match approved fixtures without requiring historical batch re-extraction.

## Requirements

### Requirement: stable-registry-publication-format
Freeze SHALL preserve the existing registry indentation, trailing newline convention, top-level/member key order and relative order of unrelated entries. Updating an existing domain SHALL retain its entry position; new domains SHALL append. A newly created registry SHALL use four-space indentation. Only the target domain's metadata SHALL change semantically. Existing validation, atomic publication and rollback behavior SHALL remain in force.

#### Scenario: four-space-existing-registry
- **WHEN** a domain is frozen into a registry using four-space indentation
- **THEN** the result SHALL retain four-space indentation and unrelated entries SHALL NOT be reordered or changed.

#### Scenario: repeated-freeze
- **WHEN** the same unchanged strategy is frozen twice
- **THEN** the second registry publication SHALL be byte-identical to the first.

#### Scenario: failed-publication
- **WHEN** freeze validation or publication fails
- **THEN** the prior strategy and registry SHALL be restored according to the existing lifecycle contract.
