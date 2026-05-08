# Design

## Context

chrome-agent 的 `mediawiki-api-extract` 管线当前仅支持 wikitext-first 内容获取（`prop=wikitext`）。对于 `slaythespire.wiki.gg`，测试验证表明 `action=parse&prop=text` 返回完整服务端渲染 HTML（Cards_List 达 1.8MB，含 576 个 card-box 和全部图片），且 API 端点不受 Cloudflare challenge 影响。同时，用户已有 `wiki.gg` 项目（跨仓库）积累了成熟的 HTML→Markdown 转换逻辑。

本 design 定义如何在 chrome-agent 管线中扩展 HTML 渲染路径，融合 wiki.gg 经验，实现语义化目录映射和完整站点抓取。

## Goals / Non-Goals

**Goals:**
- 新增 `HtmlRenderedAcquisitionStrategy` 获取服务端渲染 HTML（spec: `html-rendered-acquisition`）
- 新增 `HtmlToMarkdownConverter` 融合 wiki.gg 的 HTML 解析引擎（spec: `html-to-markdown-converter`）
- 实现语义化目录映射：`ns=0`→根目录，`ns=3000`→`Slay_the_Spire_2/`，`ns=14`→`Category_Name/index.md`（spec: `semantic-directory-mapping`）
- 实现分类页混合生成：parse 描述 + categorymembers 列表（spec: `category-page-generator`）
- 扩展 Phase B 支持策略分支选择（spec: `mediawiki-api-extraction-pipeline`）
- 更新 `slaythespire.wiki.gg` 站点策略配置（spec: `site-strategy-slaythespire`）

**Non-Goals:**
- 不引入浏览器自动化（Playwright/Scrapling）——API 已返回完整渲染 HTML
- 不修改 `wiki.gg` 仓库代码（仅作为经验输入）
- 不处理增量更新、状态持久化、图片本地下载
- 不处理 Board Game 命名空间（ns=3010）
- 不处理用户页、讨论页、模板页

## Decisions

### Decision 1: 管线架构——在 Phase B 内部分支，而非新建管线

**选择**：扩展现有 `mediawiki-api-extract` 管线的 Phase B，在 `process_single_page` 内根据策略选择 wikitext 或 HTML 路径。

**理由**：
- Phase A（discovery）和 Phase C（assembly）对两种路径通用
- 只需在 Phase B 的内容获取和转换阶段分支
- 最小化代码重复，保留现有管线基础设施（并发、重试、统计）

**实现**：
- `strategies.py` 新增 `HtmlRenderedAcquisitionStrategy` 实现 `ContentAcquisitionStrategy` 协议
- `strategies.py` 新增 `HtmlToMarkdownConverter` 类封装清洗和转换逻辑
- `_STRATEGY_REGISTRY` 注册 `"html_rendered"` 到 `content_acquisition`
- `process_single_page` 根据 `content_strategy` 类型选择处理路径

### Decision 2: HTML 清洗与转换——复用并扩展 wiki.gg 经验

**选择**：将 wiki.gg 项目的 `convert/markdown.py` 和 `clean/html.py` 逻辑提取并适配到 chrome-agent 的 `HtmlToMarkdownConverter` 中。

**理由**：
- wiki.gg 项目已验证 selectolax 解析器在处理 MediaWiki parse 输出时的效率和准确性
- 现有 HTML→Markdown 转换器支持标题、列表、表格、图片、内链、代码块等所有必要元素
- 避免重复造轮子，同时保留 chrome-agent 管线的统一接口

**实现**：
- 新建 `html_converter.py`（或内嵌在 `strategies.py`）包含：
  - `clean_parse_html()`: 移除 `.mw-editsection`, `#toc`, `.hatnote`, `display:none` 元素
  - `html_to_markdown()`: 将清洗后的 HTML 转为 Markdown，支持 block/inline 元素
  - `normalize_href()`: 将相对路径转为绝对 URL（图片、内链）
- 新增 `display:none` 元素过滤逻辑（wiki.gg 原项目未包含此规则）

