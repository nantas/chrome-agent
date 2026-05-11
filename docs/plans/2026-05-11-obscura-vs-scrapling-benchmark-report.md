# Obscura vs Scrapling 批量爬取对比基准测试报告

> 测试日期: 2026-05-11
> 测试环境: macOS ARM64 (Apple M-series), 本地网络直连

## 测试目标

在有限页面样本上对比 Obscura v0.1.2 与 Scrapling 在批量/多页爬取场景下的效率与产出质量，验证将 Obscura 并行爬取能力整合到 chrome-agent 主工作流的可行性。

## 测试方法

### 实验设计

```
┌──────────────────────────────────────────────────────────┐
│                     测试矩阵                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  样本: 8 URLs × 3 页面类型                               │
│  ├── static (3):  example.com, httpbin.org/html,         │
│  │               info.cern.ch                            │
│  ├── dynamic (3): news.ycombinator.com,                  │
│  │               quotes.toscrape.com,                    │
│  │               books.toscrape.com                      │
│  └── article (2): Wikipedia × 2                          │
│                                                          │
│  引擎配置:                                                │
│  ├── Scrapling get   (HTTP, 串行单页)                    │
│  ├── Scrapling fetch (Playwright, 串行单页)              │
│  ├── Obscura fetch   (V8 headless, 串行单页)             │
│  ├── Obscura scrape  (V8 worker pool, 并行×8)            │
│  └── Obscura scrape+eval (并行×8 + JS表达式抽取)          │
│                                                          │
│  压力测试: 20 URLs × concurrency {5, 10, 20}            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 工具链

| 引擎 | 版本 | 路径 |
|------|------|------|
| Scrapling CLI | latest | `~/.cache/chrome-agent-scrapling/bin/scrapling` |
| Obscura CLI | v0.1.2 | `~/.cache/chrome-agent-obscura/bin/obscura` |
| Obscura Worker | v0.1.2 | `~/.cache/chrome-agent-obscura/bin/obscura-worker` |
| 测试平台 | Python 3 + subprocess | 精确计时（time.monotonic） |

### 测量指标

- **总耗时 (wall-clock ms)**：完整批次完成时间
- **Per-URL 耗时 (ms)**：每个 URL 从提交到结果返回的延迟
- **内容大小 (bytes)**：返回 HTML 的原始大小（间接衡量内容完整性）
- **成功率**：成功返回 vs 超时/错误比例
- **加速比**：串行总耗时 / 并行 wall-clock 耗时

## 测试结果

### 核心数据：8 页串行 vs 并行

| 引擎 | 总耗时 (ms) | 加速比 (vs 并行×8) |
|------|-----------|-------------------|
| Scrapling get (HTTP串行) | 7,928 | 2.4× slower |
| Scrapling fetch (Playwright串行) | 17,310 | 5.3× slower |
| Obscura fetch (V8串行) | 12,894 | 4.0× slower |
| **Obscura scrape (并行×8)** | **3,256** | **baseline** |
| Obscura scrape+eval (并行×8) | 3,240 | ~equal |

### 逐页耗时对比

| URL | Scl-get | Scl-fetch | Obsc-ser | Obsc-scrape(×8) |
|-----|---------|-----------|----------|-----------------|
| example.com | 466ms | 1,682ms | 415ms | 428ms |
| httpbin.org/html | 1,274ms | 1,980ms | 1,024ms | 1,054ms |
| info.cern.ch | 1,523ms | 2,409ms | 1,453ms | 1,454ms |
| news.ycombinator.com | 814ms | 1,869ms | 1,225ms | 1,204ms |
| quotes.toscrape.com | 1,010ms | 2,075ms | 1,789ms | 1,794ms |
| books.toscrape.com | 1,182ms | 2,733ms | 3,285ms | 3,250ms |
| wiki/Web_scraping | 915ms | 2,162ms | 1,913ms | 1,758ms |
| wiki/Headless_browser | 739ms | 2,396ms | 1,781ms | 1,694ms |

### 内容完整性对比

| URL | Scrapling-get | Obscura-serial | 比率 |
|-----|--------------|---------------|------|
| example.com | 512B | 530B | 1.04× |
| httpbin.org/html | 3,715B | 3,739B | 1.01× |
| info.cern.ch | 639B | 663B | 1.04× |
| news.ycombinator.com | 35,174B | 35,253B | 1.00× |
| quotes.toscrape.com | 10,603B | 11,015B | 1.04× |
| books.toscrape.com | 49,315B | 51,026B | 1.03× |
| wiki/Web_scraping | 162,011B | 166,051B | 1.02× |
| wiki/Headless_browser | 99,029B | 102,977B | 1.04× |

**结论：Obscura HTML 稳定比 Scrapling 大 1-4%，内容实质等价，无信息损失。**
差异原因推测为 V8 渲染引擎注入剩余空白/属性，不影响内容提取质量。

### 高并发压力测试：20 URLs

| concurrency | wall-clock | 成功率 | avg per-URL | min | max |
|-------------|-----------|--------|-------------|-----|-----|
| 5 | 8,879ms | 20/20 | 1,948ms | 1,576ms | 3,220ms |
| 10 | 4,903ms | 20/20 | 1,827ms | 1,200ms | 3,244ms |
| 20 | 3,271ms | 20/20 | 1,835ms | 1,205ms | 3,264ms |

**关键发现：**

```
加速曲线:
concurrency 5  → 10:  1.81× 加速 (近线性)
concurrency 10 → 20:  1.50× 加速 (收益递减)
```

并发 >10 后瓶颈从 worker 调度转移到 **目标站响应速度 + 网络带宽**。这是健康信号 — 说明 worker 本身不是瓶颈。

### Worker 稳定性

- 整轮测试 0 worker 崩溃
- 40 次 worker 启动全部成功
- 所有 URL 正确返回标题和内容

## 关键发现

### 1. Worker Binary 可用性 ✅

v0.1.2 release tarball 同时包含 `obscura` 和 `obscura-worker`，三平台覆盖（macOS ARM64, Linux x86_64, Windows x86_64）。当前 chrome-agent preflight 固定在 **v0.1.0**，需升级到 v0.1.2 才能获得 worker binary。

### 2. 并行架构成熟 ✅

```
obscura scrape <urls...> --concurrency N
  ↓
