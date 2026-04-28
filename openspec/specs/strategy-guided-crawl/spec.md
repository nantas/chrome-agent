# strategy-guided-crawl — Spec

## Purpose

Define the formal bounded crawl capability for `chrome-agent`, including strategy gating, traversal boundaries from `entry_points`, `links_to`, and `pagination`, partial-success semantics, and explore-first remediation when strategy coverage is missing.

## Requirements

### Requirement: Strategy-gated crawl eligibility

The system SHALL only execute `crawl` when a matching `site-strategy` exists for the target.

#### Scenario: Crawl with known strategy

- **WHEN** the target domain or page type matches an existing `site-strategy`
- **THEN** the `crawl` command SHALL proceed using that strategy
- **AND** the strategy's `entry_points`, `links_to`, `pagination`, and related routing hints SHALL define the traversal boundary

#### Scenario: Crawl without strategy

- **WHEN** no matching `site-strategy` exists for the target
- **THEN** the system SHALL refuse to execute crawl
- **AND** it SHALL instruct the caller to run `explore` first to produce or refine a `site-strategy`

### Requirement: Strategy-guided traversal boundary

The crawl capability SHALL be bounded by `site-strategy` rather than open-ended recursive discovery.

#### Scenario: Traversal scope

- **WHEN** a strategy-guided crawl runs
- **THEN** it SHALL only traverse pages reachable through declared strategy structure
- **AND** it SHALL not escalate into unrestricted site-wide recursive crawling

### Requirement: Entry-point based crawl start

The crawl capability SHALL begin from declared strategy entry points.

#### Scenario: Entry point selection

- **WHEN** the matched `site-strategy` defines one or more `entry_points`
- **THEN** the crawl workflow SHALL start from those declared entry points or a caller-selected subset of them
- **AND** it SHALL not invent undeclared starting pages as the default path

### Requirement: Pagination-aware traversal

The crawl capability SHALL honor the strategy-declared pagination model for list pages.

#### Scenario: URL-parameter pagination

- **WHEN** a strategy declares `pagination: { mechanism: "url_parameter", ... }`
- **THEN** the crawl workflow SHALL follow that pagination contract when traversing list pages
- **AND** it SHALL stop according to the implementation's bounded completion rule rather than recurse indefinitely

#### Scenario: Infinite-scroll pagination

- **WHEN** a strategy declares `pagination: { mechanism: "scroll_infinite", ... }`
- **THEN** the crawl workflow SHALL treat that page as a bounded strategy-guided traversal target
- **AND** it SHALL report partial completion if pagination stopping conditions become ambiguous or blocked

### Requirement: Partial failure semantics

The crawl capability SHALL support partial completion when some pages succeed and others fail.

#### Scenario: Mixed page outcomes

- **WHEN** a crawl retrieves some pages successfully but encounters blocked, rate-limited, or failed pages later in the traversal
- **THEN** the command SHALL return `partial_success`
- **AND** it SHALL identify the successful outputs and the pages or stages that failed

### Requirement: Explore-first remediation

The crawl capability SHALL treat missing strategy coverage as an explore workflow gap rather than as a generic runtime failure.

#### Scenario: Explore-first next action

- **WHEN** crawl is refused because no strategy exists
- **THEN** the command result SHALL set `result` to `failure` or `partial_success` according to implementation policy
- **AND** `next_action` SHALL explicitly direct the caller to run `chrome-agent explore` for strategy creation or refinement
