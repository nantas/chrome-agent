# Specification Delta

## Capability 对齐（已确认）

- Capability: `sample-converter`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: modified
- 用户确认摘要: 用户确认 4 个 capability 无需调整

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: apply-extraction-uses-shared-lib
`sample_converter._apply_extraction()` SHALL be rewritten as a 4-step sequential pipeline calling `lib/extraction/` shared modules, replacing the current 6-phase inline implementation.

#### Scenario: full conversion pipeline
- **WHEN** `_apply_extraction(html, extraction_rules, known_pages)` is called
- **THEN** it SHALL execute in order:
  1. `extract_infobox(full_html, config)` from `lib.extraction.infobox` → returns infobox Markdown string
  2. `preprocess_html(full_html, config, context="explore")` from `lib.extraction.preprocessor` → returns cleaned HTML
  3. `convert_html_to_markdown(cleaned_html, domain, config)` from existing shared module → returns body Markdown
  4. Prepend infobox Markdown before body Markdown if non-empty → returns final Markdown

#### Scenario: infobox not processed twice
- **WHEN** both `extract_infobox()` and `preprocess_html()` operate on the same HTML string
- **THEN** `extract_infobox()` SHALL only read the infobox (return Markdown string), while `preprocess_html()` SHALL remove the infobox container from HTML — no shared mutable state, no double processing

### Requirement: strategy-loader-replaces-load-extraction-rules
`sample_converter._load_extraction_rules()` SHALL be replaced by `lib.strategy_loader` functions.

#### Scenario: loading extraction rules from strategy file
- **WHEN** extraction rules are needed from a strategy file
- **THEN** the code SHALL use `lib.strategy_loader.parse_strategy()` to get the full frontmatter dict, then extract `extraction.*` section from it

## REMOVED Requirements

### Requirement: extract-infobox-private-function
**Reason**: Replaced by `lib.extraction.infobox.extract_infobox()` — unified implementation shared with pipeline path
**Migration**: All callers use `lib.extraction.infobox.extract_infobox()` instead

### Requirement: apply-field-handler-private-function
**Reason**: Handler logic unified into `lib.extraction.infobox` with callback-based execution
**Migration**: Handler dispatch now handled by the shared infobox module via `apply_handler_fn` callback

### Requirement: load-extraction-rules-private-function
**Reason**: Replaced by `lib.strategy_loader.parse_strategy()` (Change 1 infrastructure)
**Migration**: Call `parse_strategy(path)` then access `["extraction"]` key
