# Proposal

## 问题定义

`sitemap-driven-crawl` capability 已实现扁平 `<urlset>` sitemap 的全量 crawl（GameAnalytics 验证通过），但对 PostHog Docs（Docusaurus, 5,667 页，sitemap index）存在两个阻断性缺口：

**L1 — Sitemap index 不支持（S-line）**：PostHog 的 sitemap 使用 `<sitemapindex>` 嵌套单个子 sitemap (`sitemap-0.xml`)。当前 `parseSitemapXml()` 检测到 `<sitemapindex>` 直接返回 `{ isIndex: true }`，触发 handoff → Gate 停止。大量 Docusaurus 大站（PostHog、Mintlify、Nextra）使用 sitemap index 来拆分内容，v1 不支持意味着这些站点完全不可用。

**L2 — 无 URL 排除机制（S-line）**：PostHog 的 `references/` 目录包含 3,943 个自动生成的 SDK API reference 页面（多版本重复，占 docs 总量的 69.6%），但当前 `page_pattern` 仅支持正向 include 匹配，无法表达"排除某个目录"的语义。无 exclude 机制下，全量爬取 5,667 页耗时约 7.9 小时，不切实际。

**实证故障案例**：对 `posthog.com/docs` 执行 `crawl --discovery-only` → sitemap index → handoff。且即使绕过 index（手动指定子 sitemap URL），无法排除 references 目录 → 不可行。

## 范围边界

**In scope：**
1. `parseSitemapXml()` 增强：检测 `<sitemapindex>` 时提取子 sitemap URL 列表，返回 `{ isIndex: true, sitemaps: [...] }`
2. `runCrawlSitemapDiscovery()` 增强：index 路径下迭代 fetch 每个子 sitemap、parse、为 URL 去重（Set）、合并
3. 新增 `discovery.exclude_patterns` 字段：`["exact:/docs/references/**", "regex:^/docs/old/.*"]`，在 page_pattern include 过滤之后执行 exclude 过滤
4. 子 sitemap 部分失败处理：某个子 sitemap fetch/parse 失败 → 记录 warning + caveat → 继续处理其余子 sitemap → 产出合并 manifest
5. 修改 discovery block schema 文档：`sitemap_index_support: true`（内部，不暴露给策略）、`exclude_patterns` 字段
6. 新增 PostHog 站点策略：`discovery: { method: sitemap, sitemap_url: "https://posthog.com/sitemap/sitemap-0.xml", exclude_patterns: ["exact:/docs/references/**"] }`
7. 单元测试（node:test）+ PostHog live E2E validation
8. 更新 skill SKILL.md：sitemap index 已支持，移除"not yet supported"限制描述

**Out of scope (Deferred)：**
- Sitemap index 的递归嵌套（index → index → urlset）：不支持，仅一层 index
- `discovery.summary` 按子 sitemap 分组呈现
- `--exclude-category` 对 sitemap 路径的支持（仍无效）
- 并发 fetch 多个子 sitemap（v1 串行）

## Capabilities

### Modified Capabilities

- `sitemap-driven-crawl`: Extend sitemap discovery pipeline to support sitemap index resolution (iterate sub-sitemaps, merge URLs, deduplicate) and add `exclude_patterns` field to `discovery` block for URL exclusion after page_pattern include filtering. Update `parseSitemapXml()` to extract sub-sitemap URLs from `<sitemapindex>`, and `runCrawlSitemapDiscovery()` to handle multi-sitemap fetch with partial-failure resilience.

## Capabilities 待确认项

- [x] 能力清单已与用户确认（grill-me Q1-Q6 全部决策对齐）
- [x] Sitemap index 策略选择：parseXml 保持纯解析，discovery 层迭代 fetch
- [x] 多 sitemap 合并方式：统一 manifest，Set 去重
- [x] Exclude 机制位置：`discovery.exclude_patterns` 顶层字段
- [x] 部分失败处理：continue with warnings
- [x] 单个 change 同时包含 index + exclude（grill-me Q6: A）

## Impact

| 影响维度 | 说明 |
|---------|------|
| 新站点解锁 | PostHog Docs (5,667 docs pages)、以及所有使用 sitemap index 的静态文档站 |
| `parseSitemapXml()` | 返回值类型扩展：增加 `sitemaps` 字段（`isIndex: true` 时），保持向后兼容 |
| `runCrawlSitemapDiscovery()` | 在现有 sitemap fetch → parse → filter → group 流程中插入 index 解析分支 + exclude 过滤步骤 |
| `discovery` block schema | 新增 `exclude_patterns` 字段（optional, array of page_pattern strings） |
| 策略文件 | 新增 `sites/strategies/posthog.com/strategy.md` |
| SKILL.md | sitemap index 限制描述移除，标记为已支持 |
| 向后兼容 | 扁平 sitemap 路径不受影响（`parsed.isIndex` 为 false 时走原路径） |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：`binding.md` 全部确认
- 父 capability: `sitemap-driven-crawl` (`openspec/changes/sitemap-driven-crawl/specs/sitemap-driven-crawl/spec.md`)
