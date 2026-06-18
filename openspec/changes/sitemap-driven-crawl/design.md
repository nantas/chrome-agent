# Design

## Context

本 change 解决 `chrome-agent crawl` 对非 MediaWiki 静态文档站的可用性问题。触发源：GameAnalytics 官方文档站（Docusaurus v3.10.1，193 页，sitemap.xml 完整暴露）执行 crawl 崩溃。根因分两层：

1. `runCrawlScrapling()` 的 `pages` 作用域 bug（ReferenceError）→ 所有非 MediaWiki crawl 路径不可用
2. 无 sitemap 驱动能力 → 即使修了 bug，sitemap-driven 静态站也无法高效 crawl

设计核心：新增 `discovery` 策略块 + sitemap 路由分支，对齐 MediaWiki path 的 discovery → confirmation → extraction 三阶段契约，使 skill Confirmation Gate 对 scrapling 路径可用。

## Goals / Non-Goals

**Goals:**

1. 修复 `runCrawlScrapling` 的 `pages` 绑定 → 非 MediaWiki selector BFS 路径不再崩溃
2. `discovery.method: sitemap` 使静态文档站可通过 sitemap.xml 确定性发现 URL
3. 自动 URL path 分组 → 生成 discovery tree，使 Confirmation Gate 可用
4. 线性 extraction（无 BFS 扩散）→ sitemap 覆盖全面，不需要扩散
5. `page_manifest.json` + `discovery_summary.json` 契约对齐 MediaWiki path → skill 层零改动
6. sitemap 失败走 handoff（无 fallback）→ 策略配置错误不掩盖

**Non-Goals:**

- Sitemap index 嵌套解析（`<sitemapindex>`）
- Selector BFS fallback on sitemap failure
- 新 discovery 方法（`recursive_bfs`、`robots_txt`）
- `api:` 块删除（只删 GameAnalytics 策略的 `api`，不改 schema 规范）
- JS 运行时异常 handoff 发射（L1 路径仍可能产生裸 exception）

## Decisions

### D1: 顶层 `discovery` 块 vs `structure.discovery`

**选**：顶层 `discovery: { method, sitemap_url }`。

理由：与 `api`/`structure`/`extraction` 平级，语义互斥（`api` vs `discovery`）。`structure.pages` 是静态页面类型 schema，`discovery` 是动态 URL 发现策略——关注点分离。未来可扩展 `discovery.method` 值为 `recursive_bfs` / `first_level_links` 等。

### D2: 新函数 `runCrawlSitemapDiscovery` + `runCrawlSitemapExtraction` vs 扩展 `runCrawlScrapling`

**选**：新建两个独立函数。

理由：`runCrawlScrapling` 已 380 行，内部混合 BFS 扩散、pagination、phase fetch/convert、obscura parallel。sitemap 路径逻辑完全不同（线性遍历、不走 BFS、不用 pagination），混入会增加分支复杂度。新函数 ~80+80 行，复用 `selectFetcher` / `runEngineFetch` / `convertTraversalToMarkdown` 等共享工具。

### D3: `discovery_summary.json` JS 生成 vs 调 Python `build_discovery_summary()`

**选**：JS 生成（`buildSitemapDiscoverySummary()` ~60 行）。

理由：逻辑极简（按 `target_directory` 分组 → 计数 → 取样 → 拼 category）。Python 函数含大量 MediaWiki 专属逻辑（`source_categories`、`mw_categories`、`homepage.categories` 配置），sitemap 路径用不上。JS 实现避免 Python 3.9 兼容性、spawnSync 开销和跨进程依赖。

### D4: `sitemap_url` 默认值 vs 必填

**选**：默认 `https://<domain>/sitemap.xml`，可选覆盖。

理由：几乎每个 SSG（Docusaurus/Hugo/MkDocs/VitePress）的 sitemap 都在此位置。策略简化到 `discovery: { method: sitemap }` 两行。覆盖字段 `discovery.sitemap_url` 处理非标准位置（WordPress `/sitemap_index.xml` 等）。

