# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/scrape-command/spec.md` 的实现范围：新命令入口、参数解析、遍历逻辑、输出格式
- [x] 1.2 确认 `specs/markdown-conversion-pipeline/spec.md` 的实现范围：共享函数接口、并发控制、失败隔离、merge、HTML 清理
- [x] 1.3 确认 `specs/strategy-guided-crawl/spec.md` delta 的实现范围：crawl 默认 Markdown、新增参数 `--no-markdown` / `--merge` / `--concurrency`
- [x] 1.4 确认 `specs/global-capability-cli/spec.md` delta 的实现范围：命令面新增 `scrape`、参数面扩展
- [x] 1.5 确认前置条件：Scrapling CLI preflight 已可用（`runScraplingPreflight` 已存在，无需修改）

## 2. 核心实现任务

### 2.1 共享 Markdown 转换管线

- [x] 2.1.1 在 `scripts/chrome-agent-cli.mjs` 中新增 `convertTraversalToMarkdown(options)` 函数
  - 输入：`{ repoRoot, runDir, manifest, fetcherFn, concurrency, merge, cleanupHtml, outputName }`
  - 输出：`{ successful, failed, mergedPath }`
  - 实现并发池：维护 `pending` promises 数组，达到 `concurrency` 上限时 `await Promise.race(pending)`
  - 对每个 URL 调用 `runScraplingFetch(repoRoot, fetcherFn(url), url, mdPath, ['--ai-targeted'])`
  - 失败时写 `.error.log`，不影响其他任务
  - **验证**：单元测试用 mock `runScraplingFetch` 验证并发限制、失败隔离、返回值结构

- [x] 2.1.2 在 `convertTraversalToMarkdown` 中实现 `mergeMarkdownFiles` 子逻辑
  - 读取所有成功 `.md` 文件，按文件名排序（`01.md`, `02.md`...）
  - 提取每个文件的第一个 `# ` 行作为 TOC 条目
  - 生成 `#{outputName}.md`，格式：
    ```markdown
    # Scrape Output: <target>

    ## Table of Contents
    - [Page Title 1](#page-title-1)
    - [Page Title 2](#page-title-2)

    ---

    ## Page Title 1
    ...content...

    ---

    ## Page Title 2
    ...content...
    ```
  - **验证**：检查 merge 输出包含正确数量的 `##` 分隔和 TOC 链接

- [x] 2.1.3 在 `convertTraversalToMarkdown` 中实现 HTML 清理
  - `cleanupHtml = true` 时，遍历 `runDir` 下所有 `.html` 文件并 `fs.unlinkSync`
  - **验证**：Phase 2 完成后 `runDir` 中无 `.html` 文件

### 2.2 CLI 参数解析扩展

- [x] 2.2.1 在 `parseArgs` 函数中新增参数解析
  - `scrape` 命令识别
  - `--no-same-domain`（布尔，默认 false，即 same-domain 开启）
  - `--match <glob>`
  - `--no-markdown`（布尔，默认 false）
  - `--merge`（布尔，默认 false）
  - `--concurrency <n>`（整数，默认 5）
  - `--fetcher <name>`（字符串，默认 'get'）
  - `--keep-html`（布尔，默认 false）
  - `--entry-point` 已存在，保持
  - `--max-pages` 已存在，保持
  - **验证**：`chrome-agent --help` 显示所有新参数

### 2.3 `scrape` 命令实现

- [x] 2.3.1 新增 `runScrape(repoRoot, repoRef, resolutionMode, targetUrl, opts)` 函数
  - Phase 1：BFS 遍历
    - `queue = [targetUrl]`，`visited = Set()`
    - 循环条件：`queue.length > 0 && visited.size < maxPages`
    - 每次迭代：
      - `scrapling extract <fetcher> <url> <runDir>/<NN>.html`（无 `--ai-targeted`）
      - 提取所有 `<a href="...">`（正则 `/^<a\s[^>]*href="([^"#]+)"/gi`）
      - 转为绝对 URL：`new URL(href, baseUrl)`
      - same-domain 过滤：`url.hostname === baseHostname`
      - glob 过滤：`--match` 时 `micromatch.isMatch(url.pathname, matchPattern)`（或简单 `minimatch` 实现）
      - dedup：跳过已访问/已排队
      - 写入 manifest
  - Phase 2：调用 `convertTraversalToMarkdown`
  - 返回 `makeResult` 结果
  - **验证**：对已知 wiki 运行 `scrape --max-pages 10 --match "/wiki/*"`，检查产出 10 个 `.md` 文件

- [x] 2.3.2 在 CLI dispatch 中新增 `scrape` case
  - `if (command === 'scrape') return runScrape(...)`
  - **验证**：`chrome-agent scrape <url>` 能正确分发

### 2.4 `crawl` 命令改造

