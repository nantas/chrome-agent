# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖：`full-cache-fastpath`、`partial-cache-prefilter`、`batch-delay-only-on-network-requests` 三条 requirement 均有对应实现路径
- [x] 1.2 确认依赖：`cache.py` 的 `list_cached_pages()` 无需变更；`fetch.py` 的 `run_fetch()` 是唯一修改文件

## 2. 核心实现任务

- [x] 2.1 **全量缓存快速路径**（spec: `full-cache-fastpath`）
  - 实现路径：`fetch.py:run_fetch()` 在 `cached_pages` 计算后、ThreadPoolExecutor 之前，插入 `manifest_titles <= cached_pages` 判断
  - 完成标准：全缓存 manifest 调用 `run_fetch()` 返回 `skipped=total`，不创建线程池

- [x] 2.2 **预过滤未缓存页面**（spec: `partial-cache-prefilter`）
  - 实现路径：快速路径之后，遍历 `pages` 分离 `cached` / `to_fetch`，仅 `to_fetch` 提交线程池
  - 完成标准：部分缓存场景线程池 future 数量 = 未缓存页面数；`skipped_count` 初始化为已缓存数

- [x] 2.3 **sleep 移位至网络请求**（spec: `batch-delay-only-on-network-requests`）
  - 实现路径：将 `time.sleep(batch_delay_sec)` 从循环末尾移至 `result["status"] == "ok"` 分支内
  - 完成标准：skip/fail/not_found 的 future 不触发 sleep

- [x] 2.4 **更新 `_fetch_one` 语义**
  - 实现路径：`_fetch_one` 不再需要 cached skip 逻辑（已由预过滤处理），移除 `_fetch_one` 中的 `title in cached_pages` 检查
  - 完成标准：`_fetch_one` 仅负责 fetch + cache write

## 3. 收敛与验证准备

- [x] 3.1 验证全缓存路径：构造 100% cached manifest，确认 < 1 秒返回，日志输出 "skipping fetch"
- [x] 3.2 验证部分缓存路径：构造 50% cached manifest，确认仅未缓存页面产生 API 请求和 sleep
- [x] 3.3 验证零缓存路径：空 cache 目录，确认行为与优化前一致
- [x] 3.4 验证 `--re-fetch` 路径：`re_fetch=True` 时快速路径和预过滤均不生效
- [x] 3.5 Python 3.9 兼容性：无 `X | Y` 类型语法

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback：更新 `docs/architecture/02-pipeline-flow.md` Fetch 阶段描述，补充快速路径行为说明
