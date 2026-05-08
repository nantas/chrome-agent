# Proposal

## 问题定义

chrome-agent 的 `mediawiki-api-extract` 管线目前仅支持 **wikitext-first** 内容获取路径（`action=parse&prop=wikitext` → 模板处理 → Markdown）。对于使用复杂 Lua 模板、DRUID infobox 和 JS 驱动卡片网格的 wiki.gg 站点，wikitext 路径难以保留服务端渲染后的完整排版和图片信息。

同时，用户已有 `wiki.gg` 项目（`/Users/nantasmac/projects/personal/wiki.gg`）积累了 HTML→Markdown 转换、图片路径规范化、表格渲染等成熟经验，但该项目未覆盖完整的站点抓取（仅 ns=3000 StS2），且输出结构是按内容类型分类而非按原页面 URL 层级组织。

本 change 目标：
1. 在 chrome-agent 管线中新增 **HTML 渲染获取路径**（`action=parse&prop=text`），直接消费服务端渲染后的 HTML
2. 融合 wiki.gg 项目的 HTML 清洗和转换能力
3. 实现语义化的目录结构映射（按命名空间分容器）
4. 覆盖 StS1 (ns=0) + StS2 (ns=3000) + 分类页 (ns=14) 完整站点
5. 输出与原页面内容组织一致的 Markdown，保留图片链接和页面间链接

## 范围边界

**范围内：**
- `scripts/mediawiki-api-extract/` 管线扩展：新增 HTML 渲染获取策略和转换器
- 语义化目录映射：`ns=0` → 根目录，`ns=3000` → `Slay_the_Spire_2/` 子目录，`ns=14` → `Category_Name/index.md`
- HTML 清洗规则：移除编辑链接、TOC、隐藏元素（`display:none`），保留 infobox、表格、图片
- 图片链接规范化：`/images/...` → 绝对 URL，列表页仅保留 base 图片
- 内链转换：`<a href="/wiki/...">` → 标准 Markdown 相对链接 `[text](relative/path.md)`
- 分类页混合生成：`action=parse` 描述 + `categorymembers` API 成员列表 → `index.md`
- `sites/strategies/slaythespire.wiki.gg/strategy.md` 策略更新

**范围外：**
- 不修改 `wiki.gg` 仓库代码
- 不引入浏览器自动化（Playwright/Scrapling）——API `action=parse` 已返回完整服务端渲染 HTML
- 不下载图片到本地（保留图片 URL 链接即可）
- 不处理用户页、讨论页、模板页、帮助页
- 不处理 Board Game 命名空间（ns=3010）
- 不处理增量更新和状态持久化

## Capabilities

### New Capabilities
- `html-rendered-acquisition`: 通过 MediaWiki API `action=parse&prop=text` 获取服务端渲染 HTML，替代 wikitext-first 路径作为主要内容获取方式
- `semantic-directory-mapping`: 基于命名空间语义的目录结构映射规则（ns=3000→`Slay_the_Spire_2/` 子目录，ns=14→`Category_Name/index.md`）
- `category-page-generator`: 通过 `categorymembers` API 获取分类成员列表，与 `action=parse` 描述文本组合生成分类索引 Markdown
- `html-to-markdown-converter`: 融合 wiki.gg 项目的 HTML 解析引擎，将清洗后的 HTML 转换为保留排版和图片的标准 Markdown

### Modified Capabilities
- `mediawiki-api-extraction-pipeline`: 扩展 Phase B 支持内容获取策略分支（wikitext / html_rendered / hybrid），新增 HTML 清洗和 Markdown 转换阶段
- `site-strategy-slaythespire`: 更新站点策略 frontmatter，新增 `content_acquisition: html_rendered` 配置，更新目录映射和分类页生成规则

## Capabilities 待确认项

- [x] 能力清单已与用户确认
  - 用户确认：ns=0 页面放根目录，ns=3000 页面放 `Slay_the_Spire_2/` 子目录
  - 用户确认：分类页放 `Category_Name/index.md`
  - 用户确认：列表页只保留 base 图片，过滤 upgraded/beta 隐藏图片
  - 用户确认：通过 chrome-agent 管线执行，不修改 wiki.gg 仓库

## Impact

- **正面**：
  - 获得完整服务端渲染的排版信息（infobox、表格、列表网格）
  - 图片链接完整保留，Markdown 可直接在浏览器/阅读器中显示
  - 页面间链接转换为本地相对路径，支持离线浏览
  - 输出目录结构与原站点命名空间结构一致
- **风险**：
  - HTML 清洗规则需要维护，wiki 模板变更可能导致渲染差异
  - `action=parse` 输出体积大（Cards_List 达 1.8MB），批量抓取时需关注性能和内存
  - 分类页 `action=parse` 不返回成员列表，需二次 API 调用补充

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `sites/strategies/slaythespire.wiki.gg/strategy.md`（回写目标）
  - `scripts/mediawiki-api-extract/`（管线扩展）
  - `wiki.gg` 仓库（跨仓库经验输入，不回写）
