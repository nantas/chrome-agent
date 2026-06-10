# Design

## Context

chrome-agent 的 Pipeline 目前专为 MediaWiki API 站点设计——Fetch 阶段通过 `ApiClient` 获取 wikitext/HTML，Convert 阶段通过 wikitext 模板引擎转换。chrome-cdp 引擎需要一条并行的"浏览器辅助提取"路径，但不应重复造轮：缓存层（`cache.py`）、链接修复、输出装配应复用现有基础设施。

本次 change 是 Nintendo Developer Portal 爬取任务的复盘产物，将实战中验证过的通用能力从 `/tmp` 脚本提升为仓库正式资产。

## Goals / Non-Goals

**Goals:**
- 让 chrome-cdp 引擎的页面产出可持久化、可跨 session 复用（`.cache/` 接入）
- 将 HTML→MD 转换、链接修复、图片下载提升为可复用的 Pipeline phase 或共享库
- 修复 explore scaffold 覆盖手动策略的 bug（已在本次 change 中完成代码修复）
- 保持与现有 `cache.py` 接口的完全兼容，不修改其源码

**Non-Goals:**
- 不新建站点专用管线（Nintendo 的 `contents/` URL 模式属于 strategy.md frontmatter）
- 不修改 CDP 工具本身（`.agents/skills/chrome-cdp/scripts/cdp.mjs`）
- 不新增 CLI 命令——复用现有 `fetch` / `explore` / `convert` 入口
- 不改变 MediaWiki 管线的现有行为

## Decisions

### D1: CDP 缓存直接复用 `cache.py`

**决策**: 不修改 `cache.py`。CDP fetch 阶段调用方直接使用 `save_page_cache(repo_root, "chrome-cdp", domain, raw_data)`。

**理由**: `cache.py` 的接口对 JSON 内容无 schema 校验——只要传入的 dict 包含调用方需要的字段即可。CDP 页面只需 `html`、`url`、`fetched_at` 三个字段，与 MediaWiki 缓存的字段集是并集关系。

**缓存路径示例**:
```
.cache/chrome-cdp/developer.nintendo.com/
├── Packages_Docs_Guides_Online_Play_Guide_contents_Pages_Page_239857945.json
└── Packages_Network_Guides_NX-Account_Guide_contents_Pages_Page_106359742.json
```

### D2: 新增 `fetch_cdp.py` Phase

**决策**: 在 `scripts/pipeline/pipeline/phases/` 下新增 `fetch_cdp.py`，作为 Fetch 阶段的 CDP 变体。

**职责**:
1. 从 manifest 读取页面列表
2. 对每个页面，先查 `is_cached("chrome-cdp", domain, safe_path)`，命中则跳过
3. 未命中则通过 CDP `nav` + `eval` 提取 HTML
4. 调用 `save_page_cache()` 写入缓存
5. 返回 stats（total, fetched, skipped, failed）

**不合并到 `fetch.py`**: `fetch.py` 强依赖 `ApiClient` 和 `ContentAcquisitionStrategy`（MediaWiki 特定）。CDP fetch 的输入是页面 URL 列表 + CDP tab ID，与 MediaWiki API 请求模型不兼容。保持独立文件避免耦合。

### D3: 新增 `convert_html.py` Phase

**决策**: 在 `scripts/pipeline/pipeline/phases/` 下新增 `convert_html.py`，作为 Convert 阶段的 HTML 变体。

**职责**:
1. 从 `.cache/` 读取缓存的 HTML
2. 调用 `html_to_markdown()` 转换（条件：仅当 HTML 含 `<table>` 时触发表格处理）
3. 输出 `.md` 文件到输出目录
4. 返回 stats

**转换器实现位置**: `scripts/lib/extraction/html_to_markdown.py`。当前 `scripts/lib/extraction/` 已有 `infobox/`、`preprocessor/`、`converter/`，HTML→MD 作为新的提取能力加入该目录。

### D4: 链接修复和图片下载放在 `scripts/lib/`

**决策**: 
- `scripts/lib/markdown_link_resolver.py` — 链接批量修复
- `scripts/lib/cdp_image_downloader.py` — CDP 图片下载

这两个工具不直接对应 Pipeline phase（它们操作的是已经装配完成的 MD 文件），而是作为 `assemble.py` 或独立后处理步骤调用的库。

### D5: explore scaffold guard 已修复

**决策**: `scripts/explore/strategy_scaffold_generator.py` 的修复已在本次 change 中完成（4 行改动：首行检测 + 跳过逻辑）。设计文档仅记录此决策，不重复描述实现。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| CDP 页面缓存 key 冲突 | 同一域名下不同路径可能产生相同的 safe_path | `raw_to_cache_filename()` 已处理 `/` → `_` 转换，路径深度保证唯一性 |
| 图片下载依赖活 CDP session | 如果浏览器关闭或 session 过期，下载失败 | 图片下载作为独立步骤，失败不阻塞 MD 生成；缓存已下载图片可跳过 |
| 嵌套表格处理复杂度 | 极端嵌套情况可能无法完美转换 | 本次已验证 Nintendo 文档的嵌套模式（一层嵌套 + locale 码表）；更深嵌套作为已知限制记录 |
| `/tmp` 脚本迁移遗漏 | 某个工具函数未被迁入 `lib/` | tasks 阶段逐文件对照，确保 `rebuild_md_v2.py` 中的 `convert_table`、`safe_name`、`html2md` 等函数均迁入 |
