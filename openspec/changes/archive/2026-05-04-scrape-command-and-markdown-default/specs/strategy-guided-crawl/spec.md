# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-guided-crawl`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 crawl 默认输出从 HTML 改为 Markdown，新增 --no-markdown、--merge、--concurrency 参数

## 规范真源声明

- 本文件是 `strategy-guided-crawl` 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/strategy-guided-crawl/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Default Markdown output

The `crawl` command SHALL default to producing Markdown output for each crawled page.

#### Scenario: Default Markdown mode

- **WHEN** `crawl <url>` is invoked without `--no-markdown`
- **THEN** after strategy-guided traversal completes, the command SHALL invoke the shared Markdown conversion pipeline
- **AND** each successfully visited page SHALL produce a `.md` file via `scrapling extract <fetcher> <url> <path>.md --ai-targeted`
- **AND** intermediate `.html` files SHALL be cleaned up after conversion

#### Scenario: HTML fallback mode

- **WHEN** `crawl <url> --no-markdown` is invoked
- **THEN** the command SHALL skip Phase 2 Markdown conversion
- **AND** it SHALL retain intermediate `.html` files as the final output
- **AND** the behavior SHALL match the pre-change crawl implementation

### Requirement: Optional merged output

The `crawl` command SHALL support merging all per-page Markdown files into a single document.

#### Scenario: Merge flag

- **WHEN** `crawl <url> --merge` is invoked
- **THEN** after Phase 2 conversion completes, the command SHALL concatenate all `.md` files into `crawl-output.md`
- **AND** the merged document SHALL include a table of contents derived from each page's first `#` heading

### Requirement: Concurrent Markdown conversion

The `crawl` command SHALL support concurrent Phase 2 Markdown conversion.

#### Scenario: Default concurrency

- **WHEN** Phase 2 conversion runs without an explicit `--concurrency` value
- **THEN** the default concurrency SHALL be 5 concurrent Scrapling invocations

#### Scenario: Custom concurrency

- **WHEN** `crawl <url> --concurrency 10` is invoked
- **THEN** Phase 2 conversion SHALL run with up to 10 concurrent Scrapling invocations

### Requirement: Phase 2 partial failure semantics

The `crawl` command SHALL report `partial_success` when Phase 2 Markdown conversion has failures.

#### Scenario: Conversion partial failure

- **WHEN** Phase 1 traversal succeeds but some Phase 2 conversions fail
- **THEN** the final result SHALL be `partial_success`
- **AND** the manifest SHALL record failed URLs in `phase2.failed_urls`
- **AND** successfully converted `.md` files SHALL remain available

## MODIFIED Requirements

### Requirement: Partial failure semantics

The crawl capability SHALL support partial completion when some pages succeed and others fail.

#### Scenario: Mixed page outcomes (Phase 1)

- **WHEN** a crawl retrieves some pages successfully but encounters blocked, rate-limited, or failed pages during traversal
- **THEN** the command SHALL return `partial_success`
- **AND** it SHALL identify the successful outputs and the pages or stages that failed

#### Scenario: Phase 2 conversion failures

- **WHEN** Phase 1 completes successfully but Phase 2 Markdown conversion has failures
- **THEN** the command SHALL return `partial_success`
- **AND** the successful `.md` files SHALL remain as usable artifacts
- **AND** the manifest SHALL identify which URLs failed conversion
