# Explore Domain: Scaffold Generation — Merged Spec

> **Merged from**: `strategy-scaffold-generation`, `strategy-templates`, `sample-converter`, `sample-self-check`, `explore-skill-gates`
> **Purpose**: Covers the full scaffold lifecycle: template selection, scaffold generation with layered API merge, sample conversion using shared lib, self-check (S1-S12), agent gate rules, and skill-level presentation gates.

---

## Part 1 — Source: `strategy-scaffold-generation`

### Requirement: layered-api-merge

scaffold generator 的 API 对象组装 SHALL 使用分层合并逻辑：

- **Layer 1 — 模板声明性字段**：`platform_variant`、`content_profile`、`rate_limit` 从模板的 `api` 对象复制到 scaffold
- **Layer 2 — 探测事实性字段**：`base_url`、`version` 从 api_config 覆盖到 scaffold
- **Layer 3 — 动态推导字段**：`capabilities` 通过 `derive_capabilities()` 从 content_profile 生成

`api_config` 中的 `capabilities`、`site_name`、`lang`、`pages`、`articles` 等 siteinfo 字段 SHALL NOT 写入策略文件。

#### Scenario: api-config-present-template-has-profile
- **WHEN** api_config 返回 `{base_url, version, capabilities}` 且模板包含 `content_profile` 和 `platform_variant`
- **THEN** scaffold 的 `api.base_url` 来自 api_config，`api.content_profile` 来自模板，`api.capabilities` 由 `derive_capabilities()` 生成

#### Scenario: api-config-absent
- **WHEN** api_config 为 None
- **THEN** scaffold 的 `api` 完全来自模板

### Requirement: api-discovery-capabilities-isolation

`api_discovery.py` 的 `_probe_mediawiki()` 返回结果 SHALL 继续包含 `capabilities` 字段（用于信息展示），但 scaffold generator SHALL NOT 将 api_config 的 capabilities 传递到策略文件的 `api.capabilities` 字段。

### Requirement: scaffold-generates-derived-capabilities

scaffold generator 在组装 API 对象时 SHALL 调用 `derive_capabilities()` 函数生成 `api.capabilities` 字段。

#### Scenario: fandom-scaffold-capabilities
- **WHEN** scaffold 使用 `mediawiki-fandom.yaml` 模板
- **THEN** 生成的 `api.capabilities` 包含 `["category_lookup", "html_parse", "page_list"]`

---

## Part 2 — Source: `strategy-templates`

### Requirement: template-directory

The system SHALL maintain a `sites/templates/` directory containing platform-specific strategy skeleton files.

#### Scenario: template-structure
- **WHEN** the system is initialized
- **THEN** `sites/templates/` SHALL contain:
  - `mediawiki.yaml` — generic MediaWiki
  - `mediawiki-fandom.yaml` — Fandom-hosted MediaWiki
  - `mediawiki-wiki-gg.yaml` — wiki.gg-hosted MediaWiki
  - `wordpress.yaml` — WordPress REST API (skeleton)
  - `static-site.yaml` — plain static HTML
  - `registry.json` — template index

### Requirement: template-content

Each template SHALL contain the platform's base extraction rules, known anti-crawl references, and a skeleton YAML frontmatter. Every registered MediaWiki template's extraction configuration SHALL pass the shared extraction schema and reference only implemented cleanup operations. Generic MediaWiki and wiki.gg templates SHALL remove edit-section links through `strip_edit_links` and remove TOC elements through `.toc` and `#toc` cleanup selectors; other existing valid selectors, image rules and template declarations SHALL be preserved.

#### Scenario: template-yaml-frontmatter
- **WHEN** a template is used to generate a strategy scaffold
- **THEN** the frontmatter SHALL populate domain, description, protection_level, anti_crawl_refs, structure.pages, structure.entry_points, api, extraction.selectors, extraction.cleanup and extraction.text_normalization.

#### Scenario: registered-mediawiki-templates-are-admissible
- **WHEN** each MediaWiki template registered in sites/templates/registry.json is loaded and passed through the real scaffold generator
- **THEN** it SHALL produce a draft with schema-valid extraction configuration
- **AND** it SHALL NOT publish a frozen strategy or modify production registry eligibility.

