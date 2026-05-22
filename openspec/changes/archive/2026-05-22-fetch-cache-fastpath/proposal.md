# Proposal

## 问题定义

`run_fetch()` 在处理已全量缓存的 manifest 时，存在三条性能缺陷：

1. **无条件 sleep**：`as_completed` 循环内每个 future（含已缓存 skip 的）都执行 `time.sleep(batch_delay_sec)`，5000 页全缓存时累计 sleep 83 分钟
2. **全量提交线程池**：所有页面都提交到 `ThreadPoolExecutor`，即使 100% 已缓存也要调度线程 + 创建 future 对象
3. **缺少快速路径**：没有集合包含判断——当 manifest 所有页面均已缓存时，可以瞬间返回

用户场景：外部仓库对已爬取的 wiki 站点重新执行 pipeline（`--from-manifest`），即使页面全部缓存，fetch 阶段仍需逐页检查 + sleep，整体耗时远超预期。

## 范围边界

**In Scope**：
- `run_fetch()` 快速路径优化（集合包含判断 + 预过滤 + sleep 移位）
- 缓存模块无变更（`list_cached_pages` 已满足需求）
- `02-pipeline-flow.md` 文档更新

**Out of Scope**：
- 缓存有效性验证（不检查缓存内容完整性）
- Convert / Assembly 阶段优化
- 新增 CLI 参数（如 `--skip-fetch-if-cached`）
- `--resume` 状态管理变更

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `fetch-phase-cache-fastpath`: 为 run_fetch 添加全量缓存快速路径、预过滤未缓存页面、将 batch_delay sleep 限制为仅实际网络请求的页面

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

- **性能**：全量缓存场景 fetch 耗时从 O(N) × batch_delay 降至 <1 秒；部分缓存场景仅对缺失页面产生 sleep 开销
- **兼容性**：纯内部优化，无 API / CLI 行为变化，`--re-fetch` 语义不变
- **风险**：低。快速路径基于 `list_cached_pages()` 已有的集合逻辑，无新 I/O 路径

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 项目页：`docs/architecture/02-pipeline-flow.md`（Fetch 阶段描述）
  - 变更主目标：`scripts/pipeline/pipeline/phases/fetch.py`
  - 依赖模块：`scripts/pipeline/pipeline/cache.py`