### Decision 3: 目录映射——集中式 `title_to_filepath()` 函数

**选择**：在 manifest 生成阶段（Phase A）统一计算 `target_directory` 和 `target_filename`，而非分散在各处。

**理由**：
- 保证全局一致的映射规则
- 链接解析器（Phase B）和文件写入（Phase C）共享同一映射
- 便于验证和调试

**实现**：
- `semantic_directory_mapping.py` 或内嵌在 `strategies.py` 中：
  ```python
  def title_to_filepath(title: str, ns: int) -> tuple[str, str]:
      """Return (target_directory, target_filename)"""
  ```
- 在 `CategoryMembersDiscoveryStrategy.discover_pages()` 或 `phase_a.py` 的 manifest 构建中调用
- 分类页特殊处理：`ns=14` → `target_directory = slugify(title.removeprefix("Category:"))`, `target_filename = "index.md"`

### Decision 4: 链接转换——基于 manifest 的全局映射表

**选择**：在 Phase B 处理每个页面时，使用预构建的 `title → filepath` 映射表解析所有内部链接。

**理由**：
- 需要处理跨命名空间链接（StS2→StS1、StS1→StS2）
- 相对路径计算需要知道源文件和目标文件的完整路径
- 全局映射表保证一致性

**实现**：
- 扩展 `ShortNameLinkResolver`：
  - 构建 `title → (target_directory, target_filename)` 索引
  - 解析 `<a href="/wiki/Title">` 时查表获取目标路径
  - 使用 `os.path.relpath()` 计算源到目标的相对路径
  - 输出格式为标准 Markdown `[text](relative/path.md)`
- 外部链接、锚点链接、非导出命名空间链接按 spec 规则处理

### Decision 5: 分类页处理——ns=14 Category 页面不抓取

**选择**：不在 manifest 中纳入 ns=14 的 Category 页面。`Slay the Spire 2:Ancients` 这类主题分类首页是 ns=3000 的内容页，通过常规 discovery 即可获得。

**理由**：
- `Category:Ancients` 只是字母表顺序的自动分类索引，`Slay the Spire 2:Ancients` 才是人工编辑的主题首页
- ns=14 页面通过 `action=parse` 只返回描述段落（如 "All Ancient related information is located here."），成员列表需额外 `categorymembers` API
- 移除 ns=14 简化了管线逻辑，减少 API 调用

**实现**：
- 策略文件 `namespaces: [0, 3000]`（移除 14）
- 早期实现中的 Phase C `CategoryPageAssembler` 路径不再触发

### Decision 6: 列表页图片过滤——在清洗阶段移除 `display:none` 元素

**选择**：将 `display:none` 过滤作为 HTML 清洗的通用规则，不仅限于列表页。

**理由**：
- 这是服务端渲染 HTML 的普遍问题（隐藏状态/变体元素）
- 通用规则比页面类型特定规则更易维护
- 符合用户"只保留 base 图片"的明确要求

**实现**：
- 在 `clean_parse_html()` 中，使用 selectolax 查找并移除所有 `style` 属性包含 `"display:none"` 的元素

### Decision 7: DRUID 卡牌拼凑图片过滤和卡牌统计提取

**选择**：在 `HtmlToMarkdownConverter.clean_html()` 中过滤 DRUID card frame 拼凑图片（`StS2_Bg*`、`StS2_Frame*`、`StS2_Banner*`、`StS2_Type*`、`*Orb.png`、`*Art.png`）；在 `_process_html_page()` 中提取 DRUID infobox 结构化数据并注入格式化统计表。

**理由**：
- 单卡页面的 DRUID infobox 使用 CSS 绝对定位将 6 层图片（背景框、稀有度框、类型标记、角色水晶、卡面插图）叠成一张视觉卡牌。平铺为 Markdown 后完全不可读
- infobox 中卡牌文字信息（名称、费用、类型、稀有度、基础/升级描述）以 `.druid-toggleable-data` 子容器按 Base/Upgraded 标签页组织
- 直接移除 infobox 并注入结构化的 Card Stats 表格后，单卡页面变得完整可读