#### Scenario: edit-and-toc-cleanup-preserves-body
- **WHEN** generic MediaWiki or wiki.gg template extraction rules preprocess a fixture containing body text, edit-section links and class/id TOC elements
- **THEN** edit and TOC elements SHALL be removed and body text SHALL remain
- **AND** existing wiki.gg selectors and decorative-image rules SHALL remain intact.

### Requirement: template-selection

The system SHALL select the appropriate template based on platform type detected during deep discovery.

#### Scenario: auto-select-matching-template
- **WHEN** deep discovery identifies an API type and CDN
- **THEN** the system SHALL select the best-matching template
- **THEN** if no match is found, the system SHALL fall back to `custom.yaml`

### Requirement: registry-index

`sites/templates/registry.json` SHALL contain entries with: `id`, `platform`, `protection_level`, `file`.

### Requirement: template-content-profile-recommendations

平台模板的 `api` 对象 SHALL 包含 `content_profile` 字段，提供该平台变体的推荐策略 ID 组合。

| 模板 | discovery | acquisition | link_resolver | template_processor | assembler |
|------|-----------|-------------|---------------|--------------------|-----------|
| `mediawiki.yaml` | `allpages` | `wikitext_only` | `exact_title_match` | `simple_substitution` | `frontmatter_driven` |
| `mediawiki-fandom.yaml` | `category_members` | `html_rendered` | `short_name_with_cross_namespace` | `fandom_infobox` | `hybrid_frontmatter_and_rendered` |
| `mediawiki-wiki-gg.yaml` | `allpages` | `html_rendered` | `exact_title_match` | `structured_with_lua_fallback` | `hybrid_frontmatter_and_rendered` |

### Requirement: template-rate-limit-defaults

| 模板 | rate_limit.tier |
|------|----------------|
| `mediawiki.yaml` | 无 |
| `mediawiki-fandom.yaml` | `strict` |
| `mediawiki-wiki-gg.yaml` | `strict` |

### Requirement: template-no-static-capabilities

平台模板 SHALL NOT 包含 `capabilities` 字段。capabilities 由 scaffold generator 通过 `derive_capabilities()` 从 content_profile 动态推导。

### Requirement: template-image-filtering

The `mediawiki-wiki-gg.yaml` template SHALL include default `extraction.image_filtering.skip_patterns`.

### Requirement: template-extraction-cleanup-selectors

The `mediawiki-wiki-gg.yaml` template SHALL include default `extraction.cleanup_selectors`.

### Requirement: template-infobox-field-handlers-default

Platform templates SHALL NOT include `infobox_field_handlers` by default. These are site-specific.

---

## Part 3 — Source: `sample-converter`

### Requirement: apply-extraction-uses-shared-lib

`sample_converter._apply_extraction()` SHALL be a 4-step sequential pipeline calling `lib/extraction/` shared modules:

1. `extract_infobox(full_html, config)` from `lib.extraction.infobox`
2. `preprocess_html(full_html, config, context="explore")` from `lib.extraction.preprocessor`
3. `convert_html_to_markdown(cleaned_html, domain, config)`
4. Prepend infobox Markdown before body Markdown if non-empty

#### Scenario: infobox not processed twice
- **WHEN** both `extract_infobox()` and `preprocess_html()` operate on the same HTML string
- **THEN** `extract_infobox()` SHALL only read the infobox, while `preprocess_html()` SHALL remove the infobox container from HTML

### Requirement: strategy-loader-replaces-load-extraction-rules

`sample_converter._load_extraction_rules()` SHALL be replaced by `lib.strategy_loader` functions.

#### Scenario: loading extraction rules from strategy file
- **WHEN** extraction rules are needed
- **THEN** the code SHALL use `lib.strategy_loader.parse_strategy()` to get the full frontmatter dict

### Requirement: sample-converter-cli-entry

`scripts/explore/sample_converter.py` SHALL provide `main()` with `apply` and `fetch-and-apply` subcommands.

#### Scenario: apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py apply --strategy <path> --html <path> --title <name> --output <path>` is invoked
- **THEN** it SHALL load extraction rules, read HTML, produce Markdown, write to `--output`

