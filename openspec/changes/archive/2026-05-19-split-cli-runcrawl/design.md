# Design

## Context

`runCrawl()` 是 `chrome-agent-cli.mjs` 中最大的单体函数（~764 行），混合了三种互不重叠的 crawl 调度路径。该函数在 `main()` 中被调用，是 `crawl` 命令的唯一执行入口。

前序 Change 1-4 已完成 Python 层的重构，`chrome-agent-cli.mjs` 的 spawn 路径已更新为 `scripts.pipeline`。本次 Change 5 是 Phase 3 的唯一变更，也是整个结构优化重构规划的最后一环。

## Goals / Non-Goals

**Goals:**

- 将 `runCrawl()` 从 ~764 行降至 ≤ 80 行，仅做路由
- 三路调度分别提取为独立函数，每个 ≤ 400 行
- 外部行为（参数面、输出格式、退出码、makeResult 结构）完全不变
- 保持代码风格一致性：函数声明风格（`function` 非箭头函数）、ESM import、JSON-first

**Non-Goals:**

- 不改变 Node.js ↔ Python spawn 参数（已在 Change 3 完成）
- 不提取 `runFetch()`、`runScrape()` 等已有独立函数
- 不创建新文件（所有提取函数保留在 `chrome-agent-cli.mjs` 内）
- 不改变 `runCrawl()` 的错误处理逻辑或 handoff 生成逻辑
- 不改变变量命名约定

## Decisions

### 决策 1: 提取为新独立函数，不导出

三个新函数（`runCrawlMediawikiApi`、`runCrawlScraplingDiscovery`、`runCrawlScrapling`）均为文件内部函数，使用 `function` 声明，不 `export`。

**理由**: 它们是 `runCrawl()` 的实现细节，外部调用方（`main()` 中的 dispatch）只通过 `runCrawl()` 入口访问。不导出避免增加不必要的 API 面。

### 决策 2: 函数签名传递具体参数而非 `opts`

每个提取函数的签名接收已解构的参数，而非原始 `opts` 对象。

**签名定义**:

```javascript
// Route 1: MediaWiki API pipeline
function runCrawlMediawikiApi(repoRoot, runDir, targetUrl, strategy, startPage, opts) → result
// opts = { maxPages, concurrency, discoveryOnly, phase, reFetch, fromManifest, excludeCategory, yesFlag, keepHtml, markdown, merge, parallel, workers, emitReport, reportPath }

// Route 2: Scrapling discovery-only
function runCrawlScraplingDiscovery(repoRoot, runDir, targetUrl, strategy, startPage, opts) → result
// opts = { yesFlag, emitReport, reportPath }

// Route 3: Standard Scrapling crawl
function runCrawlScrapling(repoRoot, runDir, targetUrl, strategy, startPage, matchingPage, entryPoints, opts) → result
// opts = { maxPages, concurrency, discoveryOnly, fromManifest, excludeCategory, phase, reFetch, keepHtml, markdown, merge, parallel, workers, emitReport, reportPath }
```

**理由**: 三个路径需要的参数子集不同，传入完整 `opts` 对象会导致各函数内部重新解构。但为保持简洁和最小改动，**实际采用传入 opts 对象**（同 `runCrawl` 当前的内部解构模式），避免为每个函数定义不同参数列表带来的维护负担。

### 决策 3: 每个函数独立 return，runCrawl 不做收尾

每个提取函数内部做完整的 `return makeResult(...)`。原 `runCrawl()` 中三路之后的公共逻辑（manifest 写入、产物收集、report 生成）已被各函数独立处理。

**理由**: 三路之间不存在共享的收尾逻辑——MediaWiki API 路径和 discovery-only 路径在函数内部提前 return，Scrapling 路径有自己完整的结果构造。提取后每条路径自包含。

### 决策 4: 代码移动策略 — 纯移动，不改逻辑

代码从 `runCrawl()` 中剪切粘贴到对应子函数，不做任何逻辑修改。

**验证策略**: 对 bindingofisaacrebirth.wiki.gg 站点的完整 crawl 输出在重构前后 diff 为空（除时间戳外）。

### 决策 5: runCrawl 精简后结构

```javascript
async function runCrawl(repoRoot, repoRef, resolutionMode, targetUrl, opts = {}) {
  // 1. 解构 opts (不变)
  const { ... } = opts;

  // 2. 路径与策略解析 (不变)
  const { runDir, reportPath } = buildRunPaths(...);
  const { strategy } = findStrategy(...);
  // ... 无策略 / 无入口点的错误处理 (不变)

  // 3. 路由
  if (apiConfig && apiConfig.platform === "mediawiki") {
    return runCrawlMediawikiApi(repoRoot, runDir, targetUrl, strategy, startPage, opts);
  }

  if (discoveryOnly && !doc?.api?.platform) {
    return runCrawlScraplingDiscovery(repoRoot, runDir, targetUrl, strategy, startPage, opts);
  }

  return runCrawlScrapling(repoRoot, runDir, targetUrl, strategy, startPage, matchingPage, entryPoints, opts);
}
```

## Risks / Migration

| 风险 | 可能性 | 缓解 |
|------|--------|------|
| 剪切粘贴时遗漏变量声明 | 低 | 每个子函数内部的变量声明与原代码一一对应，diff 对比确认无遗漏 |
| 闭包变量引用断裂 | 低 | 所有路径使用独立变量作用域，不依赖外层 `runCrawl` 的闭包变量 |
| 错误处理路径遗漏 | 低 | 所有 `return makeResult(...)` 和 handoff 生成逻辑原样移动 |
| 测试因行号变化失败 | 低 | `tests/chrome-agent-runtime.test.mjs` 不依赖具体行号 |
