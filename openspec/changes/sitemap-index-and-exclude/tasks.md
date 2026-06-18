# Tasks
## Session Handoff (2026-06-18, ~4h)

### Completed
- **T1–T6**: Fully implemented (T1-T2 confirmation, T3-T5 TDD RED→GREEN, T6
  PostHog strategy + registry).
- Unit tests: **32/32 pass** (baseline was 21/21; +11 from T3/T4/T5).
- PostHog strategy created (`sites/strategies/posthog.com/strategy.md`) + registry
  entry. **Strategy uses sitemap INDEX URL** (design D6 sanctioned) so the new
  index-resolution capability is exercised end-to-end.
- Strategy `sitemap_url`:
  `"https://posthog.com/sitemap/sitemap-index.xml"` (NOT sitemap-0.xml — task
  text said child, but index is the point of the change; D6 allows either).
- Page include pattern: `"regex:^https://posthog\\.com/docs(/.*)?$"` (catches
  `/docs` landing AND all subpaths).

### Critical Bug Found in T5 (matchesPagePattern — exclude)
T7 discovery-only ran successfully (result: success, manifest at
`outputs/20260618T094540-crawl-posthog-com-docs/`) but only **46** of ~3,943
references were excluded. The manifest still contains 3,897 reference URLs.

**Root cause** (verified in terminal — see compiled output):
The glob→regex conversion in `matchesPagePattern()` has a **double-replacement
bug**. The two `.replace()` calls run sequentially:

  1. `.replace(/\*\*/g, ".*")` converts `**` → `.*`
  2. `.replace(/\*/g, "[^/]*")` then re-matches the `*` inside `.*`,
     producing `.[^/]*` instead of `.*`

For pattern `exact:/docs/references/**`, the compiled regex is:
  `^/docs/references/.[^/]*$`  ← BUG: only matches single-segment after references.
Should be:
  `^/docs/references/.*$`      ← matches any depth.

This passed unit tests because the tests only exercised single-level paths
(e.g., `/docs/references/posthog-js`) where `.[^/]*` still happens to match.

**Exact fix** (one-line change in `scripts/chrome-agent-cli.mjs`, ~line 586):
```js
// BEFORE (buggy):
.replace(/\*\*/g, ".*")
.replace(/\*/g, "[^/]*")
// AFTER (correct — single-pass):
.replace(/\*\*?/g, (m) => m.length === 2 ? ".*" : "[^/]*")
```

Also **add** a multi-level test to `tests/sitemap-driven-crawl.test.mjs`:
```js
test("matchesPagePattern exact-glob excludes deep references path", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("exact:/docs/references/**"),
    JSON.stringify("https://posthog.com/docs/references/posthog-js/types/ActionStepType")
  ]);
  assert.strictEqual(r, true);
});
```

### Factual Correction
PostHog is **Gatsby 4.25.9**, NOT Docusaurus (proposal/design incorrectly
assumed Docusaurus). Does not affect code — both are SSG, scrapling-get
works. The strategy file documents Gatsby.

