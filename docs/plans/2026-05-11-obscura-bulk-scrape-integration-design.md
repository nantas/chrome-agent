# Obscura 并行爬取整合方案设计（v2 — 根据交汇分析修正）

> 设计日期: 2026-05-11
> 基于:
> - [Obscura vs Scrapling 基准测试报告](./2026-05-11-obscura-vs-scrapling-benchmark-report.md)
> - [Obscura 爬取管线交汇分析](./2026-05-11-obscura-crawl-convergence-analysis.md)

## 1. 问题定义

### 当前状态

chrome-agent 有两条独立的内容获取管线：

```
┌─ 管线 A: 基于 Scrapling 的爬取 ──────────────────────────┐
│ 适用: 无 API 的 HTML/JS 站点                               │
│ crawl/scrape → strategy → Scrapling get/fetch 串行        │
│ → Markdown 转换                                            │
│                                                            │
│ 性能: 8页 8-17s (串行)                                     │
│ 每页 ~1-3s（不含 Playwright 启动开销）                      │
└────────────────────────────────────────────────────────────┘

┌─ 管线 B: MediaWiki API 提取 ─────────────────────────────┐
│ 适用: wiki.gg, Fandom, Weird Gloop 等                     │
│ crawl → strategy → api.platform=mediawiki?                │
│ → 路由到 scripts/mediawiki-api-extract (Python)            │
│ → Phase A: API 发现 (category_members)                     │
│ → Phase B: API 内容获取 (action=parse)                     │
│ → Phase C: 结构化后处理 (template_map, taxonomy)           │
│ → 结构化 Markdown + frontmatter                            │
│                                                            │
│ 性能: API 调用已高效 (<1s/页)                                │
│ 但不涉及 browser 引擎                                       │
└────────────────────────────────────────────────────────────┘
```

### 关键诊断（2026-05-11 交汇分析）

**Obscura `scrape` 子命令不返回页面内容。**

```json
{"url": "...", "title": "...", "eval": null, "time_ms": 1259, "worker": 0}
// ❌ 无 html, 无 text, 无 content
```

`scrape` 是**元数据批处理工具**，不是内容批获取工具。

**可实现完整内容并行获取的路径：**

`obscura serve --workers N` 启动 worker pool，每个 worker 是完整 CDP endpoint，然后并发下发 `obscura fetch --dump html` 到不同 worker，**返回完整 HTML**。

验证结果：3 workers + 4 并发 fetch → 3.3s 获取 4 页完整 HTML（含 166KB Wikipedia 页）✅

### 目标（修正后）

将 Obscura 的 **serve + 并发 fetch 模式**整合到 chrome-agent，专门替代**管线 A（非 API 站点的批量爬取）**。管线 B（MediaWiki API）保持独立，Obscura 仅作为 fallback。

### 设计原则

1. **管线分离**：管线 A（browser）可被 Obscura 加速，管线 B（API）保持独立
2. **serve 生命周期管理**：chrome-agent 管理 obscura serve 的启动/停止
3. **内容归一化**：Obscura serve fetch 的 HTML 走现有 Markdown 转换 pipeline
4. **降级透明**：Obscura serve 不可用时回退到 Scrapling 串行

## 2. 架构设计

### 2.1 新增引擎：`obscura-serve-pool`

> ⚠️ 不是 `obscura-bulk-scrape`！因为 `scrape` 子命令只返回元数据。
> 使用 `obscura serve --workers N` + 并发 `fetch` 模式获取完整内容。

