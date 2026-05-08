# Specification Delta: mediawiki-api-extraction-pipeline

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认扩展管线 Phase B 支持内容获取策略分支（wikitext / html_rendered / hybrid）

## 规范真源声明

- 本文件是 `mediawiki-api-extraction-pipeline` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: content-acquisition-strategy-selection
The system SHALL support multiple content acquisition strategies in Phase B, selectable via the site strategy configuration.

#### Scenario: select-html-rendered-strategy
- **WHEN** the site strategy specifies `content_acquisition: html_rendered`
- **THEN** Phase B SHALL use `HtmlRenderedAcquisitionStrategy`
- **AND** it SHALL call `action=parse&prop=text` for each page
- **AND** the returned HTML SHALL be passed through the HTML-to-Markdown converter

#### Scenario: select-wikitext-strategy
- **WHEN** the site strategy specifies `content_acquisition: wikitext_only`
- **THEN** Phase B SHALL continue to use `WikitextOnlyAcquisitionStrategy`
- **AND** behavior SHALL remain unchanged from the existing implementation

#### Scenario: select-hybrid-strategy
- **WHEN** the site strategy specifies `content_acquisition: hybrid_wikitext_plus_rendered`
- **THEN** Phase B SHALL use `HybridAcquisitionStrategy`
- **AND** behavior SHALL remain unchanged from the existing implementation

### Requirement: strategy-registry-extension
The system SHALL extend the strategy registry to include `html_rendered` as a valid content acquisition option.

#### Scenario: register-html-rendered
- **WHEN** `build_pipeline()` is called with a strategy containing `content_acquisition: html_rendered`
- **THEN** it SHALL resolve to `HtmlRenderedAcquisitionStrategy`
- **AND** it SHALL NOT fall back to the default `WikitextOnlyAcquisitionStrategy`

### Requirement: pipeline-phase-b-extension
The system SHALL extend `process_single_page` in Phase B to handle HTML-rendered content.

#### Scenario: process-html-rendered-page
- **WHEN** processing a page with `html_rendered` strategy
- **THEN** the system SHALL:
  1. Fetch HTML via `action=parse&prop=text`
  2. Clean the HTML (remove UI noise, display:none elements)
  3. Convert cleaned HTML to Markdown using the HTML-to-Markdown converter
  4. Convert internal links to relative Markdown links using the title-to-path mapping
  5. Return the final Markdown content with frontmatter

#### Scenario: preserve-frontmatter-extraction
- **WHEN** processing with `html_rendered` strategy
- **THEN** frontmatter fields (name, cost, type, rarity, color, image) SHALL still be extracted from wikitext if available
- **AND** if wikitext is not fetched, frontmatter SHALL be populated from HTML infobox parsing or left empty

### Requirement: discovery-namespace-expansion
The system SHALL expand discovery to cover all target namespaces (0, 3000, 14).

#### Scenario: discover-all-namespaces
- **WHEN** the site strategy specifies `namespaces: [0, 3000, 14]`
- **THEN** Phase A discovery SHALL iterate through all specified namespaces
- **AND** `CategoryMembersDiscoveryStrategy` SHALL call `categorymembers` for each namespace separately
- **AND** `AllPagesDiscoveryStrategy` SHALL call `allpages` for each namespace separately

#### Scenario: deduplicate-across-namespaces
- **WHEN** discovery returns pages from multiple namespaces
- **THEN** the system SHALL deduplicate by `pageid`
- **AND** pages with the same title in different namespaces SHALL be treated as distinct pages

### Requirement: output-path-integration
The system SHALL integrate semantic-directory-mapping into the manifest generation.

#### Scenario: generate-manifest-with-paths
- **WHEN** Phase A builds the manifest
- **THEN** each page entry SHALL include `target_directory` and `target_filename` computed by semantic-directory-mapping rules
- **AND** the link resolver SHALL use these paths for relative link generation

## REMOVED Requirements

### Requirement: sts2-only-namespace-filter
**Reason**: The original pipeline hardcoded ns=3000 filtering. With the expansion to cover StS1 (ns=0) and categories (ns=14), namespace filtering is now configuration-driven via the strategy file.
**Migration**: Update site strategy to specify `namespaces: [0, 3000, 14]` instead of relying on hardcoded ns=3000.
