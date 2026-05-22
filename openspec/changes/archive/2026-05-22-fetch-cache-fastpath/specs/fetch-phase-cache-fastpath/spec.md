# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-phase-cache-fastpath`
- 来源: `proposal.md` / Modified Capabilities
- 变更类型: modified
- 用户确认摘要: 用户确认三条优化方案（全量缓存快速路径 + sleep 限制 + 预过滤），无新增 CLI 参数

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: full-cache-fastpath
`run_fetch()` SHALL 在进入 ThreadPoolExecutor 之前，检查 manifest 所有页面标题是否为 `list_cached_pages()` 返回集合的子集。若 `manifest_titles ⊆ cached_pages` 且 `re_fetch == False`，SHALL 跳过整个线程池调度，直接返回 `skipped = total` 的 stats dict。

#### Scenario: all-pages-cached
- **WHEN** manifest 包含 N 个页面，`list_cached_pages()` 返回的集合包含所有 N 个标题，且 `re_fetch == False`
- **THEN** `run_fetch()` SHALL NOT 创建任何线程或发起任何 API 请求，直接返回 `{"total": N, "fetched": 0, "skipped": N, "failed": 0}`，总耗时 < 1 秒

#### Scenario: all-pages-cached-with-re-fetch
- **WHEN** `re_fetch == True`
- **THEN** 快速路径 SHALL NOT 触发，行为与当前一致（全量重新获取）

### Requirement: partial-cache-prefilter
`run_fetch()` SHALL 在提交 ThreadPoolExecutor 之前，将 manifest 页面分为两组：已缓存（skip）和未缓存（fetch）。只有未缓存页面 SHALL 提交到线程池。已缓存页面 SHALL 直接计入 `skipped_count`，不创建 future 对象。

#### Scenario: partial-cache
- **WHEN** manifest 包含 5000 页面，其中 4900 已缓存，100 未缓存
- **THEN** 仅 100 个 future 提交到线程池；`skipped_count` 初始化为 4900；线程池 max_workers 仅调度 100 个任务

#### Scenario: no-cache
- **WHEN** manifest 包含 N 页面，`list_cached_pages()` 返回空集
- **THEN** 所有 N 页面提交到线程池，行为与当前一致

### Requirement: batch-delay-only-on-network-requests
`run_fetch()` SHALL 仅在 `as_completed` 循环中实际产生了网络请求（`status == "ok"`）时执行 `time.sleep(batch_delay_sec)`。跳过（cached / not_found）和失败的页面 SHALL NOT 触发 sleep。

#### Scenario: skip-does-not-sleep
- **WHEN** 一个 cached 页面在预过滤阶段被排除（不进入 `_fetch_one` 和 `as_completed` 循环）
- **THEN** 该页面 SHALL NOT 触发 `time.sleep(batch_delay_sec)`（因其在线程池外直接计入 skipped_count）

#### Scenario: fetch-does-sleep
- **WHEN** 一个页面实际执行了 API 请求并返回 `{"status": "ok"}`
- **THEN** 主循环 SHALL 执行 `time.sleep(batch_delay_sec)` 以遵守速率限制

## REMOVED Requirements

（无）

## RENAMED Requirements

（无）
