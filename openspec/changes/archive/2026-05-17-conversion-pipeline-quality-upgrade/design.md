# Design

## Context

本次 change 基于对 `bindingofisaacrebirth.wiki.gg` 的 6 轮迭代爬取测试（v1→v8 converter），发现了 HTML→Markdown 转换管线中 9 个 bug 和 explore 工作流中 4 个流程缺陷。核心根因有三类：

1. **嵌套 HTML 元素匹配失败**：非贪婪 regex `.*?` 在嵌套结构中产生不确定行为（TOC 删除吃掉全篇、mw-editsection span 只匹配到内层）
2. **URL 未参数化**：内部链接和图片使用相对路径，离线 Markdown 无法访问
3. **Agent Gate 缺失**：无质量自检报告、无文件路径输出、agent 推卸 QA 责任

## Goals / Non-Goals

**Goals:**

- 在所有 MediaWiki 站点的 HTML→MD 转换中，用 balanced depth-counting 替代非贪婪 regex 进行元素移除
- 实现 tooltip icon-text link merge 预处理
- 实现 YouTube oEmbed 标题提取
- 所有内部链接和图片使用完整 URL（通过 `wiki_domain` 参数化）
- 自检体系从 S1-S7 扩展到 S1-S12
- explore 工作流增加 5 个 Agent Gate 行为规范
- 策略文件增加 `infobox_field_handlers` 配置
- wiki.gg 模板增加 `image_filtering` 和 `cleanup_selectors`

**Non-Goals:**

- 不修改 MediaWiki API 管线的 Phase A/B/C 编排
- 不修改 `crawl` / `scrape` 命令的执行逻辑
- 不新增或修改引擎
- 不处理 Fandom / static site / WordPress 等非 wiki.gg 平台
- 不修改输出生命周期或 manifest 格式
- 不把 Isaac Wiki 的 site-specific 逻辑写入通用转换器

## Decisions

### D1: Balanced element removal 作为独立可复用方法

**决策**: 实现 `remove_balanced_element(html, tag, attr_pattern)` 和 `remove_all_matching(html, tag, attr_pattern)` 作为 `HtmlToMarkdownConverter` 的静态方法，可被 pipeline 和 explore scripts 独立调用。

**替代方案**: 在 `clean_html()` 内联实现 → 拒绝，因为 explore 的 `sample_converter.py` 也需要这些方法。

**实现位置**: `scripts/mediawiki_api_extract/converters/html_to_markdown.py`

### D2: Tooltip merge 在 image/link conversion 之前执行

**决策**: 在 `convert_body()` pipeline 中，`merge_tooltip_links()` 在 `convert_images_to_md()` 和 `convert_links_to_md()` 之前调用。顺序为：

```
merge_tooltip_links() → convert_images_to_md() → headings → convert_links_to_md() → tables
```

**理由**: 合并 `<a href="X"><img/></a>` + `<a href="X">text</a>` 必须在图片和链接转换之前完成，否则 `<img>` 已变成 `![alt](url)` 无法匹配。

### D3: wiki_domain 参数化而非硬编码

**决策**: `wiki_domain` 从策略文件的 `domain` 字段或 `api.base_url` 提取，不作为 `HtmlToMarkdownConverter` 构造函数的可选参数。缺失时 raise `TypeError`。

**理由**: 管线层不做任何站点假设。`specs/pipeline-converters` 已有 `domain-parameterization` requirement，本次在实现层落实。

### D4: YouTube oEmbed 为同步阻塞调用

**决策**: 在 `extract_video_links()` 中同步调用 YouTube oEmbed API，使用 5 秒超时。失败时 fallback 到 `YouTube Video (VIDEO_ID)` 格式。

**替代方案**: 异步调用 → 拒绝，explore sample conversion 是低频操作（每样本 1-2 个视频），同步调用的复杂度成本远低于异步实现。

### D5: Agent Gate 规则写入 SKILL.md 非 AGENTS.md

**决策**: explore 阶段的 Agent Gate 行为规范（自检先于展示、输出文件路径、自行审计、全量重测）写入 `skills/chrome-agent/SKILL.md`，与 `explore-workflow` spec 中的 requirement 保持一致。

**理由**: `AGENTS.md` 是治理层面的全局文档，`SKILL.md` 是 explore 工作流的行为入口。Agent Gate 规则是 explore 专属的。

### D6: infobox_field_handlers 为可选配置

**决策**: `extraction.infoxbox_field_handlers` 为可选配置项。缺失时所有字段使用默认 `text` handler。不强制要求每个策略文件定义此 map。

**理由**: 部分站点的 infobox 字段不需要特殊语义处理（纯文本即可），强制配置增加策略编写负担。

## Risks / Migration

### Risk R1: Balanced removal 性能

**风险**: `remove_all_matching()` 对每个匹配元素做一次 O(n) 全文扫描，大型 HTML（Items 页面 1M chars）可能显著慢于 `re.sub(..., flags=re.DOTALL)`。

**缓解**: 
- `remove_all_matching()` 只在 `convert_body()` 预处理阶段调用（TOC/editsection/navbox/nav-header/sidebar dl），总计 ≤ 5 次扫描
- 对 Items 页面的实测（v6 converter，balanced removal 启用，1M HTML → 252KB MD）耗时 < 5 秒，在可接受范围
- 如未来发现性能瓶颈，可优化为单次扫描同时匹配多个 pattern

### Risk R2: oEmbed 依赖外部 API

**风险**: YouTube oEmbed 端点不可达时，视频标题退化为 `YouTube Video (ID)`，可能触发 S10 自检 fail。

**缓解**: oEmbed 调用包含 5 秒超时和异常捕获，失败不阻塞转换。S10 的 fixable_type 为 `youtube_title`，auto-remediation 可重试。

### Risk R3: wiki_domain 缺失导致 TypeError

**风险**: 如果策略文件未正确定义 `domain` 或 `api.base_url`，`HtmlToMarkdownConverter` 构造时抛出 `TypeError`。

**缓解**: 
- `mediawiki-wiki-gg.yaml` 模板已定义 `domain` 占位符
- Pipeline 启动时 `parse_strategy()` 校验必填字段
- 未提供 domain 的站点只能通过 `bootstrap-strategy` 补充

### Risk R4: Agent Gate 规则对现有 explore 流程的中断

**风险**: 新增的 Agent Gate 规则（自检报告先于展示、全量重测）可能延长 explore 流程，对已有策略的站点造成冗余检查。

**缓解**: explore 流程对 strategy-matched 场景保持现有行为不变。Agent Gate 仅在 strategy-gap 场景（deep discovery → sample conversion）生效。

### Migration Path

1. **转换器升级**: `HtmlToMarkdownConverter` 新增方法为纯增量，现有调用方不受影响
2. **自检升级**: `self_check.py` 新增 S8-S12 函数，`run_checks()` 签名从 5 参数扩展到 7 参数。现有调用方需添加 `wiki_domain` 和 `page_type` 参数
3. **策略文件升级**: `infobox_field_handlers` 为可选配置，现有策略文件无需修改即可正常使用
4. **模板升级**: `mediawiki-wiki-gg.yaml` 新增 `image_filtering` 和 `cleanup_selectors`，已有站点需手动合并或重新 bootstrap
