# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-workflow-skill`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: explore 阶段确认 —— SKILL.md 新增 Crawl Confirmation Gate 章节，在 `crawl` 意图路由后插入 discovery → tree → ask_user → proceed 工作流

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/global-workflow-skill/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: crawl-confirmation-gate-interception

When the SKILL routes a user request to `crawl` and the `--yes` flag is NOT present, the SKILL SHALL intercept the workflow before execution and invoke the Crawl Confirmation Gate.

The Crawl Confirmation Gate SHALL execute in three stages:
1. **Discovery**: Run `chrome-agent crawl <url> --discovery-only --format json`
2. **Presentation**: Build a tree diagram from `discovery_summary.json` and present via `ask_user`
3. **Execution**: On user confirmation, run `chrome-agent crawl <url> --from-manifest <manifest_path> [--exclude-category X ...] [--max-pages N]`

The SKILL SHALL NOT proceed to extraction without completing the confirmation gate.

#### Scenario: crawl-intent-triggers-gate

- **WHEN** the SKILL detects a `crawl` intent
- **AND** `--yes` is NOT present in the user's request
- **THEN** the SKILL SHALL execute discovery-only first
- **AND** the SKILL SHALL build and present the tree diagram
- **AND** the SKILL SHALL wait for user response before proceeding

#### Scenario: crawl-intent-with-yes-bypasses-gate

- **WHEN** the SKILL detects a `crawl` intent
- **AND** `--yes` is present in the user's request
- **THEN** the SKILL SHALL execute the normal atomic crawl without the confirmation gate
- **AND** the SKILL SHALL NOT run discovery-only as a separate step

#### Scenario: crawl-intent-with-from-manifest-bypasses-gate

- **WHEN** the SKILL detects a `crawl` intent
- **AND** `--from-manifest` is present in the user's request
- **THEN** the SKILL SHALL assume confirmation was already completed
- **AND** the SKILL SHALL execute crawl directly from the manifest without the gate

### Requirement: crawl-gate-tree-presentation

The SKILL SHALL read `discovery_summary.json` from the discovery-only result and build a tree diagram.

The tree diagram SHALL include, at minimum:
- Each category directory with its page count
- Whether the directory has an index page
- 3-5 sample page names per category for user context
- Excluded categories with reasons
- Unclassified/misc page count
- Discovery method
- Caveats (if present, especially for Scrapling path)
- Warnings (if present)
- Estimated total time

The SKILL MAY render the tree using emoji, ASCII, or plain Markdown — the format is presentation-layer, not spec-enforced.

#### Scenario: tree-from-api-discovery

- **WHEN** `discovery_method` is `"homepage"` or `"allpages"`
- **THEN** the tree SHALL show exact page counts per category
- **AND** the tree SHALL include sample pages from `categories[*].sample_pages`
- **AND** the tree SHALL list excluded categories with their page counts

#### Scenario: tree-from-scrapling-discovery

- **WHEN** `discovery_method` is `"first_level_links"`
- **THEN** the tree SHALL prominently label page counts as estimates
- **AND** the tree SHALL include `caveats` below the tree structure
- **AND** the tree SHALL explain that only first-level links were discovered

#### Scenario: tree-with-warnings

- **WHEN** `warnings` is non-empty
- **THEN** the tree SHALL include warnings after the tree structure
- **AND** the SKILL SHALL mention that `failure_rate` indicates the fraction of discovery operations that failed

### Requirement: crawl-gate-user-confirmation

The SKILL SHALL present the tree diagram to the user via `ask_user` using a structured interview.

The interview SHALL have at minimum:
- A `type: "preview"` question showing the tree diagram in the preview pane
- Options: proceed, adjust (exclude categories), or cancel

#### Scenario: proceed-executes-extraction

- **WHEN** the user selects "proceed"
- **THEN** the SKILL SHALL run `chrome-agent crawl <url> --from-manifest <manifest_path>`
- **AND** the SKILL SHALL pass any user-specified `--max-pages` limit
- **AND** the SKILL SHALL present the extraction result using standard result packaging

#### Scenario: adjust-filters-and-re-presents

- **WHEN** the user selects "adjust"
- **THEN** the SKILL SHALL present a multi-select of categories from `discovery_summary.categories[*].name`
- **AND** after the user selects categories to exclude, the SKILL SHALL rebuild the tree with those categories removed
- **AND** the SKILL SHALL re-present the updated tree for final confirmation
- **AND** upon final confirm, the SKILL SHALL add `--exclude-category` flags for each excluded category

#### Scenario: cancel-stops-workflow

- **WHEN** the user selects "cancel"
- **THEN** the SKILL SHALL stop the crawl workflow
- **AND** the SKILL SHALL inform the user that the crawl was cancelled

### Requirement: crawl-gate-error-propagation

The SKILL SHALL propagate discovery-only failures according to the pipeline's established error semantics.

#### Scenario: discovery-total-failure

- **WHEN** `--discovery-only` returns `result: "failure"` or exit code ≥ 10
- **THEN** the SKILL SHALL surface the failure to the user using standard result packaging
- **AND** the SKILL SHALL NOT proceed to the tree presentation
- **AND** the SKILL SHALL NOT proceed to extraction

#### Scenario: discovery-partial-failure

- **WHEN** `--discovery-only` returns `result: "partial_success"`
- **AND** `discovery_summary.failure_rate` ≤ 0.5
- **THEN** the SKILL SHALL present the tree with warnings
- **AND** the SKILL SHALL let the user decide whether to proceed

#### Scenario: discovery-summary-missing

- **WHEN** `--discovery-only` returns `result: "success"` but `discovery_summary.json` does not exist or is unreadable
- **THEN** the SKILL SHALL report the error to the user
- **AND** the SKILL SHALL NOT fabricate a tree diagram
- **AND** the SKILL SHALL NOT proceed to extraction

### Requirement: crawl-gate-skill-section

The SKILL.md file SHALL contain a "Crawl Confirmation Gate" section under "Intent Routing", after the existing "Agent Gate (Explore → Crawl Confirmation)" section.

The section SHALL document:
- When the gate is triggered (crawl intent without `--yes`)
- The two-phase flow: discovery → tree → confirmation → execution
- The `--yes` bypass for automation
- The adjust/cancel options
- Error handling for discovery failures

The section SHALL reference the `crawl-confirmation-gate` spec as the behavioral authority.

#### Scenario: skill-md-contains-gate-section

- **WHEN** the SKILL.md is read
- **THEN** it SHALL contain a `## Crawl Confirmation Gate` heading under `## Intent Routing`
- **AND** the section SHALL document the discovery → tree → confirmation → execution flow
- **AND** the section SHALL document `--yes` as the bypass mechanism