#### Scenario: fetch-and-apply-subcommand
- **WHEN** `python3 scripts/explore/sample_converter.py fetch-and-apply --strategy <path> --page <title> --output <path>` is invoked
- **THEN** it SHALL fetch HTML via MediaWiki API, then apply extraction rules

---

## Part 4 — Source: `sample-self-check`

### Requirement: self-check-s1-image-retention

Verify image count matches and all retained images use full URLs (no relative `/images/` paths).

### Requirement: self-check-s2-link-resolution

Verify zero relative `/wiki/` links in Markdown.

### Requirement: self-check-s3-infobox-extraction

Verify infobox has ≥ 3 fields, key fields non-empty, no raw HTML residue.

### Requirement: self-check-s5-text-integrity

Verify no formatting anomalies including: missing spaces, base64 residue, escape artifacts, repeated link text, raw HTML tags, unresolved entities.

### Requirement: self-check-s6-table-integrity

Verify table row count within 5% tolerance.

### Requirement: self-check-s8-section-completeness

Verify all `mw-headline` sections are preserved as Markdown headings.

### Requirement: self-check-s9-navigation-leakage

Verify navigation sidebar content has NOT leaked into Markdown body.

### Requirement: self-check-s10-youtube-title-quality

Verify YouTube links use descriptive titles, not generic "YouTube Video".

### Requirement: self-check-s11-zero-relative-links

Verify ZERO relative `/wiki/` or `/images/` link references.

### Requirement: self-check-s12-infobox-semantic-quality

Verify infobox Name has spaces between words, ID fields contain only digits/dots, no image filenames as text.

### Requirement: auto-remediation-extended

The system SHALL recognize issue types including relative_image_url, relative_link, infobox_html_residue, section_loss, nav_leak, youtube_title and id_navigation_leak, while determining automatic remediation eligibility from implemented consumers and available parameters. Infobox_incomplete, name_spacing and name_is_filename SHALL remain outside automatic remediation. Recognition SHALL NOT imply that a cleanup operation exists.

For schema-valid MediaWiki input, a remediation proposal SHALL contain only supported extraction fields and operations; report metadata SHALL be separate from extraction configuration. Existing `auto_remediate()` callers SHALL continue to receive an extraction dictionary. Proposal generation SHALL NOT mutate the input configuration, including nested structures. Valid existing rules SHALL be preserved.

#### Scenario: implemented-fixes-produce-valid-rules
- **WHEN** image-wrapper, table-class or space-normalization remediation is requested
- **THEN** supported operation/normalization updates SHALL pass the shared schema and reach the real configured consumer
- **AND** batch ordering and deduplication SHALL be deterministic.

#### Scenario: lazyload-with-complete-evidence
- **WHEN** a base64/lazyload issue has complete existing or explicit evidence-backed placeholder_pattern and real_src_attr values
- **THEN** remediation SHALL use structured lazyload configuration
- **AND** real preprocessing SHALL replace the matching placeholder source using the configured source attribute
- **AND** it SHALL NOT emit fix_lazyload_images as a cleanup operation.

#### Scenario: unsupported-or-under-specified-remediation
- **WHEN** a requested repair lacks an implemented consumer or required configuration evidence
- **THEN** extraction configuration SHALL NOT gain invented operations, guessed attributes, destructive broad selectors or report-only fields
- **AND** a separate unresolved record SHALL retain the source issue and include a stable reason code and explanation
- **AND** the issue SHALL remain unresolved until later self-check evidence establishes resolution.

#### Scenario: retry-only-on-admitted-change
- **WHEN** all requested remedies are unsupported or produce no effective configuration change
- **THEN** callers SHALL surface unresolved records without repeatedly reconverting unchanged rules
- **AND** supported changes, when present, SHALL be admitted before reconversion and subject to the existing retry limit.

### Requirement: ki-lifecycle-consumption

Self-check failure output SHALL be consumable by the KI Lifecycle module for classification, prioritization and status tracking. Remediation inability SHALL retain original failure identity and applicable fixable_type, with separate diagnostic reasons; it SHALL NOT mark the failure resolved or change its identity solely because a rule was proposed.