```
┌──────────────────────────────────────────────────────┐
│             引擎生态（新增后）                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  rank 1 | scrapling-get      | http                  │
│  rank 2 | obscura-fetch      | cdp_lightweight       │
│  rank 3 | obscura-serve-pool | cdp_lightweight_pool  │  ★ 新增
│  rank 4 | scrapling-fetch    | playwright            │
│  rank 5 | scrapling-bulk-fetch | playwright_bulk     │
│  rank 5 | cloakbrowser-fetch | playwright_stealth    │
│  rank 6 | chrome-devtools-mcp| cdp_managed           │
│  rank 7 | chrome-cdp         | cdp_live              │
│                                                      │
│  管线 B（MediaWiki API）不在此引擎生态内               │
│  两条管线是正交的，由 strategy frontmatter 路由        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 2.2 整合架构

```
┌──────────────────────────────────────────────────────────────┐
│              Obscura 整合架构（serve 模式）                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  管线 A (非 API 站点):                                       │
│                                                              │
│  ┌────────────┐    ┌──────────────────┐   ┌────────────────┐│
│  │ crawl/     │───▶│ Phase 1: 遍历    │──▶│ Phase 2: 并行  ││
│  │ scrape     │    │ (Scrapling get)  │   │ 内容获取       ││
│  │ 命令入口   │    │ → 发现 URLs      │   │                ││
│  └────────────┘    └──────────────────┘   │ +─── serve ─── ││
│                                           │ │ workers 3-10 ││
│  ┌───────────────────────┐                │ │ 并发 fetch  ││
│  │ Phase 3: Markdown 转换│◀───────────────│ │ → 完整 HTML ││
│  │ (现有 pipeline)       │                │ └───────────── ││
│  └───────────────────────┘                └────────────────┘│
│                                                              │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│                                                              │
│  管线 B (MediaWiki API 站点):                                │
│                                                              │
│  crawl → strategy → api.platform=mediawiki                   │
│  → mediawiki-api-extract (独立 Python pipeline)              │
│  → Phase A (发现) → Phase B (内容) → Phase C (后处理)       │
│  → 结构化 Markdown + frontmatter                             │
│                                                              │
│  ★ 两条管线互不干扰，由 strategy frontmatter 决定路由         │
│  ★ Obscura 只优化管线 A，不影响管线 B                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 关键交互流程

