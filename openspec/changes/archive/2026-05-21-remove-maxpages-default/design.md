# Design

## Context

`chrome-agent-cli.mjs` 中 `maxPages` 参数在四个函数（`runCrawl`、`runCrawlMediawikiApi`、`runCrawlScrapling`、`runScrape`）里被硬编码为默认值 3 或 10。Python pipeline 端已正确支持 `null` = 不限制语义，但 JS 端三层默认值堵死了这一路径。

## Goals / Non-Goals

**Goals:**
- 移除所有 JS 层 `maxPages` 硬编码默认值，统一 `null` = 不限制
- 修正所有使用 `maxPages` 的条件判断以正确处理 `null`
- 保持 CLI `--max-pages N` 传入正整数时行为不变

**Non-Goals:**
- 不修改 Python pipeline 代码（已正确）
- 不新增 `--max-pages=unlimited` 等新 CLI 语法
- 不给 Scrapling 路径加安全上限（可后续独立处理）
- 不修改 `parseArgs()` 解析逻辑

## Decisions

### D1: 解构默认值统一改为 null

**Decision**: 所有 `maxPages = 3` / `maxPages = 10` 解构默认值改为 `maxPages = null`。

**Rationale**: 与 Python 端 `default=None` 对齐，null 作为"不限制"的唯一哨兵值。

涉及位置：
- L1979 `runCrawl()`: `maxPages = 3` → `maxPages = null`
- L2071 `runCrawlMediawikiApi()`: `maxPages = 3` → `maxPages = null`
- L2315 `runCrawlScrapling()`: `maxPages = 3` → `maxPages = null`
- L2753 `runScrape()`: `maxPages = 10` → `maxPages = null`

### D2: main() 调用透传 parsed.maxPages

**Decision**: `main()` 中 `parsed.maxPages ?? 3` 和 `parsed.maxPages ?? 10` 改为直接 `parsed.maxPages`。

**Rationale**: 默认值不应在调用点填充，应由函数签名表达。CLI 不传 `--max-pages` 时 `parsed.maxPages` 为 `null`，透传后自然为"不限制"。

涉及位置：
- L3717: `parsed.maxPages ?? 3` → `parsed.maxPages`
- L3739: `parsed.maxPages ?? 10` → `parsed.maxPages`

### D3: 条件判断改为显式 null 检查

**Decision**:
- `if (maxPages)` → `if (maxPages != null)`（spawnSync 传参，L2118）
- `visited.size < maxPages` → `(maxPages == null || visited.size < maxPages)`（while 循环 L2392、L2812）
- `queue.length + visited.size < maxPages` → `(maxPages == null || queue.length + visited.size < maxPages)`（分页入队 L2444、L2448）

**Rationale**: `if (maxPages)` 在 `maxPages = 0` 时为 falsy，语义不明确。显式 `!= null` 避免歧义。while 条件中 `null` 表示不限制，用短路求值。

## Risks / Migration

- **CLI 行为变更**：不传 `--max-pages` 的 `crawl` 从"最多 3 页"变为"不限制"。默认 3 没有合理依据，此变更属于修正而非退化。
- **Scrapling 长时间运行**：无限制时 BFS 可能持续较久，但不会无限循环（网络终止 + 无新链接终止）。用户可用 `--max-pages` 显式限制。
- **manifest 元数据**：`max_pages: null` 在 JSON 输出中。`null` 语义明确（不限制），无需特殊处理。
