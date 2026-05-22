# Design

## Context

`run_fetch()`（`scripts/pipeline/pipeline/phases/fetch.py`）当前对每个 manifest 页面无条件提交到 `ThreadPoolExecutor`，并在 `as_completed` 循环中逐 future 执行 `time.sleep(batch_delay_sec)`。即使页面已在 `.cache/` 中命中，仍会经历线程调度 + sleep，导致全量缓存场景的无效耗时。

缓存检查本身已高效（`list_cached_pages()` 返回 `set[str]`），瓶颈完全在 fetch 调度层的架构选择。

## Goals / Non-Goals

**Goals:**
- 全量缓存 manifest 瞬间返回（< 1 秒）
- 部分缓存 manifest 仅对缺失页面产生线程调度和 sleep 开销
- 保持 `--re-fetch`、`--resume`、concurrency 等现有行为不变
- Python 3.9+ 兼容

**Non-Goals:**
- 缓存内容完整性校验（如检查 JSON 是否可解析）
- 新增 CLI 参数
- Convert / Assembly 阶段优化
- 修改 `cache.py` 模块

## Decisions

### D1: 快速路径 — 集合子集判断

在 `run_fetch()` 中，`cached_pages` set 已存在（`list_cached_pages()` 返回值）。直接比较 `manifest_titles <= cached_pages`：

```python
manifest_titles = {p["title"] for p in pages}
if not re_fetch and manifest_titles and manifest_titles <= cached_pages:
    log.info("Cache: all %d manifest pages already cached — skipping fetch", len(manifest_titles))
    return {"total": len(pages), "fetched": 0, "skipped": len(pages), "failed": 0}
```

**选择理由**：零新依赖，O(N) set 构建 + O(N) 子集判断，对 5 万页以内的 manifest 可忽略不计。

### D2: 预过滤 — 分离 cached / to_fetch

快速路径之后，将页面分为两组：

```python
to_fetch = []
skipped_count = 0
for p in pages:
    if not re_fetch and p["title"] in cached_pages:
        skipped_count += 1
    else:
        to_fetch.append(p)
```

仅 `to_fetch` 提交到线程池。**选择理由**：减少线程调度和 future 对象创建开销，逻辑清晰。

### D3: sleep 移位 — 仅限 status == "ok"

将 `time.sleep(batch_delay_sec)` 从无条件执行移至 `result["status"] == "ok"` 分支内：

```python
if result["status"] == "ok":
    fetched_count += 1
    time.sleep(batch_delay_sec)
```

**选择理由**：速率限制的语义是控制 API 请求频率，skip / fail 不消耗 API 配额，无需 throttle。

### D4: 日志保留

快速路径和预过滤路径均保留 `log.info` 输出，确保用户在日志中能看到跳过原因。

## Risks / Migration

- **风险极低**：变更仅影响 `run_fetch()` 内部调度逻辑，不改变函数签名、返回值结构或 CLI 行为
- **回归点**：`--re-fetch` 模式下快速路径和预过滤均被 `re_fetch` flag 短路，行为不变
- **测试**：现有 `--re-fetch` 路径不受影响；需验证全缓存 / 部分缓存 / 零缓存三条路径