- [x] 2.4.1 修改 `runCrawl` 函数，在遍历完成后调用 `convertTraversalToMarkdown`
  - 默认 `markdown = true`（除非 `--no-markdown`）
  - 传递 `merge`、`concurrency` 参数
  - `fetcherFn` 使用现有的 `selectFetcher(strategy, findMatchingPage(...))`
  - 更新结果摘要：包含 Phase 2 成功/失败数量
  - **验证**：`chrome-agent crawl <url>`（有策略时）产出 `.md` 文件而非 `.html`

- [x] 2.4.2 修改 `runCrawl` 的 artifact 列表
  - `--markdown` 模式下：artifacts 只列 `.md` 和 `manifest.json`
  - `--no-markdown` 模式下：保持原有行为，列 `.html`
  - **验证**：检查 JSON result 的 `artifacts` 数组

- [x] 2.4.3 修改 `buildCrawlReport`，在报告中体现 Phase 2 结果
  - 新增 "Phase 2: Markdown Conversion" 小节
  - 列出成功/失败数量
  - **验证**：`--report` 产出的 report 包含 Phase 2 统计

### 2.5 Help 文本与文档

- [x] 2.5.1 更新 `printHelp` 函数
  - 新增 `scrape` 命令描述
  - 新增 `scrape` 参数列表
  - 更新 `crawl` 参数列表（新增 `--no-markdown`, `--merge`, `--concurrency`）
  - **验证**：`chrome-agent --help` 输出完整且格式正确

## 3. 收敛与验证准备

- [x] 3.1 为 `scrape` 编写 smoke test：对 `vampire.survivors.wiki` 的 category 页面执行 `--max-pages 5 --match "/wiki/*" --markdown`
  - 验证产出 5 个 `.md` 文件
  - 验证无 `.html` 残留
  - 验证 manifest 包含 5 个 visited URL

- [x] 3.2 为 `crawl` 编写 regression test：对已有策略的站点执行 crawl
  - 验证默认产出 `.md` 文件
  - 验证 `--no-markdown` 产出 `.html`
  - 验证 `--merge` 产出 `crawl-output.md`

- [x] 3.3 并发测试：使用 `--concurrency 10` 抓取 20 页
  - 验证实际并发不超过 10
  - 验证总耗时显著低于串行

- [x] 3.4 失败隔离测试：构造一个会返回 404 的 URL 混入队列
  - 验证 404 页面不影响其他页面转换
  - 验证 manifest 记录失败 URL
  - 验证最终 result 为 `partial_success`

## 4. 验证与回写收敛

- [x] 4.1 基于真实测试结果生成 `verification.md`
  - 列出每个 spec requirement 的验证证据（测试命令、输出路径、结果截图）
  - 标记所有 requirement 为 verified / partially-verified / not-verified

- [x] 4.2 基于 verification 结论生成 `writeback.md`
  - 明确回写目标文件列表
  - 明确每个文件的变更内容摘要
  - 记录执行人、时间、结果

- [x] 4.3

## 5. 补充需求：结构化 Markdown 输出

### 5.1 Spec 补充
- [x] 5.1.1 在 `specs/markdown-conversion-pipeline/spec.md` 中补充结构化输出要求
- [x] 5.1.2 在 `specs/scrape-command/spec.md` 中补充结构化输出要求

### 5.2 实现
- [x] 5.2.1 新增 `urlToStructuredPath(url, runDir)` 函数：URL pathname → 子目录文件路径
- [x] 5.2.2 修改 `convertTraversalToMarkdown`：使用结构化路径替代数字编号
- [x] 5.2.3 新增 `relativizeMarkdownLinks(content, mdPath, urlToPath)` 函数：绝对链接转相对路径
- [x] 5.2.4 在 `convertTraversalToMarkdown` 中调用链接相对化（Phase 2 后处理）
- [x] 5.2.5 修改 artifact 收集逻辑（递归查找子目录中的 .md 文件）
- [x] 5.2.6 更新 `mergeMarkdownFiles` 支持结构化路径

### 5.3 验证
- [x] 5.3.1 scrape 测试：验证子目录结构和相对链接
- [x] 5.3.2 crawl 测试：验证子目录结构和相对链接
- [x] 5.3.3 merge 测试：验证结构化路径下 merge 仍正常工作 执行回写
  - 更新 `AGENTS.md` §2 能力框架表格（新增 `scrape`，更新 `crawl` 描述）
  - 冻结并回写 `openspec/specs/global-capability-cli/spec.md`
  - 冻结并回写 `openspec/specs/strategy-guided-crawl/spec.md`
  - 新增并冻结 `openspec/specs/scrape-command/spec.md`
  - 新增并冻结 `openspec/specs/markdown-conversion-pipeline/spec.md`
  - 归档本 change 到 `openspec/changes/archive/`