```
┌──────────────────────────────────────────────────────────────┐
│          Obscura serve + 并发 fetch 批量流程                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Obscura Preflight (v0.1.2)                               │
│     ├── 检查 OBSCURA_CLI_PATH                                │
│     ├── 检查 ~/.cache/chrome-agent-obscura/bin/obscura       │
│     ├── 确认 obscura-worker 存在                             │
│     └── 失败回退 → Scrapling 串行                            │
│                                                              │
│  2. URL 集合构建                                             │
│     ├── crawl: 策略驱动遍历收集 URLs                         │
│     ├── scrape: 递归提取收集 URLs                            │
│     └── (新增) fetch --parallel: 直接从参数获取 URL 列表     │
│                                                              │
│  3. 启动 Obscura serve worker pool                           │
│     └── obscura serve --workers N --port <PORT>              │
│         → spawns N worker 进程                                │
│         → 负载均衡器监听 <PORT>，轮询分配请求到 worker       │
│         → 每个 worker 是完整 CDP endpoint                    │
│                                                              │
│  4. 并发下发 fetch 到 worker pool                            │
│     └── 使用 ThreadPoolExecutor(max_workers=N)               │
│         → 每个线程: obscura fetch <URL> --dump html          │
│         → 负载均衡器自动轮询到不同 worker                    │
│         → 返回完整 HTML                                      │
│                                                              │
│  5. 关闭 serve                                              │
│     └── kill worker pool → 清理进程                          │
│                                                              │
│  6. Markdown 转换 (现有 pipeline)                            │
│     └── convertTraversalToMarkdown(runDir, manifest, opts)   │
│         → 与当前 Scrapling 串行走完全相同代码路径            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**关键差异 vs 原方案：**

| 维度 | 原方案 (scrape) | 修正方案 (serve+fetch) |
|------|----------------|------------------------|
| 返回内容 | ❌ 仅元数据 | ✅ 完整 HTML |
| Worker 生命周期 | Obscura 管理 | chrome-agent 管理 |
| 并发模型 | 内置 Semaphore | ThreadPoolExecutor |
| Markdown 转换 | ❌ 需新实现 | ✅ 复用现有 pipeline |
| 内容归一化 | ❌ 需要新转换 | ✅ 不需要（HTML已有） |
| 复杂度 | 低（一行命令） | 中（管理 serve） |

## 3. 组件变化明细

### 3.1 Preflight 更新

**文件**: `docs/playbooks/obscura-cli-preflight.md`

| 变更项 | 当前值 | 目标值 |
|--------|--------|--------|
| 版本 | `0.1.0` | `0.1.2` |
| 下载 URL | `v${VERSION}/obscura-...` | 同格式，版本翻新 |
| 安装后验证 | 仅验证 `obscura --help` | 增加 `obscura-worker --help` 验证 |
| Worker 安装 | 未处理 | 从 tarball 自动解压 `obscura-worker` |

关键变化：解压脚本无需改动（tarball 已含 worker），但验证步骤需确保 worker 也在同一目录。

### 3.2 Engine Registry 新增

**文件**: `configs/engine-registry.json`

新增 `obscura-bulk-scrape` 条目：

```json
{
  "id": "obscura-bulk-scrape",
  "type": "cdp_lightweight_bulk",
  "characteristics": {
    "efficiency": {
      "score": 0.85,
      "note": "Rust+V8 worker pool. Each worker ~50MB peak, JSON stdin/stdout IPC. Near-linear scaling up to concurrency 10-15."
    },
    "stability": {
      "score": 0.65,
      "note": "v0.1.2. Tested with 20 concurrent workers across 20 URLs with zero failures. Worker lifecycle managed by obscura scrape command."
    },
    "adaptability": {
      "score": 0.60,
      "note": "Handles dynamic content and SPA via per-worker V8 engine. Not suitable for high-protection pages (no stealth TLS). Supports JS eval per-URL for custom extraction."
    }
  },
  "composite_score": 68,
  "default_rank": 3,
  "best_for": ["bulk_dynamic", "bulk_list", "batch_fetch", "page_batch"],
  "contract_spec": "obscura-bulk-scrape-contract",
  "status": "draft"
}
```

Rank 定位说明：介于 `obscura-fetch` (rank 2) 和 `scrapling-fetch` (rank 4) 之间，与 `scrapling-bulk-fetch` (rank 4) 同级。当需要批量获取多个 JS 渲染页面时优先选择。

### 3.3 Contract Spec 新增

**文件**: `openspec/specs/obscura-bulk-scrape/spec.md`（新建）

核心契约：

| 契约项 | 规格 |
|--------|------|
| 输入 | URL 数组, 并发数(默认10), 超时(默认15s), 可选 eval JS |
| 输出 | JSON 含 total_time_ms + per-result {url, title, eval?, time_ms, error?} |
| preflight | Obscura v0.1.2+ CLI, worker binary 在同一目录 |
| 错误处理 | per-URL 超时不影响其他 URL，失败 URL 带 error 字段 |
| 并发上限 | 默认 10，建议上限 30，超过后收益递减 |
| 降级策略 | Obscura 不可用时回退到 Scrapling 串行 fetch |

### 3.4 CLI 改造

**文件**: `scripts/chrome-agent-cli.mjs`

#### 3.4.1 新增 `runObscuraServePool` 函数

```javascript
function runObscuraServePool(repoRoot, urls, opts = {}) {
  const {
    workers = 5,
    timeout = 15,
  } = opts;

  const obscuraPath = resolveObscuraCliPath(repoRoot);
  if (!obscuraPath) {
    return { ok: false, error: "Obscura CLI not available" };
  }

  // Step 1: Find available port
  const basePort = findAvailablePort(9200);

  // Step 2: Start serve worker pool
  const serveProcess = spawn(obscuraPath, ["serve", "--workers", String(workers), "--port", String(basePort)], {
    stdio: "ignore",
    detached: true,
  });
  
  // Step 3: Wait for workers to be ready
  await sleep(2000);

  // Step 4: Concurrent fetch via worker pool
  const results = [];
  const pool = new ThreadPoolExecutor(max_workers: workers);
  const futures = urls.map(url => pool.submit(() => {
    const result = spawnSync(obscuraPath, ["fetch", url, "--dump", "html", "--quiet", "--timeout", String(timeout)]);
    return { url, html: result.stdout, elapsed_ms: result.duration };
  }));

  // Step 5: Cleanup
  process.kill(-serveProcess.pid);

  return { ok: true, results };
}
```

#### 3.4.2 修改 `runEngineFetch` 路由

扩展当前路由逻辑：

```javascript
function runEngineFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs = []) {
  // Existing dispatch
  switch (fetcher) {
    case "cloakbrowser": return runCloakbrowserFetch(...);
    case "obscura": return runObscuraFetch(...);     // single-page obscura
    // scrapling variants...
  }
  return runScraplingFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs);
}

// 新增: 批量页面的 Obscura 并行 fetch
function runBatchFetch(repoRoot, urls, outputDir, opts = {}) {
  // 先尝试 Obscura 并行
  if (obscuraAvailable) {
    const result = runObscuraBulkFetch(repoRoot, urls, opts);
    if (result.ok) {
      // 将 JSON 结果归一化为 per-URL HTML 文件
      return normalizeObscuraResults(result.data, outputDir);
    }
  }
  // 降级: Scrapling 串行
  return runScraplingBatchFetch(repoRoot, urls, outputDir, opts);
}
```

#### 3.4.3 crawl/scrape 命令新增 `--parallel` 标志

```
Usage: chrome-agent crawl <url> [--parallel] [--workers <n>]
       chrome-agent scrape <url> [--parallel] [--workers <n>]
       chrome-agent batch <urls...> [--workers <n>]
