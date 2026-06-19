# Verification

## 验证结论

**结论：PASS（in-scope 全部满足；1 个 out-of-scope 抽取质量问题转入 follow-up）。**

本 change 的 spec delta 覆盖三类增量能力（sitemap index 解析合并 / 子 sitemap 部分失败韧性 / exclude_patterns 过滤）+ 四项 MODIFIED requirements。Live E2E（T7）+ 单元测试（T10）共同验证：PostHog（Gatsby 4.25.9，sitemap-index 站点）从"完全不可用"变为"discovery 可用"——14,576 条 sitemap URL 经 `page_pattern` include（保留 5,668）→ `exclude_patterns` 排除（移除 3,943 条 `/docs/references/**`）→ 最终 **1,725 页**，与策略预测的 ~1,725 完全吻合，manifest 中 **0 条 references**。

唯一缺口（**out-of-scope**）：T8 小规模 extraction 的 5 个 markdown 输出仅含 397 字节 nav/footer chrome，未抽取 `<article>` 正文（实测 `/docs/glossary` 正文 22,246 字符）。根因在 scrapling `--ai-targeted` 抽取路径，属父 capability `sitemap-driven-crawl` 的抽取引擎问题，本 change **未修改任何抽取代码**。discovery 维度（本 change 范围）已完整验证，不受影响。

## Spec-to-Implementation Coverage

> 行号基于 `scripts/chrome-agent-cli.mjs`（HEAD after T5 regression fix）。

### ADDED Requirements

| Requirement | 验证 | 证据 |
|---|---|---|
| `sitemap-index-resolve-and-merge` | `parseSitemapXml()` 检测 `<sitemapindex>` 提取 `<sitemap><loc>` 返回 `{ isIndex: true, sitemaps }`；discovery 层迭代 fetch + `Set` 去重合并 | `parseSitemapXml` `cli.mjs:656-671`；`runCrawlSitemapDiscovery` index 分支 `cli.mjs:4067-4126`（`allUrls.push` @4107，`[...new Set(allUrls)]` 去重）；单元测试：`parseSitemapXml sitemapindex returns isIndex+sitemaps`、`runCrawlSitemapDiscovery iterates sub-sitemaps instead of handoff for index` |
| `sitemap-index-partial-failure-resilience` | 单子 sitemap 失败 → warning+caveat 继续；全失败 → `sitemap_all_subs_failed` handoff | `subSitemapErrors.push` @4093/4099/4104；`sitemap_all_subs_failed` handoff @4112；单元测试：`runCrawlSitemapDiscovery tracks sub-sitemap partial failures` |
| `sitemap-exclude-patterns-filtering` | `discovery.exclude_patterns` 在 include 后、auto-group 前应用；空数组 no-op；全排除 → `sitemap_no_pattern_match` handoff | `excludePatterns` @4153，`finalUrls` filter @4155，`sitemap_no_pattern_match` @4168；单元测试：`matchesPagePattern exact-glob excludes references path`、`...keeps non-references path`、`...regex anchored to path`、`...DEEP multi-level references path`（T5 回归）、`runCrawlSitemapDiscovery applies exclude_patterns after page_pattern include` |

### MODIFIED Requirements

| Requirement | 验证 | 证据 |
|---|---|---|
| `strategy-discovery-block-schema` | `discovery.exclude_patterns` 字段已加入 schema 文档（writeback 回写 `03-strategy-schema.md`）；PostHog 策略 frontmatter 使用 | `sites/strategies/posthog.com/strategy.md` frontmatter `discovery.exclude_patterns`；writeback 目标 `docs/architecture/03-strategy-schema.md` |
| `sitemap-discovery-fetch-and-parse` | 同时支持 `<urlset>`（扁平）与 `<sitemapindex>`（迭代子 sitemap）；忽略 lastmod/changefreq/priority | `parseSitemapXml` `cli.mjs:656-671`；index 迭代 `cli.mjs:4080-4126` |
| `sitemap-url-filtering-by-page-pattern` | 两阶段：include（page_pattern）→ exclude（exclude_patterns）→ auto-group；events 记录两阶段过滤数 | include 阶段日志 `N URLs excluded by page_pattern`；exclude 阶段日志 `N URLs excluded by exclude_patterns`（Live T7：8907 / 3943） |
| `sitemap-index-handoff` | `<sitemapindex>` 不再 handoff，改为解析迭代（全失败除外） | 旧 `sitemap_index_unsupported` handoff 已被 index 解析分支替换 `cli.mjs:4067-4126`；单元测试：`runCrawlSitemapDiscovery iterates sub-sitemaps instead of handoff for index` |

### Scenario 命中映射（关键 scenario）

