# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户已通过对话确认本次重构不新增外部行为，只将现有行为提取为策略接口。新增 capabilities 词汇表、策略接口契约、namespace 场景、管线核心流程与挂载点描述。

## 规范真源声明

- 本文件是 `mediawiki-api-extraction` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本次只追加 MODIFIED Requirements，不修改或删除任何已有 Requirements

## MODIFIED Requirements

### Requirement: Capabilities 受控词汇表

The system SHALL define a controlled vocabulary for MediaWiki API capabilities, enabling strategy-driven validation instead of hardcoded capability checks.

The following capabilities SHALL be recognized:

| Capability ID | Type | Description |
|--------------|------|-------------|
| `page_list` | `required` | Ability to enumerate pages via `action=query&list=allpages` or similar |
| `category_lookup` | `required` | Ability to query category memberships per page via `action=query&prop=categories` |
| `wikitext_parse` | `required` | Ability to fetch wikitext content via `action=parse&prop=wikitext` |
| `html_parse` | `optional` | Ability to fetch rendered HTML via `action=parse&prop=text` |
| `imageinfo_query` | `optional` | Ability to query image metadata via `action=query&prop=imageinfo` |
| `redirect_resolve` | `optional` | Ability to resolve redirects via `action=query&prop=redirects` |

The system SHALL validate that the strategy's declared `api.capabilities` superset covers the union of `required_capabilities` from all chosen strategies (DiscoveryStrategy + ContentAcquisitionStrategy). Validation SHALL NOT use a hardcoded required set.

#### Scenario: Validation passes with complete strategy capabilities

- **WHEN** the strategy declares `capabilities: [page_list, category_lookup, wikitext_parse]`
- **AND** the selected DiscoveryStrategy requires `{page_list, category_lookup}`
- **AND** the selected ContentAcquisitionStrategy requires `{wikitext_parse}`
- **THEN** validation SHALL pass because the union `{page_list, category_lookup, wikitext_parse}` is covered

#### Scenario: Validation fails with missing capability

- **WHEN** the strategy declares `capabilities: [page_list]` (missing `wikitext_parse`)
- **AND** the selected ContentAcquisitionStrategy requires `{wikitext_parse}`
- **THEN** validation SHALL fail with a message indicating `wikitext_parse` is missing

#### Scenario: Validation with optional capabilities

- **WHEN** the strategy declares only `required` capabilities (e.g., `[page_list, category_lookup, wikitext_parse]`)
- **AND** the selected strategies only require `required` capabilities
- **THEN** validation SHALL pass without requiring optional capabilities

### Requirement: 策略接口契约

The system SHALL define five strategy interfaces as Python `Protocol` classes, each responsible for a distinct extraction concern. The interfaces SHALL be injectable at pipeline composition time.

The five strategy interfaces SHALL be:

1. **DiscoveryStrategy**: Page and category discovery, page classification
2. **ContentAcquisitionStrategy**: Content source fetching (wikitext, rendered HTML, images)
3. **LinkResolver**: Wiki link to Markdown relative path resolution
4. **TemplateProcessor**: Frontmatter extraction, template expansion, cleanup
5. **ListPageAssembler**: Index page assembly (DPL table replacement, directory index)

Each strategy interface SHALL declare a `required_capabilities` property returning a set of capability IDs from the controlled vocabulary.

Each strategy interface SHALL have at least one built-in default implementation that preserves the current extraction behavior.

#### Scenario: DiscoveryStrategy interface

- **WHEN** a DiscoveryStrategy implementation is used in the pipeline
- **THEN** it SHALL expose the following methods:
  - `discover_pages(client: ApiClient, strategy: dict) -> list[dict]`
  - `discover_categories(client: ApiClient, page_titles: list[str]) -> dict[str, list[str]]`
  - `classify_page(page_title, categories, list_pages, page_categories, category_filters) -> str`
  - `fetch_list_pages(client: ApiClient, list_pages: dict) -> dict[str, str]`
  - `required_capabilities -> set[str]`
- **AND** the default implementation `AllPagesDiscoveryStrategy` SHALL use `action=query&list=allpages` with `apnamespace` from `strategy.api.namespace` (default `0`)

#### Scenario: ContentAcquisitionStrategy interface

- **WHEN** a ContentAcquisitionStrategy implementation is used in the pipeline
- **THEN** it SHALL expose the following methods:
  - `fetch_page_content(client: ApiClient, title: str, strategy: dict) -> dict`
  - `required_capabilities -> set[str]`
- **AND** the default implementation `WikitextOnlyAcquisitionStrategy` SHALL fetch `prop=wikitext` only

#### Scenario: LinkResolver interface

- **WHEN** a LinkResolver implementation is used in the pipeline
- **THEN** it SHALL expose the following methods:
  - `convert_links(text: str, manifest_pages: list[dict], source_dir: str) -> str`
  - `resolve(target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str`
- **AND** the default implementation `ExactTitleLinkResolver` SHALL use exact title matching (current `convert_wiki_links` behavior) and a greedy regex for markdown link parsing

