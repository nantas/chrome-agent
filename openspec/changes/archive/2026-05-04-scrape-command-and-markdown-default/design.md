# Design

## Context

`chrome-agent` 当前有两条内容获取路径：

- `fetch`：单页获取，直接产出 Markdown（通过 `scrapling extract ... --ai-targeted`），质量已验证
- `crawl`：策略引导的多页遍历，但默认产出原始 HTML，需要额外转换

用户反馈的核心矛盾：
1. `crawl` 默认 HTML 输出与 `fetch` 的 Markdown 输出不统一，造成工作流断裂
2. `crawl` 强制依赖 `site-strategy`，但许多简单站点（MediaWiki、静态文档站）不需要策略就能有效遍历

本 change 解决这两个问题：将 `crawl` 默认改为 Markdown 输出（复用 `fetch` 已验证的 `--ai-targeted` 机制），同时新增 `scrape` 命令填补"无策略递归爬取"的空位。

## Goals / Non-Goals

**Goals:**
- `crawl` 默认产出 Markdown（.md），保留 `--no-markdown` 回退到 HTML
- `crawl` 支持 `--merge` 合并为单一文件，`--concurrency` 控制 Phase 2 并发
- 新增 `scrape` 命令：零配置、自发现链接、同域过滤、URL pattern 匹配、默认 Markdown
- 提取可复用的 `convertTraversalToMarkdown` 共享管线（`crawl` 和 `scrape` 共用）
- Phase 1 的 `.html` 中间产物在 Phase 2 完成后自动清理

**Non-Goals:**
- 不修改 Scrapling 本身（仅复用现有 `--ai-targeted` 能力）
- 不引入本地 HTML→Markdown 转换工具（pandoc/turndown 等）
- 不修改站点策略 schema 或策略引导逻辑
- 不改动 `fetch`、`explore`、`doctor`、`clean` 命令的行为
- 不做认证会话复用的增强

## Decisions

### Decision 1: 两阶段架构（Traversal + Conversion）

**选择：** Crawl 和 scrape 均采用 Phase 1（HTML traversal）+ Phase 2（Markdown conversion）的两阶段架构。

**理由：**
- 递归遍历需要解析 HTML 中的 `<a href>` 提取链接，HTML 是必需的中间产物
- Scrapling `extract` 单次调用只能输出一种格式
- 两阶段使"遍历"和"格式转换"解耦，便于独立调试和复用

**替代方案考虑过：**
- 本地 HTML→MD 转换：放弃，因为会丢失 Scrapling `--ai-targeted` 的 LLM 优化格式
- Scrapling 双输出：不可行，Scrapling 不支持单次调用双格式

### Decision 2: 共享 `convertTraversalToMarkdown` 管线

**选择：** 提取一个共享函数供 `runCrawl` 和 `runScrape` 调用，统一处理 Phase 2。

**接口：**
```javascript
async function convertTraversalToMarkdown({
  repoRoot,
  runDir,
  manifest,
  fetcherFn,        // (url) => fetcher name
  concurrency = 5,
  merge = false,
  cleanupHtml = true,
  outputName = "output", // "crawl-output" or "scrape-output"
})
```

**理由：**
- 避免在 `runCrawl` 和 `runScrape` 中重复 Phase 2 逻辑
- 并发控制、失败隔离、HTML 清理、merge 逻辑只需实现一次
- 未来新增需要 traversal+conversion 的命令可直接复用

### Decision 3: `scrape` 作为独立命令（非 crawl 的子模式）

**选择：** 新增 `scrape` 命令，而非让 `crawl --auto` 或 `crawl --no-strategy` 走无策略模式。

**理由：**
- `crawl` 和 `scrape` 的工作流语义差异大：一个策略引导、一个自发现
- 独立命令避免参数组合爆炸（`crawl` 已有 `--entry-point`、`--max-pages`，与 `scrape` 的 `--match`、`--same-domain` 不兼容）
- 符合 CLI 设计原则：每个命令做一件事，且从名字就能推断行为

