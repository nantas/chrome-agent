# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-registry`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: engine-registry-new-entry

The engine registry SHALL contain a new entry for the `obscura-serve-pool` engine.

#### Scenario: engine-registry-entry-schema
- **WHEN** the engine registry is inspected
- **THEN** it SHALL contain the following entry:
  - `id`: `obscura-serve-pool`
  - `type`: `cdp_lightweight_pool`
  - `efficiency.score`: 0.85 (Rust+V8 worker pool, near-linear scaling to ~15 workers)
  - `stability.score`: 0.65 (v0.1.2, tested with 20 concurrent workers, zero failures)
  - `adaptability.score`: 0.60 (dynamic content and SPA, not for high-protection pages)
  - `composite_score`: 68
  - `default_rank`: 3 (between obscura-fetch rank 2 and scrapling-fetch rank 4)
  - `best_for`: `["bulk_dynamic", "bulk_list", "batch_fetch", "page_batch"]`
  - `contract_spec`: `obscura-serve-pool-contract`
  - `status`: `draft`

## MODIFIED Requirements

### Requirement: engine-registry-obscura-fetch-stability-update

The existing `obscura-fetch` engine entry SHALL update its stability note to reflect v0.1.2 rather than v0.1.0.

#### Scenario: obscura-fetch-stability-note
- **WHEN** the `obscura-fetch` entry is read
- **THEN** its `stability.note` SHALL reference v0.1.2 instead of v0.1.0 (scope: note text update only, no score change)