#### Scenario: unresolved-remediation-retains-failure
- **WHEN** automatic or feedback-driven remediation cannot execute an issue's requested repair
- **THEN** the caller SHALL present unresolved issue/reason records and preserve the self-check failure for existing KI classification
- **AND** no automatic freeze, Gate bypass or fabricated success SHALL occur.

### Requirement: feedback-extraction-admission-before-write

For MediaWiki drafts, iterate SHALL build candidate extraction configuration separately, admit it with the shared schema before rewriting the scaffold or invoking conversion, and emit only consumer-supported rules. Edit feedback SHALL use strip_edit_links; TOC feedback SHALL merge .toc/#toc selectors without deleting valid existing selectors. Image feedback SHALL use existing image-wrapper cleanup where applicable and evidence-backed structured lazyload, with under-specified actions explicitly unresolved. Non-MediaWiki descriptive extraction rules SHALL retain their existing schema boundary.

#### Scenario: supported-feedback-round-trip
- **WHEN** iterate receives supported edit/TOC/image/spacing feedback for a valid MediaWiki draft
- **THEN** admitted updates SHALL survive the actual frontmatter rewrite/read cycle and reach real preprocessing
- **AND** the original in-memory configuration SHALL NOT be mutated by planning.

#### Scenario: invalid-candidate-preserves-file
- **WHEN** the existing or candidate MediaWiki extraction configuration fails schema validation
- **THEN** iterate SHALL return a structured failure including field diagnostics
- **AND** the original scaffold SHALL remain byte-for-byte unchanged
- **AND** no sample conversion SHALL be invoked.

#### Scenario: missing-lazyload-evidence-preserves-valid-actions
- **WHEN** image feedback can apply a supported wrapper rule but lacks evidence for lazyload source attributes
- **THEN** iterate MAY apply the admitted wrapper rule
- **AND** it SHALL report the lazyload action as unresolved without guessed fields or unsupported cleanup operations.

#### Scenario: non-mediawiki-boundary-preserved
- **WHEN** a non-MediaWiki draft uses descriptive extraction rules admitted by its existing workflow
- **THEN** this change SHALL NOT reject it solely by applying MediaWiki cleanup schema to those descriptions.

---

## Part 5 — Source: `explore-skill-gates`

### Requirement: skill-gate-structure-analysis

After `chrome-agent explore` returns, the agent SHALL present a structure analysis before proceeding:

1. Site type and platform identification
2. Identified page types with representative examples
3. Content map (nav structure, category hierarchy)
4. Protection assessment
5. Estimated page scale

#### Scenario: structure-analysis-from-discover-data
- **WHEN** explore result includes `discovery.content_profile` and `discovery.api`
- **THEN** the agent SHALL summarise page type, nav sections, content structure, and protection

### Requirement: skill-gate-sample-conversion

After structure analysis is confirmed, the agent SHALL run sample conversions on 2-4 representative pages.

#### Scenario: sample-selection
- **WHEN** page types are confirmed
- **THEN** the agent SHALL select 2-4 sample pages, at least one from each page type

#### Scenario: quality-issues-flagging
- **WHEN** a sample Markdown contains HTML artifacts, broken template rendering, or garbled content
- **THEN** the agent SHALL highlight these issues explicitly

### Requirement: skill-gate-llm-self-check

After sample conversion, the agent SHALL perform LLM-based self-check evaluating: Completeness, Formatting, Broken links, Content fidelity.

#### Scenario: self-check-execution
- **WHEN** sample conversion is complete
- **THEN** the agent SHALL produce a pass/fail summary per dimension per sample

### Requirement: skill-gate-user-confirmation

The agent SHALL wait for explicit user confirmation before proceeding to full extraction.

#### Scenario: confirmation-prompt
- **WHEN** samples and self-check results are presented
- **THEN** the agent SHALL ask the user to confirm
- **THEN** the agent SHALL NOT proceed to `crawl` or `fetch` without explicit user confirmation

### Requirement: skill-explore-result-interpretation

The SKILL.md SHALL include a mapping of explore result fields to their purpose and the gate that uses them.

#### Scenario: failure-result-handling
- **WHEN** explore returns `result: "failure"`
- **THEN** the agent SHALL surface the exact error and remediation
- **THEN** it SHALL NOT invent a fallback strategy or workaround
