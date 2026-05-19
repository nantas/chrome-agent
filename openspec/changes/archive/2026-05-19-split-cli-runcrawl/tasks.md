# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/global-capability-cli/spec.md` 的行为要求：三路独立函数 + `runCrawl()` ≤ 80 行路由
- [x] 1.2 确认依赖条件：`scripts/pipeline/` 包名已更新（Change 3 完成）、spawn 路径无需变更

## 2. 核心实现任务

- [x] 2.1 提取 `runCrawlMediawikiApi()` — 从 `runCrawl()` 中剪切 MediaWiki API 路径代码块（行 ~2070-2198，~128 行）到新函数，在 `runCrawl()` 中替换为路由调用
  - 完成标准：`runCrawl()` 中不再包含 `spawnSync("python3", ...)` 调用；MediaWiki API crawl 行为不变

- [x] 2.2 提取 `runCrawlScraplingDiscovery()` — 从 `runCrawl()` 中剪切 Scrapling discovery-only 路径代码块（行 ~2215-2301，~86 行）到新函数，在 `runCrawl()` 中替换为路由调用
  - 完成标准：`runCrawl()` 中不再包含 `collectLinksFromHtml()` 调用；discovery-only 行为不变

- [x] 2.3 提取 `runCrawlScrapling()` — 从 `runCrawl()` 中剪切 Scrapling 标准遍历路径代码块（行 ~2303-2664，~360 行）到新函数，在 `runCrawl()` 中替换为路由调用
  - 完成标准：`runCrawl()` 中不再包含 queue 遍历循环或 Phase 2 转换逻辑；Scrapling crawl 行为不变

- [x] 2.4 精简 `runCrawl()` — 移除已提取的三路代码，保留参数解析、策略匹配、入口点验证和错误处理，最终 ≤ 80 行
  - 完成标准：`wc -l` 确认 `runCrawl()` 函数体 ≤ 80 行

## 3. 收敛与验证准备

- [x] 3.1 运行 `node --test tests/chrome-agent-runtime.test.mjs` 确认所有测试通过
- [x] 3.2 对 `bindingofisaacrebirth.wiki.gg` 站点执行 `chrome-agent crawl` 并对比重构前后的产出 diff
- [x] 3.3 对 `slaythespire.wiki.gg` 站点执行 `chrome-agent crawl --discovery-only` 验证 discovery-only 路径不变

## 4. 验证与回写收敛

- [x] 4.1 基于实现结果生成 `verification.md`（spec 覆盖、测试证据、产出 diff 对比）
- [x] 4.2 基于 `verification.md` 生成 `writeback.md`
- [x] 4.3 回写 `docs/plans/2026-05-19-structure-refactor-and-docs.md`：更新 Phase 3 完成状态
