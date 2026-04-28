# Specification Delta

## Capability 对齐（已确认）

- Capability: `anti-crawl-schema`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: explore mode 中确认——`engine_sequence` 废弃，替换为 `engine_priority`，`purpose` 字段（primary/fallback/diagnostic）替换为 `rank`（integer），`engine` 和 `config` 字段保留

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## RENAMED Requirements

- FROM: `### Requirement: Engine Sequence 引擎序列`
- TO: `### Requirement: Engine Priority 引擎优先级`

## REMOVED Requirements

### Requirement: Engine Sequence 引擎序列（旧字段定义）

**Reason**: `engine_sequence` 被 `engine_priority` 替代。旧的 `purpose` 字段（枚举：primary/fallback/diagnostic）无法表达多维优先级排序。新的 `rank` 字段（integer，1-based）提供精确的执行顺序控制，配合 `configs/engine-registry.json` 中的引擎特性评分实现更精细的引擎选择。

**Migration**: 所有 anti-crawl 策略文件的 YAML frontmatter 中：
- 字段名从 `engine_sequence` 改为 `engine_priority`
- 每个 entry 的 `purpose` 字段删除，替换为 `rank`（1 = 首先尝试，2 = 第二尝试，以此类推）
- `engine` 和 `config` 字段保持不变
- 迁移后 SHALL 更新 `sites/anti-crawl/registry.json` 中的相关条目

## MODIFIED Requirements

### Requirement: Engine Priority 引擎优先级

The system SHALL define the `engine_priority` field as an ordered list of engines to try for this protection, with optional per-engine configuration and rank.

Each entry in `engine_priority` SHALL contain:
- `engine`: engine identifier from `configs/engine-registry.json` (e.g., `scrapling-stealthy-fetch`)
- `rank` (required): integer starting from 1, indicating execution priority order. 1 = first engine to try, 2 = second, etc. Ranks SHALL be contiguous (no gaps) and start at 1.
- `config` (optional): engine-specific configuration override (e.g., `solve_cloudflare: true`, `network_idle: true`, `timeout: 60000`)

The `rank` field replaces the deprecated `purpose` field (which used enum values: `primary`, `fallback`, `diagnostic`).

#### Scenario: 引擎优先级排序表达

- **WHEN** a Cloudflare Turnstile protection is detected and the anti-crawl strategy specifies:
  ```yaml
  engine_priority:
    - engine: scrapling-stealthy-fetch
      rank: 1
      config: { solve_cloudflare: true }
    - engine: chrome-devtools-mcp
      rank: 2
  ```
- **THEN** `scrapling-stealthy-fetch` SHALL be tried first (rank: 1)
- **AND** `chrome-devtools-mcp` SHALL be tried second (rank: 2) if the first engine fails

#### Scenario: 引擎优先级必须尊重 canonical chain

- **WHEN** an `engine_priority` is defined
- **THEN** the engines SHALL appear in the same order as the canonical escalation chain: `scrapling-get` → `scrapling-fetch` → `scrapling-stealthy-fetch` → `chrome-devtools-mcp` → `chrome-cdp`
- **AND** entries MAY be skipped (e.g., start at `scrapling-stealthy-fetch` for Cloudflare) but SHALL NOT be reordered
- **AND** `rank` values SHALL increase monotonically in canonical chain order

#### Scenario: 连续 rank 值

- **WHEN** an `engine_priority` has three entries
- **THEN** their `rank` values SHALL be 1, 2, 3 (contiguous, no gaps)
- **AND** rank values with gaps (e.g., 1, 3, 4) SHALL be treated as a schema violation

#### Scenario: 最少一个引擎

- **WHEN** an `engine_priority` is specified
- **THEN** it SHALL contain at least one entry
- **AND** an empty `engine_priority` SHALL be treated as a schema violation

#### Scenario: 引擎标识符必须存在于注册表

- **WHEN** `engine_priority` references an engine identifier
- **THEN** that identifier SHALL exist in `configs/engine-registry.json`
- **AND** a reference to a non-existent engine SHALL be treated as a validation error

### Requirement: YAML frontmatter 必填字段

The system SHALL define a mandatory YAML frontmatter schema for all anti-crawl strategy files.

Each anti-crawl file SHALL include the following fields in its YAML frontmatter:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (kebab-case), must match filename without `.md` |
| `protection_type` | enum | yes | From the controlled vocabulary |
| `sites` | string[] | yes | Domains where this protection has been observed; empty array for `default` |
| `detection` | object | yes | Detection signals that identify this protection |
| `engine_priority` | array | yes | Ordered list of engines to try, each with `rank`, `engine`, and optional `config` |
| `success_signals` | object | yes | Conditions indicating the protection was bypassed |
| `failure_signals` | object | yes | Conditions indicating the bypass attempt failed |

#### Scenario: 必填字段完整性

- **WHEN** an anti-crawl strategy file is created or updated
- **THEN** it SHALL contain all required frontmatter fields
- **AND** `id` SHALL match the filename stem (e.g., `cloudflare-turnstile.md` → `id: cloudflare-turnstile`)
- **AND** `engine_priority` SHALL replace the deprecated `engine_sequence` field; `engine_sequence` SHALL NOT be used in new or updated strategy files

### Requirement: Default 默认策略

The system SHALL define a `default.md` anti-crawl strategy that serves as the fallback when no known protection signals are detected and no site strategy matches.

`default.md` SHALL:
- Have `id: default` and `protection_type: none`
- Have `sites: []` (not bound to any specific domain)
- Encode the Scrapling-first escalation chain using `engine_priority`:
  ```yaml
  engine_priority:
    - engine: scrapling-get
      rank: 1
    - engine: scrapling-fetch
      rank: 2
    - engine: scrapling-stealthy-fetch
      rank: 3
    - engine: chrome-devtools-mcp
      rank: 4
  ```
- Serve as the behavior for simple, unprotected pages with no known site strategy

#### Scenario: 无匹配策略

- **WHEN** an agent encounters a URL with no matching site strategy and no detection signals match any anti-crawl strategy
- **THEN** the agent SHALL use the `default` strategy
- **AND** the default strategy SHALL try engines in rank order (1 → 2 → 3 → 4)

## MODIFIED Requirements (minor — field name update in existing text)

### Requirement: Protection Type 受控词汇表

The system SHALL define a controlled vocabulary for `protection_type`.

(Field list unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full vocabulary.)

### Requirement: Detection 检测信号

The system SHALL define the `detection` object to describe signals that identify this protection mechanism.

(Structure unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)

### Requirement: Success/Failure Signals

The system SHALL define success and failure signal schemas for anti-crawl strategies.

(Structure unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)

### Requirement: Markdown body 推荐章节

The system SHALL recommend Markdown body sections for anti-crawl strategy files.

(Structure unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)

### Requirement: Registry.json 索引格式

The system SHALL maintain a `sites/anti-crawl/registry.json` index. The `primary_engine` field in registry entries SHALL reference the engine with `rank: 1` from `engine_priority`.

(Other fields unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)

### Requirement: 新增策略的治理约束

The system SHALL enforce governance constraints for strategy creation through AGENTS.md.

(Rules unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)

### Requirement: 目录存放结构

The system SHALL organize anti-crawl strategy files as flat files in `sites/anti-crawl/`.

(Rules unchanged — see `openspec/specs/anti-crawl-schema/spec.md` for full definition.)
