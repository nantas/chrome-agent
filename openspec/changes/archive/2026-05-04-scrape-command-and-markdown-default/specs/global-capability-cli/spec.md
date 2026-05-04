# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-capability-cli`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 CLI 命令面新增 `scrape` 命令，扩展 `crawl` 参数面（--no-markdown、--merge、--concurrency）

## 规范真源声明

- 本文件是 `global-capability-cli` 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/global-capability-cli/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Scrape command surface

The CLI SHALL expose `scrape` as a first-class command alongside `explore`, `fetch`, `crawl`, `doctor`, and `clean`.

#### Scenario: Command inventory with scrape

- **WHEN** an operator invokes `chrome-agent --help`
- **THEN** the CLI SHALL present `scrape` as the sixth first-class command
- **AND** it SHALL describe `scrape` as a strategy-free recursive crawling workflow
- **AND** it SHALL describe `crawl` as a strategy-guided bounded traversal workflow (to distinguish the two)

### Requirement: Scrape command routing

The `scrape` command SHALL route into the repository-local content retrieval workflow.

#### Scenario: Scrape command execution

- **WHEN** `chrome-agent scrape <target>` is invoked
- **THEN** the CLI SHALL dispatch to a repository-local strategy-free scraping workflow
- **AND** the result SHALL identify `workflow: content_retrieval`
- **AND** the result SHALL include all per-page `.md` files (or `.html` if `--no-markdown`) in `artifacts`

### Requirement: Crawl parameter extensions

The CLI SHALL extend the `crawl` command with new parameters for Markdown output control.

#### Scenario: Crawl Markdown parameters

- **WHEN** `chrome-agent crawl <url> --no-markdown` is invoked
- **THEN** the command SHALL skip Phase 2 Markdown conversion and retain `.html` output

- **WHEN** `chrome-agent crawl <url> --merge` is invoked
- **THEN** the command SHALL merge all per-page `.md` files into `crawl-output.md`

- **WHEN** `chrome-agent crawl <url> --concurrency 10` is invoked
- **THEN** Phase 2 Markdown conversion SHALL run with up to 10 concurrent Scrapling invocations

### Requirement: Scrape parameter surface

The CLI SHALL define a complete parameter surface for the `scrape` command.

#### Scenario: Scrape parameter inventory

- **WHEN** an operator invokes `chrome-agent scrape --help`
- **THEN** it SHALL present the following parameters:
  - `--max-pages <n>` — maximum pages to traverse (default: 10)
  - `--no-same-domain` — allow cross-domain link following (default: same-domain is on)
  - `--match <glob>` — URL pathname pattern filter
  - `--no-markdown` — retain HTML output, skip Markdown conversion
  - `--merge` — merge all `.md` files into a single document
  - `--concurrency <n>` — Phase 2 concurrent conversion limit (default: 5)
  - `--fetcher <name>` — override Scrapling fetcher (default: `get`)
  - `--keep-html` — retain intermediate `.html` files alongside `.md`
  - `--report` — force durable report emission
  - `--no-report` — disable durable report emission

## MODIFIED Requirements

### Requirement: Global command surface

The system SHALL expose `chrome-agent` as the repo-backed low-level explicit execution surface for this repository's external capabilities.

The CLI SHALL define these first-class commands:
- `explore`
- `fetch`
- `crawl`
- `scrape`
- `doctor`
- `clean`

#### Scenario: Command inventory

- **WHEN** an operator invokes `chrome-agent --help`
- **THEN** the CLI SHALL present the six first-class commands above
- **AND** it SHALL describe `fetch`, `explore`, `crawl`, and `scrape` as explicit backend workflows rather than as the only user-facing intent layer