### D5: Error → handoff（无 fallback）

**选**：sitemap 404 / parse error / 0 match → handoff → Gate 停止。

理由：用户写 `discovery.method: sitemap` 声明了"此站有 sitemap"。sitemap 不存在 = **策略配置错误**，不应静默 fallback 到 BFS（会掩盖配置问题）。handoff 给出明确 remediation（检查 URL、显式指定路径）。

### D6: `page_manifest.json` 格式

**选**：简化版（`url` + `title` + `target_directory` + `target_filename` + `assigned_category` + `page_type`），不含 MediaWiki 专属字段（`mw_categories`、`source_categories`、`assignment_method`、`is_list_page`）。

理由：sitemap 无 MediaWiki 分类体系，这些字段在 sitemap 路径下无意义。`page_manifest.json` 主要用途：(1) auto-group 结果持久化，(2) extraction 时作为 URL 种子队列，(3) skill Confirmation Gate 通过 `manifest_path` 引用。

### D7: Extraction 串行 vs 并行

**选**：复用 `convertTraversalToMarkdown`（串行），`parallel`/`workers` opts 预留但不在 v1 激活。

理由：`convertTraversalToMarkdown` 已稳定（含 relativize links、cleanup、merge），v1 串行是最小风险方案。开发约束 C3（`-m` 调用方式）、C4（引擎版本同步）表明增加并行复杂度（obscura pool）应单独评估。193 页 @ 5s/page ≈ 16 min，可接受。

## Risks / Migration

### Risk 1: GameAnalytics 策略 frontmatter 破坏现有引用

- **Risk**：删除 `api:` 块 → 如果其他代码分支（非 crawl 路径）依赖 `api.base_url`，可能出错
- **Mitigation**：grep 全仓库确认 `api.base_url` / `api.platform` / `api.capabilities` 仅在 `runCrawl` / `selectFetcher` / `findStrategy` 中使用，无其他消费者
- **Migration**：策略 frontmatter 变更与代码变更在同 change 内原子提交

### Risk 2: 非 MediaWiki 现有策略（x.com / fanbox.cc / leagueofgamemakers / boardgamegeek / wiki.supercombo.gg）无 `discovery` 块

- **Risk**：这些策略无 `discovery` 块 → `doc.discovery` 为 undefined → sitemap 分支不触发 → 仍走 `runCrawlScrapling`（L1 已修复）→ 行为不变
- **Mitigation**：回归测试（Modification Requirement 的 live smoke）确认 selector BFS 路径不受影响

### Risk 3: `discovery_summary.json` schema 与 skill 消费端不一致

- **Risk**：sitemap 路径的 `discovery_summary.json` 可能缺少 skill 期望的字段，导致 Confirmation Gate Stage 2 渲染失败
- **Mitigation**：实现时对照以下已确认 schema 字段：`discovery_method`, `site_title`, `domain`, `categories[]` (name/directory/type/is_index_page/page_count/sample_pages/page_type), `excluded[]`, `unclassified`, `total_pages`, `estimated_time_minutes`, `manifest_path`, `warnings`, `caveats`, `failure_rate`

### Risk 4: sitemap XML parser 边缘案例

- **Risk**：非标准 sitemap（命名空间前缀、CDATA、HTML 实体）可能导致 parse 失败
- **Mitigation**：使用宽松 XML 解析（Node.js 内置或最小依赖），对 `<loc>` 内容做 whitespace trim + URL validation；无效 URL 跳过并记录 events

### Risk 5: 大端口 site extraction 时间过长 + 无进度

- **Risk**：193 页串行约 16 min，终端无实时进度
- **Mitigation**：`events` 数组已记录每页 fetch/conversion 结果，manifest 写入 `phase2` 统计。v1 不追加实时进度；后续 change 可加进度条
