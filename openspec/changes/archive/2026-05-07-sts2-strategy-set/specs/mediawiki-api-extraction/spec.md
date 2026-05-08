# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认新增 5 个策略实现、L6 验证层、跨 namespace 发现与输出、动态内容检测

## 规范真源声明

- 本文件是 `mediawiki-api-extraction` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 策略实现注册表扩展

The system SHALL recognize the following additional strategy IDs in `strategy.api.content_profile`:

| Concern | New ID | Implementation | Description |
|---------|--------|----------------|-------------|
| `discovery_strategy` | `category_members` | `CategoryMembersDiscoveryStrategy` | Discovers pages via `action=query&list=categorymembers` with `cmnamespace` filtering |
| `content_acquisition` | `hybrid_wikitext_plus_rendered` | `HybridAcquisitionStrategy` | Fetches `prop=wikitext` primary, detects `#invoke`/`#dpl` and supplements with `prop=text` and `prop=images` |
| `link_resolver` | `short_name_with_cross_namespace` | `ShortNameLinkResolver` | Resolves short titles (without namespace prefix) and supports cross-namespace link targets |
| `template_processor` | `structured_with_lua_fallback` | `StructuredTemplateProcessor` | Supports multi-parameter templates (positional and named) with Lua module awareness |
| `list_page_assembler` | `hybrid_frontmatter_and_rendered` | `HybridListPageAssembler` | Prefers rendered HTML table extraction, falls back to frontmatter-driven assembly |

When an unknown strategy ID is specified, the system SHALL log a warning and fall back to the default implementation for that concern.

#### Scenario: CategoryMembersDiscoveryStrategy selected

- **WHEN** `strategy.api.content_profile.discovery_strategy` is `"category_members"`
- **THEN** the pipeline SHALL use `CategoryMembersDiscoveryStrategy`
- **AND** page discovery SHALL use `action=query&list=categorymembers` with `cmnamespace` from `strategy.api.namespace`
- **AND** the strategy SHALL iterate over categories defined in `strategy.api.taxonomy.page_categories` to build the page inventory

#### Scenario: HybridAcquisitionStrategy selected

- **WHEN** `strategy.api.content_profile.content_acquisition` is `"hybrid_wikitext_plus_rendered"`
- **THEN** the pipeline SHALL use `HybridAcquisitionStrategy`
- **AND** for each page, the strategy SHALL first fetch `prop=wikitext`
- **AND** if the wikitext contains `#invoke` or `#dpl` syntax, the strategy SHALL additionally fetch `prop=text` and `prop=images`
- **AND** the strategy SHALL return a `PageContent` object containing `wikitext`, `rendered_html`, and `images` fields

#### Scenario: ShortNameLinkResolver selected

- **WHEN** `strategy.api.content_profile.link_resolver` is `"short_name_with_cross_namespace"`
- **THEN** the pipeline SHALL use `ShortNameLinkResolver`
- **AND** the resolver SHALL build a `short_title_index` mapping `title.split(':')[-1]` to full title
- **AND** link resolution SHALL first try exact title match, then short name match, then namespace-prefixed match
- **AND** the resolver SHALL use a stack-based balanced bracket parser for Markdown link targets (replacing greedy regex)
- **AND** relative paths SHALL be computed with `os.path.relpath(target_path, source_dir)`

#### Scenario: StructuredTemplateProcessor selected

- **WHEN** `strategy.api.content_profile.template_processor` is `"structured_with_lua_fallback"`
- **THEN** the pipeline SHALL use `StructuredTemplateProcessor`
- **AND** template expansion SHALL support positional parameters: `{{TemplateName|arg1|arg2}}`
- **AND** template expansion SHALL support named parameters: `{{TemplateName|key1=val1|key2=val2}}`
- **AND** unrecognized templates containing `#invoke` SHALL be logged as "Lua module" warnings rather than generic "unrecognized template" warnings

#### Scenario: HybridListPageAssembler selected

- **WHEN** `strategy.api.content_profile.list_page_assembler` is `"hybrid_frontmatter_and_rendered"`
- **THEN** the pipeline SHALL use `HybridListPageAssembler`
- **AND** if `rendered_html` is available from Phase B, the assembler SHALL extract the actual table structure from the rendered HTML
- **AND** if `rendered_html` is unavailable, the assembler SHALL fall back to frontmatter-driven table assembly