tokio::sync::Semaphore(N)
  ↓ (并行派生子进程)
obscura-worker × N  (每个独立 BrowserContext)
  ↓ stdin/stdout JSON 协议
navigate → [evaluate] → shutdown
  ↓
JSON 输出: {total_time_ms, results: [{url, title, eval, time_ms, worker}]}
```

### 3. Scrapling 无原生并行能力 ⚠️

`scrapling-bulk-fetch` 在 engine-registry 注册为 `playwright_bulk`（rank 4, score 61），但实际 CLI 仅支持单 URL 操作。批量需外部串行循环。

### 4. 对整站爬取的意义

```
当前 crawl/scrape 工作流:
  URL 遍历 (Scrapling 串行)  →  每页 ~1-3s
  100 页 = 100-300s

整合 Obscura 并行后:
  URL 遍历 (Scrapling get)   →  发现所有链接
  ↓
  批量 fetch (Obscura scrape)  →  100 页 ≈ 10-20s (并行×10-20)
  ↓
  内容归一化 → Markdown

理论加速: 10-30× (取决于页面类型和目标站限速)
```

### 5. 已知限制

| 限制 | 说明 |
|------|------|
| 高保护页面 | Obscura worker 无 stealth TLS，不适合 Cloudflare/reCAPTCHA |
| JS 子集 | 无 WebSocket/Service Worker 支持（与当前限制一致） |
| 内存 | 每个 worker ~50MB 峰值，100 worker ≈ 5GB（建议上限 20-30） |
| 并发上限 | 超过 20 并发后收益递减，建议默认 10，上限 30 |

## 建议

1. **立即更新 preflight** 到 v0.1.2，确保 `obscura-worker` 被安装
2. **新增 engine `obscura-bulk-scrape`** 作为 `cdp_lightweight_bulk` 类型，rank 介于 scrapling-get 和 scrapling-fetch 之间
3. **crawl/scrape 两阶段改造**：Scrapling 发现 URL → Obscura 并行 fetch
4. **默认并发 10**，自适应调节，上限 30

## 原始数据

测试输出保存于 `/tmp/obscura-benchmark/results/`，包含：

- `raw-results.json`：结构化时序数据
- `parallel-8.json`：Obscura 并行×8 完整输出
- `parallel-8-eval.json`：Obscura 并行+eval 完整输出
- `parallel-heavy.json`：Obscura 重页测试输出