### Decision 4: 并发实现采用 Promise pool（非 async.queue 或 worker_threads）

**选择：** Phase 2 并发使用简单的 Promise pool 模式（维护 pending promises 数组，达到上限时 `Promise.race` 等待）。

**理由：**
- Scrapling 调用是外部子进程，`Promise.all` + 手动限流足够
- 不需要 `async` 库依赖（当前 CLI 无此依赖）
- 不需要 worker_threads（IO-bound，非 CPU-bound）
- 实现简洁，约 20 行代码

### Decision 5: `--max-pages` 默认值差异

**选择：** `crawl` 保持默认 3，`scrape` 默认 10。

**理由：**
- `crawl` 用于精准遍历（策略已限定范围），3 页是安全默认值
- `scrape` 用于快速抓取，用户预期是"尽可能多"，10 页更符合心智模型
- 两者均可通过 `--max-pages` 覆盖

### Decision 6: HTML 中间产物默认清理、opt-out 保留

**选择：** `--markdown` 模式下 Phase 2 完成后自动删除 `.html` 文件；`--keep-html` 可保留。

**理由：**
- 用户调用 `--markdown` 时期望看到干净的 `.md` 文件，`.html` 是噪音
- 调试链接发现时需要查看 `.html`，`--keep-html` 提供逃逸舱
- 符合 output-lifecycle spec：中间产物是 disposable，最终产物是用户-facing

## Risks / Migration

### Breaking Change: `crawl` 默认输出从 HTML 变为 Markdown

**影响：** 现有脚本或自动化流程依赖 `crawl` 产出 `.html` 文件的行为会断裂。

**缓解：**
- 提供 `--no-markdown` 显式回退，一行改动即可恢复旧行为
- 在 CHANGELOG 中标记为 breaking change
- `crawl` 的 HTML 文件路径从 `outputs/<run>/XX-page.html` 变为 `outputs/<run>/XX.md`，脚本需要适配

### Risk: 2x 网络请求

**影响：** Phase 1（HTML）+ Phase 2（Markdown）意味着每个 URL 被请求两次。对于 467 页的 wiki，这是 934 次请求。

**缓解：**
- 对于静态站点（MediaWiki），每次请求极轻，压力可控
- `--concurrency` 控制并发度，默认 5，避免对目标站点造成冲击
- 未来可考虑缓存 Phase 1 的 HTTP response 避免重复请求（out of scope for v1）

### Risk: 并发 Scrapling 调用资源消耗

**影响：** 并发运行多个 Scrapling 进程可能消耗较多内存/CPU。

**缓解：**
- 默认并发 5，可下调至 1（串行）
- Scrapling 本身是轻量级 HTTP 客户端（`get` 模式），非完整浏览器
- 监控实际资源消耗，后续可调优默认值

### Risk: `scrape` 无策略导致噪音链接

**影响：** `scrape` 提取所有 `<a href>`，可能跟踪到编辑页、讨论页、特殊页等不想要的 URL。

**缓解：**
- `--same-domain` 默认开启，限制跨域
- `--match "/wiki/*"` 等 glob 过滤可大幅削减噪音
- `--max-pages` 提供硬上限，防止无限扩散
- 对于需要精准控制的场景，引导用户使用 `crawl` + 策略

### Migration Guide

| 场景 | 迁移前 | 迁移后 |
|------|--------|--------|
| 需要 crawl 产出 HTML | `chrome-agent crawl <url>` | `chrome-agent crawl <url> --no-markdown` |
| 批量抓取 wiki（无策略）| 无此能力 | `chrome-agent scrape <url> --match "/wiki/*" --max-pages 500 --merge` |
| 策略引导遍历 + Markdown | 无此能力（先 crawl 得 HTML，再转换） | `chrome-agent crawl <url>` |