### Requirement: 跨 namespace 发现与输出

The system SHALL support discovering and outputting pages from multiple namespaces simultaneously when the strategy configuration indicates cross-namespace scope.

When `strategy.api.cross_namespace_discovery` is `true` (or when `CategoryMembersDiscoveryStrategy` is used with multiple namespace targets), the system SHALL:

1. Discover pages in each specified namespace independently
2. Build a unified manifest containing all discovered pages with their namespace metadata
3. Generate output directories organized by namespace: `<namespace_canonical>/<category_directory>/`
4. Strip namespace prefixes from filenames: `Slay the Spire 2:Bash` → `Bash.md`
5. Preserve namespace metadata in the manifest for cross-namespace link resolution

#### Scenario: Dual namespace discovery (ns=0 + ns=3000)

- **WHEN** the strategy targets slaythespire.wiki.gg with `cross_namespace_discovery: true`
- **THEN** Phase A SHALL discover pages in both ns=0 and ns=3000
- **AND** ns=3000 pages SHALL be output to `StS2/<category>/` directories
- **AND** ns=0 pages SHALL be output to `StS1/<category>/` directories
- **AND** filenames SHALL NOT contain namespace prefixes
- **AND** the manifest SHALL include a `namespace` field for each page

#### Scenario: Cross-namespace link resolution

- **WHEN** a page in `StS2/Cards/Bash.md` contains `[[Strike (Ironclad)]]`
- **AND** `Strike (Ironclad)` resolves to an ns=0 page
- **THEN** the link SHALL be rewritten to `[Strike (Ironclad)](../../StS1/Cards/Strike_(Ironclad).md)`
- **AND** the relative path SHALL correctly account for both directory depth and namespace boundary crossing

### Requirement: 动态内容检测

The system SHALL detect dynamic content indicators in wikitext and automatically supplement content acquisition with rendered HTML when necessary.

Dynamic content indicators include:
- `{{#invoke:...}}` — Lua module calls
- `{{#dpl:...}}` — DynamicPageList calls
- Any `{{#...:...}}` parser function syntax

When dynamic content indicators are detected, the system SHALL:
1. Fetch `prop=text` (rendered HTML) in addition to `prop=wikitext`
2. Fetch `prop=images` to capture template-generated image references
3. Store both sources in the `PageContent` result for downstream processing

#### Scenario: DRUID infobox with Lua-generated images

- **WHEN** Phase B processes a page whose wikitext contains `{{#invoke:DRUID|...}}`
- **THEN** the system SHALL detect the Lua module call
- **AND** the system SHALL additionally fetch `prop=text` and `prop=images`
- **AND** the image information from `prop=images` SHALL be made available for frontmatter injection

#### Scenario: DPL list page with dynamic table

- **WHEN** Phase B processes a list page whose wikitext contains `{{#dpl:...}}`
- **THEN** the system SHALL detect the DPL call
- **AND** the system SHALL additionally fetch `prop=text`
- **AND** the rendered HTML SHALL be made available for `HybridListPageAssembler`

### Requirement: L6 验证质量层

The system SHALL provide built-in validation scanners that run after Phase C to verify output quality.

The L6 layer SHALL consist of three scanners:

1. **Link Integrity Scanner** (`validate_links`): Scan all output `.md` files and verify that every `[text](path)` internal link points to an existing file. Report broken links with source file and target path.

2. **Content Integrity Checker** (`validate_content_integrity`): Scan all output `.md` files and verify that each file contains non-empty body content beyond frontmatter. Report empty or frontmatter-only files.

3. **Image Availability Validator** (`validate_images`): Extract all `![alt](url)` image references and batch-query `action=query&prop=imageinfo&titles=File:...` to verify image existence. Report unavailable images.

The L6 scanners SHALL run automatically after Phase C when the pipeline executes in full mode. They SHALL also be available as an independent validation command (`--validate`) that can be run against an existing output directory.

L6 validation failures SHALL be recorded as warnings (soft fail) rather than hard failures, allowing the pipeline to complete and report issues for manual review.

#### Scenario: Full pipeline with automatic L6 validation

- **WHEN** the pipeline executes all phases (A → B → C) without `--skip-validation`
- **THEN** the L6 scanners SHALL run automatically after Phase C
- **AND** broken links SHALL be reported with source file and target path
- **AND** empty content files SHALL be reported with page title
- **AND** unavailable images SHALL be reported with image URL
- **AND** validation results SHALL be saved to `validation_report.json` in the output directory

