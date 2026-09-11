# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy`
- 来源: `proposal.md` / 用户已授权两组修复目标
- 变更类型: `modified`
- 用户确认摘要: 规划两组修复，ns0 空目录按建议归 Misc，不处理历史产物。

## 规范真源声明

- 本文件为本 capability 在本 change 的行为规范真源；design/tasks/verification 必须引用本文件。
- 项目页面回写不得替代本文件。

## 归档目标

MODIFIED `Extraction` maps exactly to `openspec/specs/strategy/strategy-schema.md`. Other MODIFIED requirements map exactly to `openspec/specs/strategy/strategy-lifecycle.md`; ADDED requirements SHALL be appended there. Do not create a parallel canonical strategy/spec.md.

## MODIFIED Requirements

### Requirement: Extraction

Extraction SHALL expose selectors and image_handling maps, cleanup as list[str] of supported shared operations, optional lazyload map with enabled/placeholder_pattern/real_src_attr, text_normalization as list[str] of supported normalizers, and other explicitly consumed schema fields. Unsupported legacy descriptive pipeline keys and malformed/named operations SHALL fail validation. Validation SHALL run at scaffold/bootstrap/freeze and production consumption boundaries before network work; templates SHALL pass structural validation after target fields are filled.

#### Scenario: production-rejects-old-cleanup
- **WHEN** any production entry receives cleanup dictionaries, unsupported normalization keys or dead extraction.pipeline
- **THEN** it SHALL return structured configuration failure before network access.

### Requirement: 字段适配规则

Bootstrap SHALL inherit only explicitly allowed reusable platform settings: validated API platform/variant/content-profile identifiers, rate limits, protection/engine references and schema-valid platform extraction defaults. It SHALL derive domain and API/image base URLs from the target, and SHALL NOT copy the source topic, version, labels, page patterns/examples, entry points, taxonomy or site-specific filters/field handlers as verified target facts. Site-specific values SHALL be absent or marked as pending validation in draft metadata. Known generic patterns MAY be supplied from a platform template with provenance, never claimed as site verification. Profile overrides SHALL resolve to supported operations and pass schema validation.

#### Scenario: cross-game-bootstrap
- **WHEN** a Fandom target is bootstrapped from another game
- **THEN** its URLs SHALL use the target domain, description SHALL not claim the reference game/version, and target page/taxonomy identities SHALL remain unverified until filled and validated.

#### Scenario: invalid-reference-extraction
- **WHEN** reusable source extraction or profile override violates the shared schema
- **THEN** bootstrap SHALL fail with diagnostics rather than copying invalid rules into a registered strategy.

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

### Requirement: strategy-registry-sync

Registry metadata SHALL match the authoritative strategy frontmatter. Production lookup SHALL require a matching registry entry and a non-draft strategy that passes current validation; an unregistered file SHALL NOT become eligible merely because its marker is absent. Newly generated drafts SHALL retain explicit draft metadata until validated freeze and SHALL be excluded from production lookup. Previously frozen unmarked strategies MAY remain eligible subject to current schema validation; a legacy bootstrap marker SHALL be treated as draft regardless of existing registry membership. Re-freeze SHALL apply the same validations as first freeze rather than bypassing them based on marker shape.

#### Scenario: legacy-bootstrap-marker
- **WHEN** registry points to a strategy retaining a Bootstrapped or scaffold marker
- **THEN** production lookup SHALL reject its draft status until validated freeze.

#### Scenario: legacy-frozen-strategy
- **WHEN** an unmarked existing strategy passes current schema and has valid target identity
- **THEN** it SHALL remain usable without forcing a new site-analysis run.

## ADDED Requirements

### Requirement: fandom-extraction-configuration-migration

The Fandom template and Neon Abyss strategy SHALL use supported extraction configuration, translating lazyload rules to lazyload config, edit/TOC removal to supported cleanup/selectors, normalization to supported normalizer names, and removing dead descriptive pipeline fields. Migration SHALL preserve intended supported behavior through sample evidence, not mechanically turn every dictionary key into an operation string. Source changes SHALL NOT regenerate or mutate historical manifests, Markdown or downstream ingests.

#### Scenario: migrated-fandom-template
- **WHEN** target-specific fields are filled in the Fandom template
- **THEN** shared schema and Gate SHALL accept its cleanup/lazyload/normalization configuration.

#### Scenario: neon-behavior-regression
- **WHEN** Neon Abyss sample conversion runs with migrated configuration
- **THEN** supported lazyload/edit/TOC/ambox/image-wrapper and normalization behavior SHALL match approved fixtures without requiring historical batch re-extraction.
