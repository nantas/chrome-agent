# Proposal

## 问题定义

当前 `chrome-agent crawl` 的 MediaWiki API 管线和 Scrapling 管线都将"原始内容获取"与"HTML→Markdown 转换"耦合在一个原子操作中完成。以 binding of isaac wiki（1769 页）为例，单次全量爬取耗时约 11 小时（`batch_delay_ms: 1200` + `tier: strict` 速率限制）。每次调整 extraction 规则、converter 行为或输出格式，都需要重新执行全量 API 请求，无法在已有原始数据的基础上反复迭代后处理。

同时，`extraction_results.json` 只持久化 `status` 和 `error`，原始 API 响应（wikitext、渲染 HTML、图片列表）在转换完成后全部丢弃，导致 `--phase assemble` 也无法从持久化数据重建结果。

**核心痛点**：调整 Markdown 生成细节的成本 = 全量 API 爬取成本（数小时 + IP 限流风险）。

## 范围边界

**范围内**：
- 将 fetch（原始内容获取）与 convert（HTML→Markdown 转换）拆分为两个独立 pipeline phase
- 引入持久化内容缓存层，按 `<platform>/<domain>/` 组织，支持跨 session 复用
- Scrapling 路径和 MediaWiki API 路径统一支持 `--phase fetch` / `--phase convert`
- 修复 `extraction_results.json` 不保存原始内容的 bug
- 移除 deprecated 的 `--phase extract`、`A`、`B`、`C`、`homepage` 值

**范围外**：
- 不改变 discovery phase（`--phase discover` 保持不变）
- 不改变 assembly phase 的内部逻辑
- 不引入缓存过期/失效策略（v1 仅支持 `--re-fetch` 手动刷新）
- 不引入增量爬取逻辑（新页面发现仍依赖完整 discovery）

**验证策略**：
- 不执行全量 1769 页爬取验证
- 选取 ~10 个页面覆盖不同页面类型（entity_page、list_page、disambiguation），验证 fetch→convert 完整链路
- 验证 fetch 产出的缓存可被后续 fetch 识别并跳过（不重复下载/覆盖）

## Capabilities

### New Capabilities
- `page-content-cache`: 持久化页面原始内容缓存层——按 `<platform>/<domain>/<safe_title>.json` 组织，存储 API 获取的完整原始响应（或 Scrapling 下载的原始 HTML + 元数据），支持跨 session 复用、存在性检测和清单查询
- `pipeline-fetch-phase`: 独立的 fetch phase——从 API/Scrapling 获取页面原始内容，写入 `.cache/<platform>/<domain>/`，支持缓存跳过（已有缓存不重复请求）
- `pipeline-convert-phase`: 独立的 convert phase——从缓存读取原始内容，应用 strategy extraction 规则执行 HTML→Markdown 转换，纯本地执行无网络请求

### Modified Capabilities
- `mediawiki-api-extraction-pipeline`: Phase B 拆分为 fetch 和 convert 两个独立 phase；`--phase` choices 新增 `fetch`、`convert`，移除 `extract` 及所有 deprecated 值（`A`、`B`、`C`、`homepage`）；`extraction_results.json` 保存 `content` 和 `rendered_html` 以修复 assemble 阶段数据丢失
- `strategy-guided-crawl`: Scrapling 路径支持 `--phase fetch`（保存 HTML 到缓存）和 `--phase convert`（从缓存读取转换）；统一两条路径的 CLI 语义
- `pipeline-cli-entry`: `--phase` schema 变更（新增/移除 choices）；新增 `--re-fetch` flag 支持强制刷新缓存；缓存目录路径从 strategy 配置推导

## Impact

| 维度 | 影响 |
|------|------|
| 用户工作流 | 新增 `--phase fetch` / `--phase convert` 两步工作流；全量爬取只需一次 fetch，后续规则调整只需 convert |
| 性能 | 单次 extraction 规则调整从 ~11 小时降为 ~数分钟（convert 纯本地） |
| 存储 | 新增 `.cache/` 目录，每 wiki 约数百 MB（取决于页面数和 HTML 大小） |
| 向后兼容 | **不兼容**：移除 `--phase extract` 和 deprecated 值；`--phase all` 保持全流程默认行为 |
| Scrapling 路径 | `--keep-html` 语义变更：HTML 保存位置从 runDir 移至缓存目录 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页（四个 capability spec）已确认
  - 项目页（AGENTS.md / README.md）待 verification 后回写
  - Obsidian 项目页面待确认后补充