#### Scenario: Independent validation run

- **WHEN** `python -m scripts.mediawiki-api-extract --output /path --validate` is invoked
- **THEN** the system SHALL skip Phase A/B/C and run only the L6 scanners against the existing output directory
- **AND** the system SHALL load `page_manifest.json` and `extraction_results.json` from the output directory for context
- **AND** validation results SHALL be printed to stdout and saved to `validation_report.json`

#### Scenario: Link integrity validation

- **WHEN** `validate_links` scans an output directory containing `StS2/Cards/Bash.md`
- **AND** `Bash.md` contains `[Strike (Ironclad)](../../StS1/Cards/Strike_(Ironclad).md)`
- **AND** the target file `StS1/Cards/Strike_(Ironclad).md` does NOT exist
- **THEN** the scanner SHALL report a broken link: `StS2/Cards/Bash.md → ../../StS1/Cards/Strike_(Ironclad).md`

#### Scenario: Content integrity validation

- **WHEN** `validate_content_integrity` scans an output directory
- **AND** a file contains only YAML frontmatter with no body text
- **THEN** the scanner SHALL report: `page_title: empty content (frontmatter only)`

#### Scenario: Image availability validation

- **WHEN** `validate_images` extracts all `![alt](url)` references from output files
- **AND** batch-queries `action=query&prop=imageinfo&titles=File:...`
- **AND** an image returns no `imageinfo` data
- **THEN** the scanner SHALL report the unavailable image with its referencing page

## MODIFIED Requirements

### Requirement: Pipeline 策略注入

The system SHALL support strategy injection at pipeline composition time via a `build_pipeline` function or equivalent mechanism.

The pipeline SHALL accept a `PipelineStrategies` container holding one instance of each strategy interface. When no explicit strategy is configured (default), all five default implementations SHALL be used.

The pipeline SHALL validate strategy compatibility before execution:
1. Collect `required_capabilities` union from all selected strategies
2. Verify the strategy's `api.capabilities` field covers the union
3. Fail with a clear error message if capabilities are insufficient

The `content_profile` field in `strategy.api` SHALL allow declarative strategy selection. When absent, all default strategies SHALL be used.

The following strategy IDs SHALL be recognized:

| Concern | Default ID | Available IDs |
|---------|-----------|---------------|
| `discovery_strategy` | `allpages` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only` | `wikitext_only`, `hybrid_wikitext_plus_rendered` |
| `link_resolver` | `exact_title_match` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

#### Scenario: Default strategy composition

- **WHEN** `strategy.api.content_profile` is absent from the strategy file
- **THEN** the pipeline SHALL compose all default implementations
- **AND** the output behavior SHALL be identical to the pre-refactoring pipeline

#### Scenario: Strategy composition with content_profile

- **WHEN** `strategy.api.content_profile` specifies a subset of strategies
- **THEN** the pipeline SHALL use the specified strategy for that concern
- **AND** unspecified concerns SHALL fall back to their default implementations

#### Scenario: StS2 strategy composition

- **WHEN** `strategy.api.content_profile` specifies StS2-specific strategies:
  - `discovery_strategy: "category_members"`
  - `content_acquisition: "hybrid_wikitext_plus_rendered"`
  - `link_resolver: "short_name_with_cross_namespace"`
  - `template_processor: "structured_with_lua_fallback"`
  - `list_page_assembler: "hybrid_frontmatter_and_rendered"`
- **THEN** the pipeline SHALL compose the corresponding StS2 strategy implementations
- **AND** the `required_capabilities` union SHALL include `{page_list, category_lookup, wikitext_parse, html_parse, imageinfo_query}`
- **AND** validation SHALL fail if the strategy's `api.capabilities` does not cover this union

#### Scenario: Unknown strategy ID fallback

- **WHEN** `strategy.api.content_profile` specifies an unknown strategy ID (e.g., `discovery_strategy: "unknown"`)
- **THEN** the pipeline SHALL log a warning: `Unknown strategy ID 'unknown' for discovery, using default 'allpages'`
- **AND** the pipeline SHALL use the default implementation for that concern
- **AND** the pipeline SHALL NOT fail
