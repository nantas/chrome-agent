# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-registry`
- 来源: `add-obscura-engine` proposal
- 变更类型: modified
- 用户确认摘要: 新增 `obscura-fetch` 引擎条目及其对应的 `cdp_lightweight` 引擎类型

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: 注册索引位置与格式

The system SHALL maintain a machine-readable engine registry at `configs/engine-registry.json`.

The registry file SHALL be a JSON object with a single key `engines` containing an array of engine entry objects. Each entry SHALL contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Canonical engine identifier (kebab-case, must match contract spec directory name stem, e.g., `scrapling-get`) |
| `type` | string | yes | Engine type: `http`, `playwright`, `playwright_stealth`, `cdp_managed`, `cdp_live`, `cdp_lightweight`, `playwright_bulk` |
| `characteristics` | object | yes | Three scoring dimensions: efficiency, stability, adaptability (see Characteristics requirement) |
| `composite_score` | number | yes | Weighted aggregate score (0-100), derived from characteristics |
| `default_rank` | integer | yes | Default execution priority order (1 = first to try, higher = later) |
| `best_for` | string[] | yes | Page types or scenarios where this engine excels |
| `contract_spec` | string | yes | Capability ID of the engine's contract spec (e.g., `scrapling-get-contract`) |
| `status` | enum | yes | Lifecycle state: `draft`, `frozen`, `superseded` |

#### Scenario: 注册索引可查询

- **WHEN** an agent encounters a URL with known page type and protection level
- **THEN** it SHALL be able to scan `configs/engine-registry.json` to determine available engines, their characteristics, and default ranking
- **AND** this SHALL inform the agent's engine selection decision

#### Scenario: 注册索引一致性

- **WHEN** an engine's contract spec is created, modified, or superseded
- **THEN** the corresponding entry in `configs/engine-registry.json` SHALL be updated
- **AND** if inconsistency is detected between registry entry and contract spec, the contract spec SHALL be considered authoritative

### Requirement: 引擎特性评分维度

The system SHALL define three scoring dimensions for each engine in the registry, each scored 0.00-1.00.

1. **efficiency** (`characteristics.efficiency.score`): Speed and resource cost of the engine. Higher = lighter/faster.
   - HTTP-based engines (no browser): typically 0.80-0.95
   - CDP-lightweight engines (Rust/V8, no full browser): typically 0.70-0.90
   - Playwright-based engines (browser launch): typically 0.30-0.60
   - CDP-based engines (real Chrome): typically 0.20-0.40
2. **stability** (`characteristics.stability.score`): Reliability and consistency of the engine for its target scenarios.
   - Well-tested engines with known targets: 0.75-0.90
   - New or limited-evidence engines: 0.50-0.70
3. **adaptability** (`characteristics.adaptability.score`): Range of scenarios the engine can handle successfully.
   - General-purpose engines covering many page types: 0.80-0.95
   - Narrow-purpose engines (single page type): 0.20-0.50

Each dimension SHALL include a `note` field (string) providing the rationale for the score.

#### Scenario: 评分维度完整性

- **WHEN** an engine entry is added to the registry
- **THEN** all three characteristic dimensions (efficiency, stability, adaptability) SHALL be present with non-null score and note
- **AND** scores SHALL be between 0.00 and 1.00 inclusive

#### Scenario: 评分维度可比较

- **WHEN** two engines are compared for a given scenario
- **THEN** the agent SHALL consult the three-dimensional scores to understand tradeoffs
- **AND** the `composite_score` SHALL provide a single aggregate metric for ranking

### Requirement: Default Rank 推导规则

The system SHALL derive `default_rank` from engine family ordering while respecting the Scrapling-first principle.

The `default_rank` SHALL reflect the default execution order:
- Rank 1: first engine to try for unknown or unmatched URLs
- Higher ranks: progressively later escalation fallbacks

The Scrapling-first principle SHALL be enforced by overriding raw score ordering within engine families:
- All Scrapling engines (`http`, `playwright`, `playwright_stealth`, `playwright_bulk`) SHALL rank before CDP engines (`cdp_managed`, `cdp_live`)
- CDP-lightweight engines (`cdp_lightweight`) SHALL rank between Scrapling `http` and Scrapling `playwright` engines, reflecting their position as a lighter alternative to full browser automation
- Within Scrapling: lighter engines rank before heavier ones (`scrapling-get` → `scrapling-fetch` → `scrapling-stealthy-fetch`), with bulk siblings placed adjacent to their non-bulk counterparts when the scenario is batch-oriented
- Within CDP: `chrome-devtools-mcp` SHALL rank before `chrome-cdp`

