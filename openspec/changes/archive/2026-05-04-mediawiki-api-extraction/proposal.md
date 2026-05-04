# Proposal

## 问题定义

chrome-agent 是跨仓库网页抓取服务，其当前引擎体系全部基于"渲染页面→提取内容"范式（`scrapling-get`, `obscura-fetch`, `scrapling-fetch` 等）。在对 MediaWiki 游戏 wiki（如 balatrowiki.org、vampire.survivors.wiki）进行批量结构化爬取时，Scrapling 路线暴露出系统性缺陷：

**数据质量层面**：
- Scrapling 输出的 Markdown 包含大量视觉噪音：tilt-box-wrap 3D 效果导致同一图片重复 25+ 次，`[edit]` 链接、navbox 页脚（150+ 条目）、`Jump to navigation` 等导航噪音无法通过通用清洗规则根除
- 模板噪音（`{{hl|...}}`、`{{Chips|...}}`、`{{Mult|...}}` 等 DPL wikitext）暴露在渲染后的 Markdown 中，需要启发式正则清理
- Infobox 结构化数据（键值对）被渲染为纯文本，丢失结构
- 内部链接格式含 `"title")` 残留，Category 链接混入正文

**工程效率层面**：
- 后处理清洗存在深度不确定性：vampire 爬取需要 3-4 轮迭代修复 5+ 类噪音；每轮都可能引入新的 edge case
- 清洗规则对 Scrapling 输出格式高度依赖，可复用性受限
- 用户被迫绕过 chrome-agent，自己用 Python 构建 MediaWiki API 工具链（`html2md.py` + `batch_convert.py` + `organize.py` + `fetch_pages.py`），但遇到了新的问题群（DOM 解析 bug、链接路径断裂、HTML 实体编码），这些问题 chrome-agent 同样无法帮助解决

**架构层面**：
- chrome-agent 的策略 schema（`site-strategy-schema`）只描述页面结构和 CSS 选择器，没有记录 CMS API 能力
- AGENTS.md 的 Scrapling-first 路由规则没有为"已知 CMS 平台"提供 API-first 的分支判断
- 引擎注册表（`engine-registry`）的评分维度（efficiency/stability/adaptability）和引擎类型（http/playwright/cdp）全部基于渲染范式，无法表达 API 提取的效率优势

**实际数据对比**（以 balatrowiki.org/w/Joker 页面为样本）：

| 维度 | Scrapling MD | MediaWiki API Wikitext |
|------|-------------|----------------------|
| 数据大小 | 54KB (257 行) | 5KB (模板展开后) |
| 图片重复 | 25× 相同图片 | 1 个模板引用 |
| 导航噪音 | 有（[edit], navbox） | 无 |
| 模板噪音 | 有（{{hl|...}}） | 已展开 |
| Infobox | 文本化丢失结构 | 结构化的键值对 |
| 清洗需求 | 5+ 类噪音需分别处理 | 0（wikitext 无噪音） |

## 范围边界

**本次变更范围内**：
- 新增 `mediawiki-api-extraction` capability：策略驱动的 MediaWiki API 提取管线（Phase A: Discovery → Phase B: Extraction → Phase C: Assembly）
- 扩展 `site-strategy-schema` 的 `api` 字段：允许策略文件声明 CMS API 能力（端点、分类映射、文件名规则、输出配置）
- 为 `balatrowiki.org` 和 `vampire.survivors.wiki` 的策略文件补充 `api` 字段
- 实现 `scripts/mediawiki-api-extract` CLI 工具作为管线执行载体
- 在 AGENTS.md 的 `crawl` 路径中增加 API 路由分支：策略含 `api` 字段时优先走 API 管线，失败时自动 fallback 到 Scrapling
- 修复 `sites/strategies/registry.json` 缺失 balatrowiki.org 条目的治理漏洞

**本次变更范围外**：
- 不创建新的引擎类型。API 提取不是页面渲染，不纳入 `engine-registry.json` 的引擎评分体系
- 不支持 MediaWiki 以外的 CMS 平台（WordPress、Drupal 等），但 schema 的 `api.platform` 字段预留了扩展点
- 不修改 `scrape` 命令（策略无关），API 提取仅通过 `crawl`（策略引导）触发
- 不涉及 `action=parse&prop=text`（API HTML）路径——该路径仍有 DOM 解析复杂性和 HTML 实体编码问题，不如 wikitext 路径干净
- 不取代 `clean-mediawiki.sh`——该工具继续为 Scrapling fallback 路径服务

## Capabilities

### New Capabilities
- `mediawiki-api-extraction`: 策略驱动的 MediaWiki API 内容提取管线，包含 Page Discovery（`action=query`）、Wikitext Extraction（`action=parse&prop=wikitext`）和 Output Assembly（Markdown 转换 + 目录组织 + 链接修正）三个阶段

### Modified Capabilities
- `site-strategy-schema`: 策略文件 YAML frontmatter schema 新增可选 `api` 对象字段，包含 `platform`、`base_url`、`capabilities`、`taxonomy`、`filename`、`output` 子字段

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于前述对话中"从 CMS API 角度规划能力"的共识）

## Impact

**对现有能力的影响**：
- `strategy-guided-crawl`：crawl 命令的路由逻辑增加 API 检查分支，不影响现有 Scrapling crawl 行为
- `mediawiki-extraction-patterns`：不修改噪音分类学，但 API 路径使大部分噪音清洗规则变为不需要（wikitext 无视觉噪音）
- `mediawiki-cleanup-script`：保留作为 Scrapling fallback 路径的清洗工具，不被替换
- `scrape-command`：不受影响（策略无关命令不触发 API 路径）

**对新站点的影响**：
- 新增 Weird Gloop / MediaWiki 站点的策略文件可选择声明 `api` 字段以获得高质量结构化提取
- 未声明 `api` 字段的 MediaWiki 站点继续走 Scrapling 路径，行为不变

**对用户工作流的影响**：
- 用户不再需要为 MediaWiki 游戏 wiki 自建 Python 工具链
- `chrome-agent crawl <url>` 自动选择最优提取路径
- 输出 Markdown 质量从"需要多轮后处理"提升至"开箱即用"

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`site-strategy-schema`、`mediawiki-extraction-patterns`、`strategy-guided-crawl`、`engine-contracts`
  - 项目页：`balatro-wiki-structured-crawl.md`（经验证据）、`vampire-survivors-wiki-scrape.md`（对比基准）、`balatro-wiki-converter/`（现有工具链参考）
  - 回写目标：`site-strategy-schema` spec、`mediawiki-api-extraction` spec、CLI 工具、2 个站点策略文件、`registry.json`、`AGENTS.md`