### Sitemap Data (for verification)
| Metric | Value |
|--------|-------|
| sitemap-index.xml | 1 child (sitemap-0.xml) |
| sitemap-0.xml total `<loc>` | 14,576 |
| /docs URLs (after include) | ~5,668 |
| /docs/references/** | ~3,943 |
| Expected final after fix | ~1,725 |

### Next Session: /opsx-apply sitemap-index-and-exclude

1. **Apply T5 bug-fix** (matchesPagePattern glob double-replacement — see above),
   add the multi-level exclude test, run `node --test
   tests/sitemap-driven-crawl.test.mjs` → expect 33/33.
2. **Re-run T7**: `chrome-agent crawl https://posthog.com/docs --discovery-only
   --format json` → expect "~3943 URLs excluded by exclude_patterns", final
   pages ~1,725, categories include CDP/API/data-warehouse/, and NO references
   in manifest.
3. **T8**: Small extraction (`--from-manifest <manifest> --max-pages 5 --yes`).
4. **T9**: Update `skills/chrome-agent/SKILL.md` + sync to
   `~/.agents/skills/chrome-agent/SKILL.md` (remove "not yet supported"
   sitemap-index line at ~line 216).
5. **T10**: Full test run (expect 33+).
6. **T11**: Generate verification.md + writeback.md + execute writeback targets.


## 依赖图

```
T1 ── T2 ── T3 ── T4 ── T5 ── T6 (site strategy)
                                    │
T7 ── T8 (live E2E)                 │
                                    │
T9 (skill update) ── T10 ── T11 (verification + writeback)
```

## 1. Spec 覆盖与实现准备

- [x] **T1** 确认 spec delta 覆盖范围：`sitemap-index-resolve-and-merge` + `sitemap-index-partial-failure-resilience` + `sitemap-exclude-patterns-filtering` + 3 MODIFIED requirements
- [x] **T2** 确认依赖：`sitemap-driven-crawl` 基础管线已实现且 23/23 测试通过；PostHog sitemap 已确认可访问

## 2. 核心实现任务

### Sitemap Index 解析 (parseSitemapXml)

- [x] **T3** (RED) 测试：`parseSitemapXml` 返回值含 `sitemaps` 数组、含 index 含多子 sitemap、扁平 urlset 不含 sitemaps 字段
- [x] **T3** (GREEN) 实现：`parseSitemapXml()` 检测 `<sitemapindex>` 时提取所有 `<sitemap><loc>`，返回 `{ isIndex: true, sitemaps: [...] }`
  - 文件：`scripts/chrome-agent-cli.mjs` ~line 611
  - 提取逻辑：`/<loc>(?:<!\[CDATA\[)?([^<]*?)(?:\]\]>)?<\/loc>/gi`（复用现有 locRegex）
  - 输入 `<sitemapindex><sitemap><loc>https://.../sitemap-0.xml</loc></sitemap></sitemapindex>` → `{ isIndex: true, sitemaps: ["https://.../sitemap-0.xml"] }`

### Sitemap Index 迭代与合并 (runCrawlSitemapDiscovery)

- [x] **T4** (RED) 测试：`runCrawlSitemapDiscovery` index 路径的结构性测试——curl call 检测、sitemaps 迭代、Set 去重、merge 后走 filter+group
- [x] **T4** (GREEN) 实现：`runCrawlSitemapDiscovery()` 中 `parsed.isIndex` 分支改为迭代子 sitemap
  - 文件：`scripts/chrome-agent-cli.mjs` ~line 4007（替换现有 sitemap_index_unsupported handoff）
  - 循环：`for (const subUrl of parsed.sitemaps)` → curl fetch → parse → `allUrls.push(...result.urls)`
  - 去重：`const dedupedUrls = [...new Set(allUrls)]`
  - 合并后继续走 page_pattern filter → exclude_patterns filter → autoGroupSitemapUrls
  - 部分失败：记录 `subSitemapErrors` 数组 → push 到 warnings + caveats
  - 全部失败：handoff `sitemap_all_subs_failed`

### Exclude Patterns 过滤

- [x] **T5** (RED) 测试：`pagePatternMatches` 或新增 `matchesExcludePattern` 函数——exclude pattern 匹配测试；exclude_patterns 在 discovery 中的解析测试
- [x] **T5** (GREEN) 实现：在 `runCrawlSitemapDiscovery` 的 page_pattern include 过滤后插入 exclude 过滤步骤
  - 文件：`scripts/chrome-agent-cli.mjs` ~line 4018-4025
  - 新增 `const excludePatterns = doc?.discovery?.exclude_patterns ?? []`
  - 过滤：`matchedUrls.filter(url => !excludePatterns.some(p => matchesPagePattern(p, url)))`
  - 确保 `matchesPagePattern` 可复用（与 page_pattern 相同语法）
  - 排除后 0 URL → handoff `sitemap_no_pattern_match`

### PostHog 站点策略

- [ ] **T6** 创建 `sites/strategies/posthog.com/strategy.md`
  - `discovery: { method: sitemap, sitemap_url: "https://posthog.com/sitemap/sitemap-0.xml", exclude_patterns: ["exact:/docs/references/**"] }`
  - `pages` 含 `page_pattern: ["regex:^https://posthog\\.com/docs/.*"]`
  - `extraction` 块使用 Scrapling `--ai-targeted` 模式
  - `protection_level: low`
- [ ] **T6** 更新 `sites/strategies/registry.json` 注册 posthog.com

### Live E2E 验证

- [ ] **T7** Discovery-only：`chrome-agent crawl https://posthog.com/docs --discovery-only --format json`
  - 断言：`result: success`，`manifest_path` 非 null，categories 含 CDP/API/data-warehouse 等，不含 references
- [ ] **T8** 小规模 extraction：`chrome-agent crawl https://posthog.com/docs --from-manifest <manifest> --max-pages 5 --yes --format json`
  - 断言：5/5 pages converted to Markdown，`result: success`

## 3. 收敛与验证准备

- [ ] **T9** 更新 `skills/chrome-agent/SKILL.md` + 同步 `~/.agents/skills/chrome-agent/SKILL.md`
  - Crawl Confirmation Gate Stage 2：sitemap index 已支持，移除 "not yet supported" 限制描述
  - 标记 sitemap index 为已就绪（此前为 deferred 限制）
- [ ] **T10** 单元测试完整运行：`node --test tests/sitemap-driven-crawl.test.mjs`（已有测试 + T3/T4/T5 新增）

## 4. 验证与回写收敛

- [ ] **T11** 生成 `verification.md`：综合 T7 live E2E + T10 单元测试结果 + spec-to-implementation mapping
- [ ] **T11** 生成 `writeback.md` 并执行架构文档回写：
  - `docs/architecture/03-strategy-schema.md`：`exclude_patterns` 字段文档
  - `docs/architecture/02-pipeline-flow.md`：sitemap index 解析路径
  - `docs/architecture/06-engine-selection.md`：sitemap index 决策分支
  - `skills/chrome-agent/SKILL.md` + global sync（T9 已完成，此处确认）
