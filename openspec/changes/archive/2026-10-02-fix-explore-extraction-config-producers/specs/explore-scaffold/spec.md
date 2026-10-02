# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-scaffold`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: modified
- 用户确认摘要: 2026-10-02 用户回复“确认”，同意模板、iterate 与自动修复配置生产契约统一归入已有 explore-scaffold。

## 规范真源声明

- 本文件为本 change 的行为规范真源，design/tasks/verification 必须引用本文件。
- 项目页面回写不得替代 spec delta。
- MODIFIED 要求来自 `openspec/specs/explore/explore-scaffold.md`；归档按此 merged spec 的真实 requirement 位置合并，保留独立样本推荐规范。

## MODIFIED Requirements

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

## ADDED Requirements

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