`default_rank` is the baseline priority. Site strategy `engine_preference` and anti-crawl `engine_priority` SHALL override it in context.

#### Scenario: Default engine for unprotected static pages

- **WHEN** an agent encounters an unknown URL with no matching strategy and no protection signals
- **THEN** the engine with `default_rank: 1` (`scrapling-get`) SHALL be the first choice
- **AND** escalation SHALL follow ascending `default_rank` order

#### Scenario: CDP-lightweight engine position in escalation chain

- **WHEN** `scrapling-get` fails due to requiring JS rendering
- **THEN** the next engine in the escalation chain SHALL be the `cdp_lightweight` engine (`obscura-fetch`) before escalating to full `playwright` engines
- **AND** this reflects the efficiency advantage of `cdp_lightweight` over `playwright` for moderate JS rendering needs

#### Scenario: Default rank overridden by strategy

- **WHEN** a site strategy has `engine_preference.preferred: scrapling-fetch`
- **THEN** the `default_rank` of `scrapling-get` SHALL be ignored for that site
- **AND** `scrapling-fetch` SHALL be tried first regardless of its `default_rank`

### Requirement: 引擎生命周期状态

The system SHALL define three lifecycle states for engines in the registry.

| State | Meaning |
|-------|---------|
| `draft` | Engine contract spec exists but has not been fully validated via smoke-check or strategy integration |
| `frozen` | Engine contract has been validated and is stable; referenced by strategies |
| `superseded` | Engine has been replaced by a newer engine or capability; retained for historical reference |

#### Scenario: 新引擎初始状态

- **WHEN** a new engine is added via the extension-api process
- **THEN** its initial status SHALL be `draft`
- **AND** it SHALL transition to `frozen` only after completing smoke-check validation and strategy integration verification

#### Scenario: 冻结引擎不可随意修改

- **WHEN** an engine is in `frozen` status
- **THEN** modifications to its contract spec SHALL go through an openspec change
- **AND** the change SHALL update the registry entry accordingly

## ADDED Requirements

### Requirement: obscura-fetch engine entry

The system SHALL register the obscura-fetch engine in `configs/engine-registry.json` with the following characteristics:

```json
{
  "id": "obscura-fetch",
  "type": "cdp_lightweight",
  "characteristics": {
    "efficiency": {
      "score": 0.85,
      "note": "Rust+V8 headless browser. ~8MB RSS idle, ~50MB peak, 85ms page load. 2-3.5x faster than playwright for JS-rendered pages."
    },
    "stability": {
      "score": 0.55,
      "note": "v0.1.0 with limited release history. CDP implementation is a subset. Needs more site coverage validation."
    },
    "adaptability": {
      "score": 0.65,
      "note": "Handles static HTML, JS-rendered SPA, dynamic lists, basic stealth. Not suitable for high-protection pages or complex browser APIs (WebSocket, Web Worker)."
    }
  },
  "composite_score": 62,
  "default_rank": 2,
  "best_for": ["dynamic_content", "dynamic_list", "dynamic_grid", "static_article"],
  "contract_spec": "obscura-fetch-contract",
  "status": "draft"
}
```

The `composite_score` SHALL be derived using the formula: `round((adaptability × 0.50 + stability × 0.30 + efficiency × 0.20) × 100)`.

#### Scenario: obscura-fetch registry entry validation

- **WHEN** the `obscura-fetch` registry entry is validated
- **THEN** all three characteristic dimensions SHALL have non-null scores and notes
- **AND** `id` SHALL match the contract spec directory stem `obscura-fetch-contract`
- **AND** `type` SHALL be `cdp_lightweight`
- **AND** `status` SHALL be `draft`
- **AND** `composite_score` SHALL equal `round((0.65 × 0.50 + 0.55 × 0.30 + 0.85 × 0.20) × 100)` = `62`

#### Scenario: Existing engine rank adjustment

- **WHEN** obscura-fetch is added with `default_rank: 2`
- **THEN** existing engines with `default_rank ≥ 2` SHALL have their ranks incremented by 1:
  - `scrapling-fetch`: 2 → 3
  - `scrapling-bulk-fetch`: 3 → 4
  - `scrapling-stealthy-fetch`: 3 → 4
  - `chrome-devtools-mcp`: 4 → 5
  - `chrome-cdp`: 5 → 6
