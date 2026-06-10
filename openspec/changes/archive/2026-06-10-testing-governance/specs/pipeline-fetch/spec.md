# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-fetch`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——样本页面纳入 .cache 体系，无特殊 fetch 逻辑

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Sample pages stored in standard cache
Sample pages fetched during explore SHALL be stored in the standard `.cache/<platform>/<domain>/` directory using the same `save_page_cache()` interface as regular pipeline pages.

- No special cache path or prefix for sample pages.
- The test runner SHALL locate sample data by reading the strategy's `samples` field and resolving each page to its cache entry using the standard `load_page_cache()` or direct file read.

#### Scenario: Sample page reuses cache
- **WHEN** explore fetches 3 sample pages for a domain
- **THEN** those pages SHALL be available at `.cache/chrome-cdp/<domain>/<safe_path>.json`
- **THEN** subsequent full pipeline fetch SHALL skip those pages (cache hit)

#### Scenario: Test runner reads sample from cache
- **WHEN** the test runner processes a strategy with 3 samples
- **THEN** it SHALL load each sample's HTML from `.cache/` using the standard cache path convention
