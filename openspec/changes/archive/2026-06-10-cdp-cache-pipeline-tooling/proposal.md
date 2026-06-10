# Proposal

## 问题定义

在 Nintendo Developer Portal 爬取任务中暴露了 chrome-agent 的三个能力缺口：

1. **chrome-cdp 引擎无缓存机制**：CDP 爬取的 HTML 页面放在 `/tmp/` 临时目录，与 Pipeline 标准的 `.cache/<platform>/<domain>/<page>.json` 缓存体系完全脱节。每次会话重启后缓存丢失，必须重新通过 CDP 提取，无法跨 session 复用。

2. **HTML→Markdown 转换无标准路径**：本次任务大量编写了 HTML→MD 转换脚本（含表格 rowspan/colspan、嵌套表格、管道符转义），但全部放在 `/tmp/nintendo-rebuild/` 下，任务完成后即丢弃。同类的图片下载、链接修复、表格格式化等能力也散落在临时脚本中，不可复用。

3. **explore scaffold 无条件覆盖手动编写的策略**：`strategy_scaffold_generator.py` 在所有情况下都以 `"w"` 模式覆盖 `strategy.md`，没有检测文件是否已被手动编辑。导致本次任务中精心构建的 Nintendo 策略被 `chrome-agent explore` 重置为空白模板。

## 范围边界

**In scope**：
- chrome-cdp 引擎的页面缓存接入 Pipeline `.cache/` 体系
- 可复用的 HTML→Markdown 转换器（含表格处理）纳入 `scripts/lib/` 或 Pipeline phase
- Markdown 链接批量修复工具（内部相对链接 vs 外部完整 URL）
- CDP 图片下载与本地化工具
- explore scaffold 写入保护机制

**Out of scope**：
- chrome-cdp 引擎本身的 CDP 协议通信能力（`.agents/skills/chrome-cdp/scripts/cdp.mjs` 已存在）
- 策略注册表变更（`registry.json` / `_STRATEGY_REGISTRY`）
- 新的 CLI 命令路由（复用现有 `fetch` / `explore` 命令入口）
- 站点特定策略逻辑（如 Nintendo 的 `contents/` URL 模式，属于 strategy.md frontmatter 范畴）

## Capabilities

### New Capabilities
- `cdp-page-cache`: chrome-cdp 引擎的持久化页面缓存，遵循 `.cache/<platform>/<domain>/<page>.json` 约定，支持 `save_page_cache()` / `is_cached()` / `load_page_cache()` 接口
- `html-to-markdown-converter`: 可复用的 HTML→Markdown 转换器，支持表格 rowspan/colspan 传播、嵌套表格内联展平、管道符转义、图片外链保留
- `markdown-link-resolver`: Markdown 批量链接修复，根据页面映射将内部相对链接转为 `.md` 引用，未爬取页面转为完整 URL
- `cdp-image-downloader`: 通过 CDP fetch→base64 下载页面图片并本地化，MD 引用从外链切换为相对路径

### Modified Capabilities
- `explore-scaffold`: explore 管线的 scaffold 生成步骤增加写入保护——检测已存在策略文件的首行，若非 `Auto-generated scaffold` 标记则跳过覆盖，返回 `skipped` 状态

## Capabilities 待确认项

- [x] 能力清单已确认：来自复盘讨论的明确共识
- [ ] 待确认：`cdp-page-cache` 是否需要单独的 CLI 清理命令，还是复用 `chrome-agent clean --scope all`

## Impact

| 影响面 | 说明 |
|--------|------|
| `scripts/pipeline/pipeline/cache.py` | 无改动——现有接口已足够容纳 chrome-cdp 缓存 |
| `scripts/pipeline/pipeline/phases/` | 新增 `fetch_cdp.py`（CDP 获取+缓存写入）和 `convert_html.py`（HTML→MD 转换） |
| `scripts/lib/` | 新增 `markdown_link_resolver.py` 和 `cdp_image_downloader.py` |
| `scripts/explore/strategy_scaffold_generator.py` | 已修复（本次 change 中完成）：首行检测 + 跳过覆盖 |
| `docs/architecture/02-pipeline-flow.md` | 更新管线图，新增 chrome-cdp fetch 路径说明 |
| `docs/architecture/07-explore-workflow.md` | 更新 scaffold 生成章节，记录 overwrite guard |
| `sites/strategies/developer.nintendo.com/strategy.md` | 不受影响——overwrite guard 已保护手动编辑的策略 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md
