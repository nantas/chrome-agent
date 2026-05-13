# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: 新增完整的 explore 工作流（deep discovery → 模板选择 → 交互确认 → 样本自检 → 策略冻结）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: deep-discovery

The system SHALL, when `explore` is executed against a URL not covered by an existing strategy, automatically execute a deep discovery pipeline before reporting a strategy gap.

#### Scenario: chain-engine-probe
- **WHEN** `explore` starts with no matching strategy
- **THEN** the system SHALL attempt engine chain: `scrapling-get` → `obscura-fetch` → `cloakbrowser-fetch` → `chrome-devtools-mcp`
- **THEN** the system SHALL record for each engine: `status` (success/failure/partial), `http_status` or `error_type`, `page_title`, `content_length`

#### Scenario: api-discovery
- **WHEN** any engine in the chain succeeds
- **THEN** the system SHALL probe for known API endpoints: `/api.php` (MediaWiki), `/wp-json` (WordPress), `/graphql` (GraphQL), `/sitemap.xml`, `/robots.txt`
- **THEN** the system SHALL record for each detected API: `type`, `base_url`, `version`, `capabilities`

#### Scenario: structure-mapping
- **WHEN** page content is successfully retrieved
- **THEN** the system SHALL extract the page type (home/list/article/gallery) based on DOM features
- **THEN** the system SHALL identify nav structure and extract top-level section labels (≤10 items)
- **THEN** the system SHALL NOT extract the complete internal link topology
- **THEN** the system SHALL detect content structure: presence of tables, infoboxes, list/card patterns

#### Scenario: protection-identification
- **WHEN** the engine chain produces failures or partial results
- **THEN** the system SHALL identify the protection mechanism (cloudflare-turnstile / cloudflare-managed / login-wall / rate-limit / none)
- **THEN** the system SHALL record the detection basis (HTTP status, DOM markers, error message)

### Requirement: user-interactive-confirmation

The system SHALL, after deep discovery, interact with the user via ask_user to confirm crawl scope before generating samples.

#### Scenario: scope-selection
- **WHEN** deep discovery has identified the site's content sections
- **THEN** the system SHALL present the detected sections and ask the user to select: "all" / "specific sections" / "to be specified"
- **THEN** the system SHALL ask the user to select page granularity: "summary + individual" / "individual only" / "summary only"
- **THEN** the system SHALL note if certain sections have only summary pages (no individual entity pages)

#### Scenario: sample-selection
- **WHEN** the scope is confirmed
- **THEN** the system SHALL recommend 4-8 sample pages covering each content type selected
- **THEN** the system SHALL prioritize: most content-rich pages, edge cases (with/without infobox)
- **THEN** the system SHALL present the sample list to the user for confirmation before proceeding

### Requirement: strategy-scaffold-generation

The system SHALL generate a strategy scaffold file at `sites/strategies/<domain>/strategy.md` based on deep discovery results.

#### Scenario: scaffold-from-template
- **WHEN** deep discovery is complete and scope is confirmed
- **THEN** the system SHALL select a platform template from `sites/templates/` based on detected platform type
- **THEN** the system SHALL fill the template with: `domain`, `protection_level`, `anti_crawl_refs`, `structure.pages[]`, `api` config, `extraction` rules
- **THEN** the system SHALL mark the scaffold with `# Auto-generated scaffold — review recommended` in the file header

### Requirement: sample-conversion-and-self-check

The system SHALL convert sample pages to Markdown and run self-checks before presenting results to the user.

#### Scenario: convert-samples
- **WHEN** scope and samples are confirmed
- **THEN** the system SHALL fetch each sample using the determined fetcher/API path
- **THEN** the system SHALL apply the extraction rules from the strategy scaffold
- **THEN** the system SHALL produce Markdown output per page with YAML frontmatter

#### Scenario: self-check-pipeline
- **WHEN** sample conversion is complete
- **THEN** the system SHALL run S1-S7 checks against each sample (see `sample-self-check` spec)
- **THEN** the system SHALL produce a summary report: `{samples[], overall_pass, overall_fail}`
- **THEN** the system SHALL present the summary to the user before displaying sample content

### Requirement: strategy-freeze

The system SHALL allow the user to freeze the strategy after sample review.

#### Scenario: freeze-on-approval
- **WHEN** the user confirms sample quality is acceptable
- **THEN** the system SHALL finalize the strategy file (remove scaffold marker)
- **THEN** the system SHALL append the entry to `sites/strategies/registry.json`
- **THEN** the system SHALL generate the final explore report

#### Scenario: iterate-on-feedback
- **WHEN** the user provides feedback on sample quality issues
- **THEN** the system SHALL update the strategy extraction rules based on feedback
- **THEN** the system SHALL re-run conversion and self-check
- **THEN** the system SHALL re-present samples for review
