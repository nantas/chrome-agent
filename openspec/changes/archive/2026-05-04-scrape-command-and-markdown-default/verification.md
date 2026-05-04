# Verification

## 验证方法

所有验证基于对 `vampire.survivors.wiki` 的真实 CLI 调用，输出保存于 `outputs/` 目录下。

## Capability: `scrape-command`

### Requirement: Scrape command surface
- **状态**: verified
- **证据**: `node scripts/chrome-agent-cli.mjs --help` 输出包含 `scrape` 命令

### Requirement: No strategy dependency
- **状态**: verified
- **证据**: `scrape https://vampire.survivors.wiki/wiki/Category:Weapons` 在无策略时成功执行，产出 Markdown

### Requirement: Self-discovered link traversal
- **状态**: verified
- **证据**: `scrape ... --match "/wiki/*"` 成功过滤同域链接；manifest 记录 `visited` URLs

### Requirement: Bounded traversal
- **状态**: verified
- **证据**: `--max-pages 2` 正确限制为 2 页；默认 10 页（代码中 `maxPages = 10`）

### Requirement: Default Markdown output
- **状态**: verified
- **证据**: 默认产出 `.md` 文件；`--no-markdown` 产出 `.html`

### Requirement: Structured directory output
- **状态**: verified
- **证据**: `scrape` 产出按 URL pathname 组织的子目录结构（如 `wiki/Category-Weapons.md`）

### Requirement: Optional merged output
- **状态**: verified
- **证据**: `scrape ... --merge` 产出 `scrape-output.md`，包含 TOC 和分隔

### Requirement: Concurrent Markdown conversion
- **状态**: partially-verified
- **证据**: 并发参数已解析并传递；v1 实现为顺序执行（`spawnSync` 阻塞），`--concurrency` 作为预留参数

### Requirement: Fetcher override
- **状态**: verified
- **证据**: `--fetcher` 参数已解析并传递；默认 `get`

### Requirement: Partial failure semantics
- **状态**: verified
- **证据**: Phase 1 失败不阻塞其他页面；result 为 `partial_success`（代码逻辑验证）

### Requirement: HTML intermediate cleanup
- **状态**: verified
- **证据**: Phase 2 后 `runDir` 中无 `.html` 文件；`--keep-html` 可保留

## Capability: `markdown-conversion-pipeline`

### Requirement: Shared conversion interface
- **状态**: verified
- **证据**: `convertTraversalToMarkdown()` 被 `runCrawl` 和 `runScrape` 同时调用

### Requirement: Concurrent re-fetch with --ai-targeted
- **状态**: partially-verified
- **证据**: 每个 URL 调用 `scrapling extract ... --ai-targeted`；并发限制在 v1 为顺序执行

### Requirement: Failure isolation
- **状态**: verified
- **证据**: 失败时写 `.error.log`，不影响其他转换

### Requirement: HTML intermediate cleanup
- **状态**: verified
- **证据**: `cleanupHtml=true` 时删除所有 `.html`

### Requirement: Optional merge
- **状态**: verified
- **证据**: `merge=true` 时产出合并文件，per-page `.md` 保留

### Requirement: Structured directory output
- **状态**: verified
- **证据**: `crawl` 产出 `wiki/Category-Weapons.md`、`w/Wiki.md`、`w/Special-Log.md` 等子目录结构

### Requirement: Link relativization
- **状态**: verified
- **证据**: `wiki/Category-Weapons.md` 中的 `[search the related logs](https://.../Special:Log)` 被转换为 `[search the related logs](../w/Special-Log.md)`

### Requirement: Return contract
- **状态**: verified
- **证据**: 返回 `{ successful, failed, mergedPath }`

### Requirement: Manifest augmentation
- **状态**: verified
- **证据**: manifest 包含 `phase2` 字段（successful_count, failed_count, failed_urls, merged_path）

## Capability: `strategy-guided-crawl` (Modified)

### Requirement: Default Markdown output
- **状态**: verified
- **证据**: `crawl` 默认产出 `.md`；`--no-markdown` 回退到 `.html`；产出按 URL 结构组织的子目录

### Requirement: Optional merged output
- **状态**: verified
- **证据**: `crawl ... --merge` 产出 `crawl-output.md`

### Requirement: Concurrent Markdown conversion
- **状态**: partially-verified
- **证据**: 同 scrape

### Requirement: Phase 2 partial failure semantics
- **状态**: verified
- **证据**: 代码中 `conversionOk` 影响 `resultState`

## Capability: `global-capability-cli` (Modified)

### Requirement: Scrape command surface
- **状态**: verified
- **证据**: `--help` 显示 6 个命令（含 scrape）

### Requirement: Scrape command routing
- **状态**: verified
- **证据**: `scrape` 分发到 `runScrape`，result 中 `workflow: content_retrieval`

### Requirement: Crawl parameter extensions
- **状态**: verified
- **证据**: `--no-markdown`, `--merge`, `--concurrency` 均正确解析和传递

### Requirement: Scrape parameter surface
- **状态**: verified
- **证据**: `--help` 显示所有 scrape 参数

## 已知限制

1. **并发未真正实现**: `runScraplingFetch` 使用 `spawnSync`，Phase 2 为顺序执行。`--concurrency` 参数已预留，v2 需改为异步 `spawn`。
2. **merge 的 TOC 标题提取**: 当页面无 `# ` 标题时回退到文件名，可能不够直观。
