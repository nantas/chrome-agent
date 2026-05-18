# Specification Delta

## Capability 对齐（已确认）

- Capability: `crawl-confirmation-gate`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: explore 阶段确认 —— crawl 工作流需在 discovery 后、extraction 前插入确认闸门，agent 生成输出结构树状图通过 ask_user 让用户确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: discovery-summary-consumption

The agent SHALL, when routing a `crawl` intent through the SKILL, first run discovery-only mode and consume the resulting `discovery_summary.json`.

The agent SHALL NOT proceed to extraction without completing the confirmation gate, unless `--yes` is explicitly passed.

#### Scenario: discovery-only execution on crawl intent

- **WHEN** the SKILL detects a `crawl` intent
- **AND** `--yes` is NOT present in the user request
- **THEN** the agent SHALL execute `chrome-agent crawl <url> --discovery-only --format json`
- **AND** the agent SHALL read the `discovery_summary.json` from the returned artifacts

#### Scenario: yes-flag bypass

- **WHEN** the SKILL detects a `crawl` intent
- **AND** the user request includes `--yes` or the agent has been instructed to skip confirmation
- **THEN** the agent SHALL execute the normal atomic crawl without the confirmation gate
- **AND** the agent SHALL NOT run discovery-only as a separate step

### Requirement: tree-diagram-generation

The agent SHALL build a tree diagram from `discovery_summary.json` showing the output directory structure with page counts.

The tree diagram SHALL include:
- Each category directory with its page count
- Whether the directory has an index page (`is_index_page: true` → `index.md`)
- 3-5 sample page names per category for context
- Excluded categories with their page counts and exclusion reasons
- Unclassified/misc pages with count
- Discovery method and any caveats
- Estimated total time

The agent MAY use emoji (📁 📄 ⚠️ 📊) or plain ASCII to render the tree.

#### Scenario: api-pipeline-tree

- **WHEN** `discovery_summary.discovery_method` is `"homepage"` or `"allpages"`
- **AND** the summary contains `categories` with precise `page_count` values
- **THEN** the tree SHALL show per-category page counts as exact numbers
- **AND** the tree SHALL include sample page names from `categories[*].sample_pages`

#### Scenario: scrapling-tree-with-caveats

- **WHEN** `discovery_summary.discovery_method` is `"first_level_links"`
- **AND** the summary contains `caveats`
- **THEN** the tree SHALL prominently display the caveats
- **AND** the tree SHALL label page counts as estimates (e.g., "≈ 50+ pages")

#### Scenario: partial-discovery-tree

- **WHEN** `discovery_summary.warnings` is non-empty
- **THEN** the tree SHALL include the warnings below the tree
- **AND** the agent SHALL NOT block confirmation solely due to warnings

### Requirement: user-confirmation-ask

The agent SHALL present the tree diagram to the user via `ask_user` with three options: proceed, adjust (exclude categories), or cancel.

The agent SHALL use a structured `ask_user` interview with `type: "preview"` so the user can see the tree diagram in the preview pane alongside the options.

#### Scenario: proceed-option

- **WHEN** the user selects "proceed"
- **THEN** the agent SHALL execute `chrome-agent crawl <url> --from-manifest <manifest_path>`
- **AND** the agent SHALL pass the original `discovery_summary.manifest_path` as the manifest path
- **AND** the agent SHALL NOT re-run discovery

#### Scenario: adjust-option

- **WHEN** the user selects "adjust"
- **THEN** the agent SHALL present a multi-select of categories to exclude (from `discovery_summary.categories[*].name`)
- **AND** the agent SHALL build an updated tree with the excluded categories removed
- **AND** the agent SHALL re-present the updated tree for final confirmation
- **AND** upon final confirm, the agent SHALL execute `chrome-agent crawl <url> --from-manifest <manifest_path> --exclude-category <name> ...`

#### Scenario: cancel-option

- **WHEN** the user selects "cancel"
- **THEN** the agent SHALL stop the crawl workflow
- **AND** the agent SHALL report that the crawl was cancelled by user

### Requirement: extraction-execution

After user confirmation, the agent SHALL execute extraction + assembly using the confirmed manifest.

The agent SHALL pass all user-adjusted exclusion parameters as CLI flags, not as strategy modifications.

#### Scenario: confirmed-execution

- **WHEN** the user confirms the crawl scope
- **THEN** the agent SHALL run `chrome-agent crawl <url> --from-manifest <manifest_path> [--exclude-category X ...] [--max-pages N]`
- **AND** the agent SHALL NOT modify the strategy file
- **AND** the agent SHALL pass through the CLI result using standard result packaging

#### Scenario: max-pages-limit

- **WHEN** the user specifies a `--max-pages` limit during confirmation
- **THEN** the agent SHALL pass it to the extraction phase
- **AND** the agent SHALL inform the user that discovery was complete but extraction is capped

### Requirement: confirmation-gate-error-handling

The agent SHALL handle discovery-only failures according to the pipeline's established error semantics.

#### Scenario: discovery-total-failure

- **WHEN** `--discovery-only` returns `result: "failure"` or exit code ≥ 10
- **THEN** the agent SHALL surface the failure to the user
- **AND** the agent SHALL NOT proceed to extraction
- **AND** the agent SHALL present the pipeline's remediation as-is

#### Scenario: discovery-partial-failure

- **WHEN** `--discovery-only` returns `result: "partial_success"`
- **AND** `discovery_summary.failure_rate` ≤ 0.5
- **THEN** the agent SHALL present the tree with warnings
- **AND** the agent SHALL let the user decide whether to proceed