```

**crawl 并行模式交互变更**：

```
当前:  遍历+串行fetch交织
       → 每步: Scrapling get(url) → 解析links → 入队列 → 重复

并行:  三阶段
       Phase 1: Scrapling get(url) 遍历 → 收集所有 visited URLs
                 (与当前一致，URL发现仍需轻量快速)
       Phase 2: obscura serve --workers N → 并发 fetch 所有 URLs
                 (每个 worker 返回完整 HTML)
       Phase 3: convertTraversalToMarkdown (与当前一致，HTML已就位)
```

注意：`--workers` 控制 Obscura worker pool 大小，而非 scrape 的 concurrency。

#### 3.4.4 新增 `batch` 命令

支持直接传入 URL 列表进行纯批量抓取（绕过遍历，直接并行 fetch）：

```
chrome-agent batch url1 url2 url3 ... \
  [--workers 5] [--timeout 15] [--markdown]
```

使用场景：
- 下游工具已提供 URL 列表
- MediaWiki API Phase A 产出 URL 清单后的批量 fetch
- 定时批量更新已知页面

#### 3.4.5 管线路由逻辑更新

```javascript
function runCrawl(repoRoot, repoRef, resolutionMode, targetUrl, opts) {
  // Step 1: 读 strategy frontmatter
  const strategy = loadStrategy(targetUrl);

  // Step 2: 管线路由 — API vs Browser
  if (strategy.api?.platform === "mediawiki") {
    // 管线 B: MediaWiki API（不涉及 Obscura）
    return runMediaWikiApiPipeline(repoRoot, strategy, targetUrl);
  }

  // 管线 A: Browser 爬取
  if (opts.parallel && obscuraAvailable()) {
    // Obscura 并行模式
    return runParallelCrawl(repoRoot, targetUrl, strategy, opts);
  } else {
    // Scrapling 串行模式（默认 / 降级）
    return runSerialCrawl(repoRoot, targetUrl, strategy, opts);
  }
}
```

### 3.5 内容归一化（serve 模式）

**无需额外归一化步骤。**

Obscura serve + 并发 fetch 返回的是**标准 HTML**——与 Scrapling `extract get` / `extract fetch` 输出完全兼容。

```javascript
function runParallelCrawl(repoRoot, targetUrl, strategy, opts) {
  // Phase 1: 遍历收集 URLs（Scrapling get，与当前一致）
  const visitedUrls = traverseSite(targetUrl, strategy, opts.maxPages);
  
  // Phase 2: 启动 Obscura serve + 并发 fetch
  const servePool = startObscuraServe(workers: opts.workers || 5);
  const htmlFiles = servePool.concurrentFetch(visitedUrls);
  servePool.stop();
  
  // htmlFiles = [{url, pageNum, htmlPath}, ...]
  // HTML 文件结构、命名规则与 Scrapling 串行模式完全一致
  
  // Phase 3: Markdown 转换（同一函数，零改动）
  return convertTraversalToMarkdown(repoRoot, runDir, manifest, opts);
}
```

| 输出 | Scrapling 串行 | Obscura serve 并行 | 差异 |
|------|---------------|-------------------|------|
| HTML 文件 | `01.html` | `01.html` | 文件名规则一致 |
| 内容格式 | 标准 HTML | 标准 HTML | ✅ 一致 |
| Markdown 管线 | `convertTraversalToMarkdown` | 同一函数 | ✅ 一致 |
| 内容大小 (example.com) | 512B | 530B | <4% |
| 错误日志 | `01.stderr.log` | `01.stderr.log` | ✅ 一致 |

## 4. 实现路线

### Phase 0: 概念验证（1 天）

```
Task 0.1: 验证 obscura serve 模式稳定性
  - serve --workers 10 + 20 并发 fetch 压力测试
  - serve 启动/停止生命周期测试
  - 验证内容完整性 vs Scrapling

Task 0.2: 确定端口管理策略
  - 端口发现逻辑（findAvailablePort）
  - serve 进程归零保证（timeout kill）
  - 并发 fetch 与 worker 数的比例关系
```

### Phase 1: 基础就绪（1-2 天）

```
Task 1.1: 更新 Obscura preflight 到 v0.1.2
  - 修改 docs/playbooks/obscura-cli-preflight.md
  - 版本号: 0.1.0 → 0.1.2
  - 增加 worker binary 验证步骤
  - 更新下载 URL（格式不变）

Task 1.2: 注册新引擎
  - 新增 configs/engine-registry.json 条目 (obscura-serve-pool)
  - 新增 openspec/specs/obscura-serve-pool/spec.md