#### Scenario: TemplateProcessor interface

- **WHEN** a TemplateProcessor implementation is used in the pipeline
- **THEN** it SHALL expose the following methods:
  - `extract_frontmatter(wikitext: str, fields: list[str]) -> dict`
  - `expand_templates(text: str, template_map: dict) -> tuple[str, list[str]]`
  - `remove_infobox(wikitext: str, fields: list[str]) -> str`
  - `clean_remaining_templates(text: str) -> str`
- **AND** the default implementation `SimpleSubstitutionTemplateProcessor` SHALL use simple string substitution for template expansion

#### Scenario: ListPageAssembler interface

- **WHEN** a ListPageAssembler implementation is used in the pipeline
- **THEN** it SHALL expose the following method:
  - `assemble_index(list_page_title, pages_in_dir, list_content, frontmatter_fields, domain) -> str`
- **AND** the default implementation `FrontmatterDrivenListPageAssembler` SHALL build index.md from frontmatter data with a data-driven DPL table replacement

### Requirement: Pipeline 策略注入

The system SHALL support strategy injection at pipeline composition time via a `build_pipeline` function or equivalent mechanism.

The pipeline SHALL accept a `PipelineStrategies` container holding one instance of each strategy interface. When no explicit strategy is configured (default), all five default implementations SHALL be used.

The pipeline SHALL validate strategy compatibility before execution:
1. Collect `required_capabilities` union from all selected strategies
2. Verify the strategy's `api.capabilities` field covers the union
3. Fail with a clear error message if capabilities are insufficient

The `content_profile` field in `strategy.api` SHALL allow declarative strategy selection. When absent, all default strategies SHALL be used.

#### Scenario: Default strategy composition

- **WHEN** `strategy.api.content_profile` is absent from the strategy file
- **THEN** the pipeline SHALL compose all default implementations:
  - `discovery_strategy: "allpages"` → `AllPagesDiscoveryStrategy`
  - `content_acquisition: "wikitext_only"` → `WikitextOnlyAcquisitionStrategy`
  - `link_resolver: "exact_title_match"` → `ExactTitleLinkResolver`
  - `template_processor: "simple_substitution"` → `SimpleSubstitutionTemplateProcessor`
  - `list_page_assembler: "frontmatter_driven"` → `FrontmatterDrivenListPageAssembler`
- **AND** the output behavior SHALL be identical to the pre-refactoring pipeline

#### Scenario: Strategy composition with content_profile

- **WHEN** `strategy.api.content_profile` specifies a subset of strategies (e.g., only `discovery_strategy: "category_members"`)
- **THEN** the pipeline SHALL use the specified strategy for that concern
- **AND** unspecified concerns SHALL fall back to their default implementations

### Requirement: Namespace 策略化

The system SHALL read the namespace parameter from `strategy.api.namespace` for page discovery. When not specified, namespace SHALL default to `0` (main namespace).

The `discover_all_pages` function (or equivalent default DiscoveryStrategy implementation) SHALL use the strategy-specified namespace in the `apnamespace` parameter of the `action=query&list=allpages` request.

#### Scenario: Namespace from strategy

- **WHEN** a strategy specifies `api.namespace: 3000`
- **THEN** `discover_all_pages` SHALL use `apnamespace=3000`
- **AND** only pages in namespace 3000 SHALL be discovered

#### Scenario: Namespace default

- **WHEN** a strategy does NOT specify `api.namespace`
- **THEN** `discover_all_pages` SHALL use `apnamespace=0`
- **AND** only main-namespace pages SHALL be discovered

### Requirement: 管线核心流程与策略挂载点

The system SHALL maintain a stable three-phase pipeline structure with clearly defined strategy mount points. The core flow SHALL be:

```
Phase A (Page Discovery)  ─── 委托 → DiscoveryStrategy
     │
     ▼
Phase B (Content Extraction)  ─── 委托 → ContentAcquisitionStrategy
     │                                    ┌─ LinkResolver
     │                                    ├─ TemplateProcessor
     │                                    └─ (utility: table converter, formatting)
     ▼
Phase C (Output Assembly)  ─── 委托 → ListPageAssembler
                                    (复用 LinkResolver)
```

Each phase SHALL accept its delegated strategy interface(s) as parameters. Strategy objects SHALL be stateless (no mutable internal state between page invocations) to support concurrent execution.

The Phase A manifest (page inventory + category mapping) SHALL be the shared data structure passed between phases.

#### Scenario: Core flow stability

- **WHEN** the pipeline executes with any valid strategy composition
- **THEN** the three-phase flow SHALL always execute in order: A → B → C
- **AND** Phase A manifest SHALL be the sole data bridge between phases
- **AND** Phase B SHALL NOT depend on Phase C implementation details
- **AND** Phase C SHALL NOT perform content extraction (only assembly and linking)

#### Scenario: Stateless strategy constraints

- **WHEN** a strategy implementation is called concurrently (Phase B thread pool)
- **THEN** the strategy SHALL NOT maintain mutable per-invocation state
- **AND** all state SHALL be contained in the return values or passed as parameters
