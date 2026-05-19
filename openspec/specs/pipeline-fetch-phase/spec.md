# pipeline-fetch-phase Specification

## Purpose
独立的 fetch phase，负责从数据源获取原始内容并写入持久化缓存。支持 manifest 驱动的批量获取、缓存跳过（已有缓存不重复请求）、rate limit 控制和 resume。MediaWiki API 路径和 Scrapling 路径均实现此 phase。

## Requirements

### Requirement: fetch-phase-cli-entry
The system SHALL 支持 `--phase fetch` CLI 参数。

`--phase fetch` 的行为 SHALL 为：
1. 若提供 `--from-manifest`，使用指定 manifest；否则执行 discovery phase 生成 manifest
2. 遍历 manifest 中所有页面
3. 对每个页面，若缓存中已存在对应文件，SHALL 跳过（不重复请求）
4. 若缓存不存在，SHALL 通过 API 或 Scrapling 获取原始内容并写入缓存
5. fetch 完成后 SHALL NOT 执行转换或 assembly

新增 `--re-fetch` flag：当指定时，SHALL 忽略已有缓存，强制重新获取所有页面并覆盖缓存文件。

#### Scenario: fetch-with-cache-skip
- **WHEN** 执行 `--phase fetch --from-manifest <path>`
- **AND** `.cache/mediawiki/<domain>/The_Lamb.json` 已存在
- **THEN** SHALL 跳过 `The Lamb` 页面的 API 请求
- **AND** 日志 SHALL 记录 `"Skipping 'The Lamb' (already cached)"`

#### Scenario: fetch-with-re-fetch
- **WHEN** 执行 `--phase fetch --re-fetch --from-manifest <path>`
- **AND** 某些页面已有缓存
- **THEN** SHALL 忽略已有缓存，重新获取所有页面
- **AND** SHALL 覆盖已有缓存文件

#### Scenario: fetch-without-manifest
- **WHEN** 执行 `--phase fetch` 但未提供 `--from-manifest`
- **THEN** SHALL 先执行 discovery phase 生成 manifest
- **AND** 然后执行 fetch

### Requirement: fetch-phase-incremental
`--phase fetch` 支持增量获取：已有缓存的页面默认跳过，仅获取新增或缺失的页面。

#### Scenario: incremental-fetch
- **WHEN** manifest 包含 1769 个页面
- **AND** 其中 1757 个页面已有缓存（如前次 fetch 成功写入）
- **AND** 12 个页面缓存缺失（如前次 fetch 失败）
- **THEN** SHALL 仅对这 12 个缺失页面发起 API 请求
- **AND** 日志 SHALL 报告 `"Fetching 12 new/uncached pages, skipping 1757 cached"`

### Requirement: fetch-phase-error-handling
单个页面 fetch 失败时 SHALL NOT 阻断其余页面的 fetch 流程。

失败信息 SHALL 记录到日志（warning 级别），包含页面标题和错误原因。

#### Scenario: single-page-fetch-failure
- **WHEN** 页面 `Blessed Penny` fetch 失败（HTTP 429）
- **THEN** 后续页面 SHALL 继续 fetch
- **AND** 日志 SHALL 记录 `"Fetch failed for 'Blessed Penny': HTTP 429"`
- **AND** 该页面的缓存文件 SHALL NOT 被创建

### Requirement: fetch-phase-rate-limiting
fetch phase SHALL 使用与当前 Phase B `run_phase_b()` 相同的 `RateLimitConfig` 和 `ThreadPoolExecutor` 并发控制。

#### Scenario: rate-limit-config
- **WHEN** strategy 的 `rate_limit.tier` 为 `"strict"` 且 `batch_delay_ms` 为 1200
- **THEN** fetch phase SHALL 以 `concurrency=1`、`batch_delay_ms=1200` 执行

### Requirement: fetch-phase-resume
fetch phase SHALL 支持 resume：通过缓存文件存在性判断页面是否已完成 fetch（无需额外的 pipeline_state 追踪）。

缓存文件存在 = 该页已 fetch 完成，可跳过。

#### Scenario: resume-after-interruption
- **WHEN** 前次 `--phase fetch` 在中途被中断
- **AND** 106 个页面的缓存文件已成功写入
- **THEN** 重新执行 `--phase fetch --from-manifest <same_manifest>` 时
- **AND** SHALL 跳过这 106 个已有缓存的页面
- **AND** SHALL 仅 fetch 剩余页面

### Requirement: fetch-phase-summary
fetch 完成后 SHALL 输出摘要日志：总页面数、成功 fetch 数、跳过数（缓存命中）、失败数。

#### Scenario: fetch-summary
- **WHEN** fetch phase 完成
- **THEN** 日志 SHALL 输出 `"Fetch phase complete: 1769 total, 1757 fetched, 0 skipped (cached), 12 failed"`