Task 1.3: doctor 增加 Obscura CLI 检测
  - doctor 命令增加 Obscura 状态检查
  - 报告 obscura + obscura-worker 是否存在
```

### Phase 2: CLI 集成（3-4 天）

```
Task 2.1: 实现 Obscura serve 生命周期管理
  - runObscuraServePool():
    a. 找可用端口
    b. spawn obscura serve --workers N --port PORT
    c. 等待 worker 就绪（轮询端口或固定 sleep）
    d. 返回 serveHandle（含 process, port）
  - stopObscuraServe(handle):
    a. kill 进程组
    b. 释放端口

Task 2.2: 实现并发 fetch 调度
  - concurrentFetch(serveHandle, urls):
    a. ThreadPoolExecutor(max_workers=serveHandle.workers)
    b. 每个线程: obscura fetch URL --dump html --quiet --timeout T
    c. 负载均衡器自动轮询到不同 worker（内置功能）
    d. 返回 {url, html, elapsed_ms, error?}

Task 2.3: crawl/scrape 支持 --parallel 标志
  - --workers <n> 参数传递（默认 5，上限 20）
  - 三阶段分离: 遍历收集 → serve+fetch → markdown
  - 降级回退逻辑（Obscura 不可用时 → Scrapling 串行）

Task 2.4: 新增 batch 命令
  - chrome-agent batch <urls...> [--workers 5] [--markdown]
  - 绕过遍历，直接并行 fetch
```

### Phase 3: 引擎自动选择（1-2 天）

```
Task 3.1: strategy 驱动的引擎路由
  - api.platform=mediawiki → 管线 B (API)
  - else → 管线 A (Browser)
    - --parallel 且 Obscura 可用 → Obscura serve pool
    - 否则 → Scrapling 串行

Task 3.2: 降级测试
  - Obscura serve 启动失败 → 回退 Scrapling
  - Obscura serve 中途死掉 → 重新启动或回退
  - 部分 worker 不可用 → 降速但继续
```

### Phase 4: 集成测试（1 天）

```
Task 4.1: 基准测试回归
  - 重新运行 benchmark script 验证加速比
  - 对比 pre/post 整合结果

Task 4.2: 测试场景
  - 10 页动态站 (concurrency 5/10/20)
  - 混合静态+动态站 (自动引擎选择)
  - 降级场景 (Obscura 不可用时)
  - 大文件/长内容边界测试
```

## 5. 风险与考量

### 风险矩阵

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Obscura v0.1.2 bug 导致批量崩溃 | 高 | 低 | 降级到 Scrapling 串行 |
| Worker 内存泄漏 | 中 | 低 | 设置 concurrency 上限 20，per-worker timeout |
| 结果归一化导致内容丢失 | 中 | 低 | 保留原始 JSON 以备回溯 |
| 目标站限速/封禁 | 中 | 中 | adaptive concurrency 机制 |
| Obscura 无后续更新 | 低 | 低 | 引擎注册为 draft，随时可替换 |

### 架构决策记录 (ADR)

| 决策 | 理由 |
|------|------|
| 不修改 Obscura upstream | 避免 fork 维护成本，用 CLI wrapper 方式集成 |
| 不替换 Scrapling 遍历路径 | Scrapling get 在静态页面 URL 发现上更快更稳定 |
| `--parallel` 为可选标志 | 保持向后兼容，用户显式选择并行模式 |
| 默认 concurrency = 10 | 基准测试显示 10 是最佳性价比，20、30 收益递减 |

## 6. 成功指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 8 页动态站加速比 | ≥ 3× vs Scrapling 串行 | benchmark 脚本 |
| 20 页批量加速比 | ≥ 4× vs Scrapling 串行 | benchmark 脚本 |
| Obscura 成功率 | ≥ 95% | 连续 100 次批量调用 |
| 降级切换延迟 | < 100ms | Preflight 检测时间 |
| 内容完整性 | 差异 < 5% | HTML 大小对比 + 采样抽查 |

## 7. 参考

- [Obscura vs Scrapling 基准测试报告](./2026-05-11-obscura-vs-scrapling-benchmark-report.md)
- [Obscura CLI Preflight](../docs/playbooks/obscura-cli-preflight.md)
- [Obscura GitHub](https://github.com/h4ckf0r0day/obscura)
- [Scrapling Fetchers Guide](../docs/playbooks/scrapling-fetchers.md)
- [Engine Registry](../configs/engine-registry.json)