| Scenario | 命中方式 |
|---|---|
| `sitemap-index-extracts-subsitemap-urls` | 单元测试 `parseSitemapXml sitemapindex returns isIndex+sitemaps` |
| `multi-sitemap-index-merged` / `cross-sitemap-deduplication` | `[...new Set(allUrls)]` @4126（Set 首次出现保留） |
| `one-sub-sitemap-fails-others-succeed` | 单元测试 `tracks sub-sitemap partial failures`；Live：PostHog 单子 sitemap 成功，failure_rate=0 |
| `all-sub-sitemaps-fail` | `sitemap_all_subs_failed` handoff @4112 |
| `exclude-references-category` / `multiple-exclude-patterns` | Live T7：`/docs/references/**` 排除 3,943 条；单元测试 DEEP + shallow path |
| `exclude-patterns-empty-no-op` | `excludePatterns.length > 0` 守卫 @4155 |
| `all-urls-excluded` | `sitemap_no_pattern_match` handoff @4168；单元测试 `has handoff for zero pattern match` |
| `sitemap-index-resolved-not-handoff` | Live T7：result=success（PostHog 是 sitemap-index 站点） |

## Task-to-Evidence Coverage

| Task | 状态 | 证据 |
|---|---|---|
| T1 spec 覆盖确认 | ✅ | proposal/design/specs 三处对齐 |
| T2 依赖确认 | ✅ | 父 capability 23/23→现 33/33；PostHog sitemap 可访问 |
| T3 (RED→GREEN) parseSitemapXml index | ✅ | `cli.mjs:656-671`；单元测试 PASS |
| T4 (RED→GREEN) discovery index 迭代 | ✅ | `cli.mjs:4067-4126`；单元测试 PASS |
| T5 (RED→GREEN) exclude_patterns + **回归修复** | ✅ | `cli.mjs:575-605`（glob 单遍替换）、`4153-4168`；DEEP 回归测试 PASS |
| T6 PostHog 策略 + registry | ✅ | `sites/strategies/posthog.com/strategy.md`；`registry.json:241` |
| T7 Discovery-only live E2E | ✅ | `outputs/20260618T133639-crawl-posthog-com-docs/`：1725 页 / 0 references / success |
| T8 小规模 extraction | ✅（断言）/ ⚠️（质量） | `outputs/20260618T133706-crawl-posthog-com-docs/`：5/5 converted，result=success；抽取质量缺口见下 |
| T9 SKILL.md 更新 + 同步 | ✅ | `skills/chrome-agent/SKILL.md:216-217`；global 已同步（diff 一致） |
| T10 单元测试 | ✅ | 33/33（sitemap）+ 44/44（全量 *.test.mjs） |
| T11 verification.md | ✅ | 本文件 |
| T11 writeback.md + 执行 | ✅ | `writeback.md` + 四个架构文档回写 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 单元测试 | `tests/sitemap-driven-crawl.test.mjs`（33 tests） | T3/T4/T5 + 全 ADDED requirements |
| 回归测试（T5 glob bug） | `matchesPagePattern exact-glob excludes DEEP multi-level references path` | sitemap-exclude-patterns-filtering |
| Live discovery 产物 | `outputs/20260618T133639-crawl-posthog-com-docs/page_manifest.json`（1725 页） | T7 / sitemap-index-resolve-and-merge + exclude |
| Live extraction 产物 | `outputs/20260618T133706-crawl-posthog-com-docs/docs/*.md`（5 文件） | T8 |
| PostHog 策略 | `sites/strategies/posthog.com/strategy.md` | T6 / strategy-discovery-block-schema |
| glob 修复 diff | `scripts/chrome-agent-cli.mjs:586-594`（单遍 `\*\*?`） | T5 回归 |
| index 解析实现 | `scripts/chrome-agent-cli.mjs:resolveSitemapIndex` (L692-718) + `runCrawlSitemapDiscovery` index 分支 (L4113-4150) | sitemap-index-resolve-and-merge + partial-failure-resilience |
| partial-failure 行为级测试 | `tests/sitemap-driven-crawl.test.mjs`（6 个 `resolveSitemapIndex:*` 行为测试，注入 fake fetcher，无网络） | sitemap-index-partial-failure-resilience（独立验证 WARNING 1 修复） |
| exclude 实现 | `scripts/chrome-agent-cli.mjs:4153-4168` | sitemap-exclude-patterns-filtering |

## 测试套件

| Suite | Result |
|---|---|
| `node --test tests/sitemap-driven-crawl.test.mjs` | ✅ **39/39 pass**（基线 21 → 父 change 23 → 本 change 39；+10 含 T5 DEEP 回归，+6 含 `resolveSitemapIndex` partial-failure 行为测试，独立验证后新增） |
| `node --test tests/chrome-agent-runtime.test.mjs` | ✅ 9/9 pass（无回归） |
| `node --test tests/crawl-scrapling-pages-scope.test.mjs` | ✅ 2/2 pass（无回归） |
| `node --check scripts/chrome-agent-cli.mjs` | ✅ pass（语法） |

## Live Verification

