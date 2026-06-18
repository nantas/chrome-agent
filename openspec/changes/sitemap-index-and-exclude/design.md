# Design

## Context

PostHog Docs（Docusaurus, 5,667 docs pages）暴露了 `sitemap-driven-crawl` v1 的两个硬限制：
1. sitemap index 不支持——PostHog 使用 `<sitemapindex>` + 子 sitemap，当前 detect 到即 handoff
2. 无 URL 排除机制——3,943 个 SDK references 页面无法过滤，全量爬取 7.9h 不切实际

这两个问题在 v1 spec 中被标记为 Deferred。本 change 收窄 scope 后实现一层 index + exclude_patterns，使 PostHog 类站点可用。

## Goals / Non-Goals

**Goals:**
- `parseSitemapXml()` 检测 `<sitemapindex>` 时提取子 sitemap URL，不再 handoff
- `runCrawlSitemapDiscovery()` 迭代 fetch 子 sitemap → parse → Set 去重 → 合并
- `discovery.exclude_patterns` 可选字段，在 page_pattern include 后应用排除规则
- 子 sitemap 部分失败时继续（warnings + caveats），全部失败才 handoff
- PostHog 策略：`sitemap_url` 指向子 sitemap + `exclude_patterns: ["exact:/docs/references/**"]`

**Non-Goals:**
- 递归 sitemap index（index → index → urlset）
- 并发 fetch 子 sitemap
- `--exclude-category` 对 sitemap 路径的支持
- 负数 page_pattern 语法（如 `!exact:...`）

## Decisions

### D1: parseSitemapXml 保持纯解析，discovery 层做迭代

`parseSitemapXml()` 不发起 HTTP 请求。index 检测时返回 `{ isIndex: true, sitemaps: ["https://..."] }`，`runCrawlSitemapDiscovery()` 负责迭代 fetch。

**理由**：关注点分离。parse 函数可纯单元测试，fetch + error handling 逻辑集中在 discovery 函数中。与现有 curl-based fetch 模式一致。

### D2: 子 sitemap 迭代串行，使用 Set 去重

每个子 sitemap 独立 curl → parse → 收集 URL → push 到 `allUrls` 数组，最终 `[...new Set(allUrls)]` 去重。

**理由**：v1 最小实现，避免并发 fetch 的复杂度（错误处理、event loop）。PostHog 只有 1 个子 sitemap，串行无性能影响。Set 去重简单可靠。

### D3: exclude_patterns 放在 discovery 块顶层

`discovery.exclude_patterns: ["exact:/docs/references/**"]` —— 独立于 page_pattern，在 include 过滤后、auto-group 前执行。

**理由**（grill-me Q4）：
- 语义正交：include（page_pattern）和 exclude（exclude_patterns）是两件独立的事
- 执行顺序明确：先 include → 再 exclude，无歧义
- 数据结构扁平：不修改 page_pattern 解析逻辑，也不在 page 条目中嵌套

### D4: 部分失败继续，非 handoff

单个子 sitemap fetch/parse 失败 → 记录 warning + caveat → 继续处理其余子 sitemap。仅当全部子 sitemap 失败时才 handoff。

**理由**（grill-me Q5）：PostHog 只有 1 个子 sitemap，败了就挂了。但为多子 sitemap 场景设计，1/3 失败不应阻挡其余内容。

### D5: 合并为单个 change（index + exclude）

两个增量能力放入一个 change：`sitemap-index-and-exclude`。

**理由**（grill-me Q6）：改动集中在同一个文件（`parseSitemapXml` + `runCrawlSitemapDiscovery`），PostHog 策略同时依赖两者。拆两个 change 会导致第二个在第一个未落地时无法端到端验证。

### D6: PostHog 策略显式 sitemap_url

PostHog 的 sitemap 在非标准位置（`/sitemap/sitemap-index.xml`），需在策略中显式指定。`sitemap_url` 指向 `https://posthog.com/sitemap/sitemap-0.xml`（绕过 index，或保持不变让 index 解析管线处理）。

**理由**：PostHog 的 sitemap index 只有 1 个子 sitemap，显式指向子 sitemap 可简化实现验证。index 解析能力对后续多子 sitemap 站点（如 Mintlify）有用。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `parseSitemapXml` 返回值类型变更导致未预期的调用方异常 | Low | Low — 仅 `runCrawlSitemapDiscovery` 调用 | 现有调用方只检查 `parsed.isIndex`（`true` → handoff），新增 `sitemaps` 字段不影响现有分支 |
| 子 sitemap 内容巨大（>100MB）→ OOM | Low | Medium | v1 无 size guard，PostHog 子 sitemap ~1.4MB（14k URLs），在 Node.js 默认内存限制内 |
| exclude_patterns 语法与 page_pattern 不一致导致混淆 | Low | Low | 文档明确声明使用相同 `exact:` / `regex:` 前缀 |
| 向后兼容：扁平 sitemap 不受影响 | Very Low | High | `parsed.isIndex === false` 时走原路径，无代码路径变更 |
| PostHog sitemap URL 变更 | Low | Medium | 显式 `sitemap_url` 在策略中，变更时更新策略即可 |
