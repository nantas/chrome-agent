# Design

## Context

当前 `chrome-agent crawl` 的 MediaWiki API 管线和 Scrapling 管线都将内容获取和 Markdown 转换耦合在单一操作中。以 binding of isaac wiki（1769 页，~11 小时全量爬取）为例，每次调整 extraction 规则都需要重跑全量 API 请求。

本次 change 将 fetch 和 convert 拆分为独立 phase，引入持久化文件缓存层，使 convert 可无限次重复执行而无需网络请求。

## Goals / Non-Goals

**Goals:**
- 拆分 fetch/convert 为独立 `--phase` 选项，支持独立执行
- 持久化缓存层按 `<platform>/<domain>/` 组织，跨 session 复用
- MediaWiki API 路径和 Scrapling 路径统一 CLI 语义
- 修复 `extraction_results.json` 不保存原始内容的 bug
- 验证采用 ~10 页面规模，覆盖 entity_page / list_page / disambiguation 类型

**Non-Goals:**
- 不引入缓存过期/失效策略（v1 仅 `--re-fetch` 手动刷新）
- 不改变 discovery phase、assembly phase 内部逻辑
- 不引入增量 discovery 逻辑
- 不改变 strategy 文件 schema

## Decisions

### 1. 缓存存储：文件系统 JSON + HTML

**决策**：使用文件系统直接存储，不引入 SQLite 或其他数据库。

**理由**：
- 每页面一个独立文件，便于调试和手动检查
- JSON（MediaWiki API）和 HTML+meta.json（Scrapling）格式，人类可读
- 文件存在性 = 缓存命中判断，零开销
- 无需额外依赖

**替代方案**：SQLite 单文件数据库——更适合结构化查询，但增加依赖、降低可调试性，对当前 <2000 页的规模不具备优势。

### 2. 缓存路径推导：直接从 strategy 配置读取

**决策**：platform 值直接从 `api.platform` 字段读取，无映射表。

```
platform = strategy.api?.platform ?? "scrapling"
cache_root = .cache/<platform>/<domain>/
```

**理由**：用户要求"减少需要映射转换的逻辑"。未来新增 CMS 平台只需在 strategy 中声明 `api.platform: "wordpress"`，缓存路径自动适配。

### 3. convert phase 强制要求 --from-manifest

**决策**：`--phase convert` 必须提供 `--from-manifest`，缓存中不存储 manifest 快照。

**理由**：用户选择了 Option B——显式传入 manifest 比隐式读取缓存中的 manifest_snapshot 更安全，避免 convert 使用过期目录分配信息。

### 4. Phase B 函数拆分而不重写

**决策**：从 `process_single_page()` 中提取 `fetch_single_page()` 和 `convert_single_page()`，保留原函数作为包装。不重写 converter 内部逻辑。

**理由**：最小化变更范围。converter（`HtmlToMarkdownConverter`、`convert_wikitext_to_markdown`）行为不变，仅改变它们的调用时机和输入来源。

### 5. Scrapling 路径 cache 实现位置

**决策**：Scrapling 路径的缓存读写逻辑在 Node.js CLI 层（`chrome-agent-cli.mjs`）实现，不与 Python 管线共享代码。

**理由**：两条路径的技术栈不同（Node.js vs Python）。通过统一的目录结构和 CLI 语义保持一致性，避免跨语言模块依赖。

### 6. fetch phase 的缓存放置在 Python pipeline 层

**决策**：MediaWiki API 路径的缓存写入在 Python pipeline 的 `fetch_single_page()` 函数中完成，而非 JS CLI 层。

**理由**：Python pipeline 已拥有 `ApiClient`、`RateLimitConfig`、`ContentAcquisitionStrategy` 等全部上下文。JS CLI 层仅负责路由和参数传递。

### 7. --phase all 默认行为保持

**决策**：`--phase all` 保持全流程默认行为（discover → fetch → convert），fetch 阶段利用缓存跳过已有页面。

**理由**：`all` 是最常用的入口，用户不应被强制要求手动分步。缓存 skip 逻辑使其对重复执行友好。

## Risks / Migration

### 风险 1：缓存与 extraction 配置不一致

**场景**：用户先 fetch（策略 `content_acquisition: "html_rendered"`），后改策略为 `"wikitext_only"`，再 convert。

**缓解**：convert 阶段检查缓存的 `content_acquisition` 字段与当前策略是否一致；不一致时输出 warning：`"Cached content was fetched with 'html_rendered' but strategy now uses 'wikitext_only' — conversion may be incomplete. Use --re-fetch to refresh."`

### 风险 2：Scrapling 路径 `--phase fetch` 与 `--no-markdown` 行为重叠

**描述**：`--no-markdown` 和 `--phase fetch` 都跳过 Markdown 转换，但前者保存 HTML 到 runDir，后者保存到缓存。

**缓解**：`--no-markdown` 逐步弃用（输出 warning 引导用户使用 `--phase fetch`），但不阻断现有工作流。v2 考虑移除。

### 风险 3：已有 `outputs/` cleanup 策略不清除缓存

**描述**：`outputs/` 有 cleanup scope（`disposable` / `all`），但 `.cache/` 不受 cleanup 影响。

**缓解**：`.cache/` 独立于 `outputs/`，不受 `--scope` 清理。用户需手动管理缓存（`.cache/` 大小通过 `--re-fetch` 刷新个别页面）。

### Migration

**对现有用户**：
- `--phase extract` / `A` / `B` / `C` / `homepage` 替换为 `fetch` / `convert` / `assemble` / `--discovery homepage`
- `--phase all` 语义不变，但 fetch 阶段新增缓存跳过行为（透明优化）
- `--keep-html` 弃用，引导使用 `--phase fetch`

**对 strategy 文件**：无 schema 变更，向后兼容。