| 验证 | 结果 |
|---|---|
| T7 Discovery-only：result=success，manifest_path 非 null | ✅ |
| T7 sitemap index 解析：PostHog sitemap-index.xml → sitemap-0.xml | ✅ engine_path `sitemap_discovery -> discovery_only` |
| T7 page_pattern include：8,907 URLs excluded | ✅ |
| T7 exclude_patterns：3,943 `/docs/references/**` excluded | ✅（bug fix 后正确，旧 bug 仅排除 46） |
| T7 最终页数：1,725（策略预测 ~1,725） | ✅ 精确吻合 |
| T7 manifest references 数量：0 | ✅ |
| T7 discovery category：`discovery_summary.json` 仅 1 个 category `Docs`（1,725 页，所有 `/docs/*` URL 按 autoGroupSitemapUrls 首段归一类）；URL 二级目录覆盖 cdp/api/data-warehouse/experiments/feature-flags 等 | ✅ |
| T7 failure_rate：0 | ✅ |
| T8 5/5 pages converted，result=success | ✅（转换计数断言） |
| T8 抽取内容质量 | ⚠️ 见缺口项 |

## 缺口与阻塞项

| 缺口 | 级别 | 范围 | 处置 |
|---|---|---|---|
| ~~partial-failure 路径仅有结构性测试，缺行为级覆盖~~ | ~~原 WARNING~~ | ~~测试覆盖~~ | ✅ **已修复**（独立验证 WARNING 1）：提取纯函数 `resolveSitemapIndex`（L692-718）注入 fetcher，新增 6 个行为测试覆盖 one-fail/all-fail/cross-dedup/parse-error/nested-index |
| **scrapling `--ai-targeted` 抽取未捕获 `<article>` 正文** | HIGH（但 out-of-scope） | 父 capability `sitemap-driven-crawl` 抽取引擎 | 转入 follow-up change（建议 `posthog-extraction-quality`）。本 change 未修改抽取代码，discovery 维度不受影响。证据：`/docs/glossary` HTML 正文 22,246 字符 vs 输出 397 字节。 |
| PostHog sitemap `description` 称 Docusaurus（proposal/design） | INFO | 文档准确性 | tasks.md Session Handoff 已更正为 Gatsby 4.25.9；策略文件已记录正确技术栈 |

### J3 测试完备性检查

| 检查项 | 结果 |
|---|---|
| 新增代码模块无对应测试 | N/A（无新增 `.py`/`.mjs` 模块文件）；但新增函数 `resolveSitemapIndex`（独立验证后提取）已有 6 个行为级测试覆盖（one-fail/all-fail/cross-dedup/parse-error/nested-index） |
| 修改已有代码模块未更新测试 | ✅ `chrome-agent-cli.mjs` 修改点已更新测试：(1) matchesPagePattern glob 修复 → DEEP 回归测试；(2) `runCrawlSitemapDiscovery` index 分支重构为委托 `resolveSitemapIndex` → 结构性测试同步更新 + 6 个行为测试 |
| 仅修改 `.md` 文档 | ✅ 不检查（SKILL.md / 策略 / 架构文档） |

## 独立验证闭环（/opsx-verify）

本 change 经独立 subagent 运行 `/opsx-verify` 工作流（从零重新核验，不复述本 verification.md）。独立验证结论：**No CRITICAL，2 WARNING，3 SUGGESTION**。两个 WARNING 已在本 session 修复：

| 独立验证发现 | 级别 | 处置 |
|---|---|---|
| Partial-failure 仅有结构性测试，缺行为级覆盖 | WARNING | ✅ **已修复**：提取 `resolveSitemapIndex` 纯函数 + 6 个行为测试（注入 fake fetcher，无网络） |
| verification.md 对 categories 描述夸大（声称多个 category，实际仅 `Docs`） | WARNING | ✅ **已修正**：verification.md 与 tasks.md 均更正为 "discovery_summary.json 仅 1 个 category Docs；cdp/api 等是 URL 二级目录" |
| `package-lock.json` incidental 变更未声明 | SUGGESTION | ⚠️ 未处理（非本 change 引入的代码改动，归档时由 commit 审查把关） |
| `excludedByPatternsCount` 多 pattern 同匹配可能重复计数 | SUGGESTION | ⚠️ 未处理（仅影响 console 日志数字，不影响 finalUrls 结果；建议后续优化） |
| 部分失败但剩余 0 URL 走 `sitemap_no_pattern_match` 而非 `partial_success` | SUGGESTION | ⚠️ 未处理（边界语义，spec 未明确要求；建议后续在 spec 补充 scenario） |

**独立验证对关键审视点的裁决**：T5 glob 修复 agree、T7 数字自洽 agree（category 措辞已修正）、T8 out-of-scope agree、D6 sitemap_url 指向 index agree。详见 `/opsx-verify` 输出。

**最终评估**（独立验证）：No critical issues. 2 warning(s) → 均已修复. Ready for archive.
