# Writeback

## Change: fetch-cache-fastpath

## Target: `docs/architecture/02-pipeline-flow.md`

### 目标章节
Fetch 阶段描述

### 回写内容

在 Fetch 阶节描述中补充以下行为说明：

1. **全量缓存快速路径**：当 manifest 所有页面均已在缓存中且未启用 `--re-fetch` 时，`run_fetch()` 跳过线程池调度，直接返回 `skipped = total` 的统计结果，总耗时 < 1 秒。

2. **预过滤未缓存页面**：`run_fetch()` 在提交线程池之前将 manifest 页面分为已缓存和未缓存两组。仅未缓存页面提交到线程池，已缓存页面直接计入 skipped 统计。

3. **速率限制 sleep 精确化**：`time.sleep(batch_delay_sec)` 仅在实际产生网络请求（`status == "ok"`）时执行，跳过和失败的页面不触发 sleep。

### 前置条件
- verification.md 已通过（所有 spec requirements 验证通过）

### 字段映射

| 规范 Requirement | 文档描述 |
|-------------------|----------|
| `full-cache-fastpath` | 全量缓存快速路径行为 |
| `partial-cache-prefilter` | 预过滤逻辑说明 |
| `batch-delay-only-on-network-requests` | sleep 精确化说明 |

### 不变项
- 函数签名、返回值结构、CLI 行为均无变化
- `--re-fetch` 语义不变
- `cache.py` 模块无变更
