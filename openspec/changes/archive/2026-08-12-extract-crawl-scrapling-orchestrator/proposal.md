# Proposal

## 问题定义

`scripts/chrome-agent-cli.mjs`（4551 行）是 god module。其中 `runCrawlScrapling`（2471–2913，~440 行 async）把五种关注点内联在同一函数：队列初始化、逐页遍历、runDir 扫描聚合、manifest 构建、handoff 生成。它直接调用 `fs.readFileSync/readdirSync/existsSync/unlinkSync` 约 10 处，并 `await findAvailablePort()` 等顶层异步操作。唯一可测 seam 是整个 CLI 的 subprocess——orchestration 逻辑无法独立于 Chrome/spawn 被单元测试，违反 ADR 0013 §4.4「模块内联编排无 seam」反模式。

## 范围边界

**范围内：**
- 提取 `runCrawlScrapling` 到 `scripts/lib/crawl_scrapling.mjs`，签名改为 `runCrawlScrapling(ctx, opts)`（12 个位置参数收编为 `ctx` 对象）
- 随行提取 4 个 scrapling 专属 helper：`runScraplingPreflight` / `runScraplingFetch` / `scraplingSlugFromUrl` / `loadScraplingCache`
- 共享 helper（`selectFetcher` / `pagePatternMatches` / `buildCrawlReport` / `generateHandoff` / `collectLinksFromHtml` / `findAvailablePort` / `runEngineFetch`）**留在 cli.mjs** 并补 `export`，新模块 import 回来
- `runCrawlScrapling` 内的 fs 直接调用改走注入的 `deps.fs`（deps seam）
- cli.mjs 3 处 dispatch 调用点（line 2202/2365/2369）改为对象传参
- 新增 `tests/crawl_scrapling.test.mjs`（node:test，注入假 deps.fs + 打桩 scrapling helper，覆盖 traversal/manifest/handoff）
- C10 同步：归档 commit 内 `cp runtime → 全局` + 刷 installed-hash

**范围外：**
- `runCrawlMediawikiApi` / `runCrawlScraplingDiscovery` / 其它 handler 提取（推迟，待本 change 稳定后按需）
- 共享 helper 自身的提取（它们被全 cli 复用，提取是更大重构）
- crawl 命令任何外部行为变更
- 新能力

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `fetch`: 声明 crawl scrapling 编排器为可独立测试的 seam 模块（`scripts/lib/crawl_scrapling.mjs`），runCrawlScrapling 从 god module 内联编排变为 lib 委托；crawl 外部行为不变

## Capabilities 待确认项

- [x] 能力清单已确认（仅 fetch 一个能力，Modified；纯结构重构无行为变更）

## Impact

- **行为影响**：零。crawl 命令产出 SHALL 字节级不变
- **seam 影响**：runCrawlScrapling 从「仅 subprocess 可测」变为「deps.fs 注入 + helper 打桩可单元测试」
- **代码量**：cli.mjs 减 ~440 行 + 4 helper；新建 crawl_scrapling.mjs；新增测试
- **C10 影响**：cli.mjs 是 tracked trigger，归档 commit 必须重新复制 runtime 全局副本 + 刷新 installed-hash（顺带闭合既有 `8111a3f` 漂移）
- **风险**：12 参数对象化 + 3 调用点改写，签名错配会运行时崩；共享 helper 补 export 后需验证无遗漏

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：global-install playbook Case 6、GOVERNANCE §3、ADR 0013 §4.4
  - 项目页：架构审查报告候选 4、scrapling-extraction-args.mjs 先例、crawl-scrapling-pages-scope.test.mjs
  - 回写目标：全局 runtime 副本 + installed-hash + 04-cli-reference（如有）