**实现**：
- `REMOVAL_SELECTORS` 新增 `.druid-infobox`
- `clean_html` 新增 CSS selector：`img[src*="StS2_Bg"], img[src*="StS2_Frame"], img[src*="StS2_Banner"], img[src*="StS2_Type"], img[src*="Art.png"]`
- `strategies.py` 新增 `extract_card_stats()` 函数，解析 DRUID infobox 的行结构（`druid-row-Name`, `druid-row-EnergyCost`, `druid-row-Description` 等）
- `phase_b.py` 的 `_process_html_page()` 在转换后调用 `extract_card_stats()`，将生成的表格插入在页面描述之前
- 完成卡牌图从 frontmatter `image` 字段注入：`https://{domain}/images/{filename}`

### Decision 8: Cards_List 按角色+稀有度拆分子页面

**选择**：不在 Phase C 中输出全量卡片网格，而是解析 `data-color` 和 `data-rarity` 属性按(角色, 稀有度)组合生成子页面。

**理由**：
- `Slay the Spire 2:Cards_List` 的 `action=parse` HTML 包含 576 个 card-box，转为 Markdown 后达 6.8MB，为单页不可读
- 每个 card-box 有 `data-color` 和 `data-rarity` 属性，可直接用于分组
- 按角色首页中的卡牌池信息（Common x20、Uncommon x36、Rare x26 等）生成 5 个子页面，阅读体验更好

**实现**：
- `strategies.py` 新增 `split_card_list_pages()` 函数
- 使用 selectolax 解析 `#cardsContainer` 中的 `.card-box> 元素
- 按 (color, rarity) 分组，每组生成 `{Color}/{Rarity}.md` 子页面
- 每张卡片格式：`## [Name](page.md)\n\n![img](url)\n\n*rarity - color - type*\n\ndescription\n\n---`
- `{Color}/index.md` 生成稀有度统计表格
- 顶层 `index.md` 替换为角色导航页面
- `phase_c.py` 的列表页处理流程中调用 `split_card_list_pages()`

## Risks / Migration

### Risk 1: HTML 清洗规则脆弱性

**风险**：wiki.gg 站点模板变更（如 DRUID infobox 结构调整、新的隐藏元素模式）可能导致清洗后 HTML 结构异常。

**缓解**：
- 清洗规则基于 CSS 选择器，尽量使用稳定的 class/ID（如 `.mw-editsection`, `#toc`）
- 保留 `REMOVAL_SELECTORS` 元组，便于维护者扩展
- 在 verification 阶段抽样验证清洗后的 HTML 结构完整性

### Risk 2: 大页面内存压力

**风险**：`Slay the Spire 2:Cards_List` 的 parse HTML 达 1.8MB，并发处理多个大页面可能导致内存峰值。

**缓解**：
- 限制并发数（现有 `concurrency` 参数已支持）
- selectolax 解析器内存效率高（C 后端）
- 如遇到 OOM，可降低并发或分批处理

### Risk 3: 分类页成员列表不完整

**风险**：`categorymembers` API 返回的成员可能包含重定向页、已删除页或不符合导出条件的页。

**缓解**：
- 使用 `cmprop=ids|title|type` 获取成员类型信息
- 过滤 `type=subcat` 到子分类区段
- 可选：通过 `prop=info` 批量验证成员页面存在性

### Risk 4: 跨仓库经验融合的维护成本

**风险**：wiki.gg 项目的转换逻辑演进后，chrome-agent 中的副本可能过时。

**缓解**：
- 在 `HtmlToMarkdownConverter` 文档中标注逻辑来源（wiki.gg `convert/markdown.py`）
- 变更时同步评估是否需要反向同步
- 长期考虑将通用转换逻辑提取为独立包

### Migration

- **现有站点策略**：更新 `slaythespire.wiki.gg/strategy.md` 的 `content_profile.content_acquisition` 为 `html_rendered`
- **现有管线调用**：命令行参数不变，策略文件驱动行为变化
- **向后兼容**：`wikitext_only` 和 `hybrid_wikitext_plus_rendered` 策略继续可用
