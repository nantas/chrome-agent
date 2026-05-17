# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: explore 工作流增加 Agent Gate 行为规范，强化样本质量自检报告先于样本展示、文件路径输出、agent 自行对比审查、全量重测等要求

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

#### Scenario: self-check-pipeline (modified)
- **WHEN** sample conversion is complete
- **THEN** the system SHALL run ALL S1-S12 checks (not just S1-S7) against each sample
- **THEN** the system SHALL produce a per-sample and overall summary report
- **THEN** the system SHALL present the self-check summary BEFORE any sample content
- **THEN** the agent SHALL follow the agent-gate rules defined in ADDED Requirements below

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

### Requirement: pipeline-dependency-preflight

The deep discovery pipeline (`scripts/explore/main.py`) SHALL verify all required Python dependencies at startup and exit with a clear error message if any are missing.

#### Scenario: main-py-dependency-self-check
- **WHEN** `python3 scripts/explore/main.py` is invoked
- **THEN** the script SHALL attempt to import `bs4`, `yaml`, and `selectolax` before executing any pipeline phase
- **THEN** if any import fails, the script SHALL print to stderr: `FATAL: Missing dependencies: <package-list>`
- **THEN** the script SHALL print to stderr: `Install with: pip3 install -r scripts/explore/requirements.txt`
- **THEN** the script SHALL exit with code 1

#### Scenario: deps-file-declaration
- **WHEN** a developer or operator inspects `scripts/explore/`
- **THEN** a `requirements.txt` file SHALL be present listing `beautifulsoup4>=4.12`, `pyyaml>=6.0`, `markdownify>=0.11`, and `selectolax>=0.3`

### Requirement: agent-gate-self-check-before-presentation

The agent SHALL run all S1-S12 self-checks and present the pass/fail summary BEFORE showing any sample Markdown content to the user.

#### Scenario: self-check-report-first
- **WHEN** sample conversion is complete and agent prepares to present results
- **THEN** the agent SHALL output a summary table: `{check_id, status, detail}` for all S1-S12 checks across all samples
- **THEN** the agent SHALL present the overall pass rate (X/Y samples passed, Z issues total)
- **THEN** the agent SHALL NOT output raw Markdown content until the user has seen and acknowledged the self-check report
- **THEN** if all samples pass all checks, the agent SHALL state "✅ All samples passed" and present content
- **THEN** if any sample has failures, the agent SHALL categorize them as fixable/non-fixable and present the remediation plan

### Requirement: agent-gate-sample-file-paths

The agent SHALL write all converted samples to files under `outputs/<run-tag>/` and SHALL present the absolute file paths to the user.

#### Scenario: sample-files-written-to-outputs
- **WHEN** sample conversion is complete
- **THEN** each sample SHALL be written as a `.md` file under `outputs/<run-tag>/`
- **THEN** the file naming SHALL follow the pattern: `{page_type}-{page_title_slugified}.md`
- **THEN** the agent SHALL list all output file paths explicitly in the results presentation
- **THEN** the agent SHALL NOT only print Markdown content to stdout without saving to files

### Requirement: agent-gate-self-audit-before-user-review

The agent SHALL perform a self-audit comparing source HTML content against converted Markdown BEFORE asking the user to review quality.

#### Scenario: agent-self-audits
- **WHEN** sample conversion is complete and agent prepares to present to user
- **THEN** the agent SHALL run a diagnostic function that compares:
  - Source `mw-headline` sections vs Markdown headings
  - Source infobox data-source fields vs Markdown infobox table rows
  - Source `<tr>` count vs Markdown table rows
  - Source images (excluding skip_patterns) vs Markdown `![]()` count
  - Source `<a href="/wiki/">` count vs Markdown full URL link count
- **THEN** the agent SHALL produce a structured discrepancy list before presenting to the user
- **THEN** the agent SHALL NOT delegate the QA responsibility to the user

### Requirement: agent-gate-full-retest-on-converter-change

When the converter or extraction rules are modified in response to audit findings, the agent SHALL re-convert and re-check ALL samples, not just the one that triggered the fix.

#### Scenario: retest-all-after-fix
- **WHEN** the converter code or extraction rules are modified
- **THEN** the agent SHALL re-run conversion on ALL sample pages
- **THEN** the agent SHALL re-run ALL S1-S12 checks on ALL samples
- **THEN** the agent SHALL NOT claim "fixed" based on a single sample test

### Requirement: agent-gate-iteration-limit

The agent SHALL limit the fix→retest→present cycle to at most 3 iterations before requiring explicit user direction.

#### Scenario: max-3-iterations
- **WHEN** the agent has completed 3 cycles of fix→retest→present
- **AND** failures still exist
- **THEN** the agent SHALL present the remaining issues and ask the user to decide: continue fixing / accept as-is / adjust scope
- **THEN** the agent SHALL NOT continue to a 4th iteration without user confirmation
