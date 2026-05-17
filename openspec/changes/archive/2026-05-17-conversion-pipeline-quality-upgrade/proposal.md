# Proposal

## 问题定义

在 2026-05-16 至 2026-05-17 对 `bindingofisaacrebirth.wiki.gg` 的爬取测试中，经过 6 轮迭代（v1→v8 converter 演进），发现以下系统性问题：

### 1. 转换管线质量问题（9 个已确认 bug）

| # | 问题 | 根因 | 层级 |
|---|------|------|------|
| 1 | TOC 删除导致后续所有章节丢失 | `<div id="toc">` 非贪婪 `.*?` 匹配贪吃了大量内容 | 管线 |
| 2 | heading 中残留 `[edit]` 后缀 | `mw-editsection` span 嵌套结构，单向 regex 无法匹配 | 管线 |
| 3 | 正文内容图片全部丢失（58/58） | `convert_images` 在 `strip` 标签之后执行，图片被清除 | 管线 |
| 4 | Infobox 字段缺失/重复 | infobox 的 `<div class="pi-data">` 嵌套结构未用平衡匹配 | 管线 |
| 5 | 相对链接在离线 Markdown 中无效 | 所有 `/wiki/xxx` 和 `/images/xxx.png` 使用相对路径 | 管线 |
| 6 | 内联 item 链接拆成双链接 | `<span class="tooltip"><a><img></a></span><a>text</a>` 未合并 | 管线 |
| 7 | YouTube 链接文字为通用 "YouTube Video" | 未调用 oEmbed API 获取真实标题 | 管线 |
| 8 | 侧栏导航泄漏到正文 | `<div class="nav-header">` 和导航 `<dl>` 未移除 | 策略 |
| 9 | Boss 名显示为文件名 | 图片 alt 值为 `Boss Mega Satan name.png` 未处理 | 策略 |

### 2. 探索阶段工作流问题（4 个流程缺陷）

| # | 问题 | 后果 |
|---|------|------|
| A | 样本转换后无质量自检即展示 | 用户被迫逐项手动 QA |
| B | 样本内容只在 stdout 输出，无文件路径 | 用户无法在编辑器查看 |
| C | agent 要求用户做 QA 而非自己对比审查 | 违反了 agent 的职责边界 |
| D | 修改 converter 后只重测 1 个样本 | 未验证全部页面类型，引入回归 |

### 3. 能力分层不明确

当前管线层（`HtmlToMarkdownConverter`）与策略层（`strategy.md` 的 `extraction` 配置）之间没有清晰的抽象边界。通用能力（如 balanced element removal）被重复实现，而站点专属语义（如 health hearts 计数、Boss name 提取）混入管线代码。

## 范围边界

### 范围内

- `HtmlToMarkdownConverter` 增加 balanced element removal、tooltip merge、oEmbed extraction 方法
- 所有内部链接和图片使用完整 URL（`--wiki-domain` 参数化），实现合规的相对链接→外部 URL 转换
- 自检系统从 S1-S7 升级到 S1-S12，增加章节完整性、导航泄漏、相对链接零残留、YouTube 标题质量等检查
- Explore 工作流增加 Agent Gate 行为规范：自检报告必须先于样本展示，样本必须输出文件路径
- 策略文件 `extraction` 配置增加 `infobox_field_handlers` 语义映射
- wiki.gg 平台模板增加 `image_filtering` 配置
- 自检 auto-remediation 增加 `tooltip_merge`、`full_url` 等可修复类型

### 范围外

- 不修改 MediaWiki API 提取管线的 Phase A/B/C 编排逻辑
- 不修改 `crawl` 和 `scrape` 命令的执行路径
- 不新增引擎或修改引擎选择策略
- 不修改输出生命周期（`output-lifecycle`）管理逻辑
- 不处理其他平台（Fandom、static site 等）的特殊转换需求

## Capabilities

### New Capabilities

- `balanced-element-removal`: 通用的 HTML 平衡元素移除方法，替代非贪婪 regex `.*?`，支持嵌套 `<div id="toc">`、`<span class="mw-editsection">`、`<table class="nav-box">` 等元素的精确删除
- `tooltip-icon-link-merge`: MediaWiki tooltip 模式的内联图片+文字链接合并预处理，将 `<span class="tooltip"><a><img></a></span><a>text</a>` 合并为 `[![img] text](url)`
- `full-url-parameterization`: 链接和图片 URL 的完整 URL 参数化转换，通过 `wiki_domain` 参数将 `/wiki/Xxx` 和 `/images/Xxx.png` 转换为 `https://domain/wiki/Xxx`

### Modified Capabilities

- `sample-self-check`: 自检体系从 S1-S7 升级到 S1-S12，新增 S8 章节完整性、S9 导航泄漏、S10 YouTube 标题质量、S11 相对链接零残留、S12 Infobox 字段语义质量；升级 S1 图片检查（增加 full URL 验证）、S3 信息框检查（增加字段数+HTML残留检查）、S5 文本异常（增加 HTML 标签残留检测）、S6 表格检查（增加行数偏差阈值）
- `explore-workflow`: explore 工作流增加 Agent Gate 行为规范：样本质量自检报告必须先于样本内容展示，样本必须输出文件路径到 `outputs/` 目录，agent 必须在展示前自行完成对比审查（不推给用户），修改 converter 后必须重测全部样本
- `pipeline-converters`: `HtmlToMarkdownConverter` 增加 `remove_balanced_element()`、`merge_tooltip_links()`、`extract_youtube_links()` 方法；`convert_images()` 增加 `skip_patterns` 参数
- `site-strategy`: 策略文件 `extraction` 配置增加 `infobox_field_handlers` map，定义每个 data-source 字段的值提取方式（text/count_images/extract_cur_id/dedup_pools/simplify_collection/extract_tags）
- `site-strategy-template`: wiki.gg 平台模板增加 `image_filtering.skip_patterns` 配置（`Font_TeamMeat`、`Dlc_*_indicator.png`）

## Capabilities 待确认项

- [x] 能力清单与自检总结一致（覆盖 9 个 bug + 4 个流程缺陷）
- [x] New Capabilities 3 个对应管线层新增基础设施能力
- [x] Modified Capabilities 5 个对应现有 spec 的 delta 修改

## Impact

- **转换器**：`HtmlToMarkdownConverter` API 扩展（新增 3 个方法、修改 2 个方法签名），所有通过 MediaWiki API 管线产出的 Markdown 质量提升
- **自检系统**：`self_check.py` 检查项从 7 扩展到 12，auto-remediation 可修复类型从 5 扩展到 7
- **Explore 工作流**：Agent Gate 行为从"模糊建议"升级为"硬性检查清单"，减少用户手动 QA 负担
- **策略文件**：Isaac Wiki `strategy.md` 需增加 `infobox_field_handlers`，wiki.gg 模板需增加 `image_filtering`
- **向下兼容**：管线现有调用方（Phase B/C、standalone extraction）不受影响，新增方法为可选调用

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`sample-self-check`、`explore-workflow`、`pipeline-converters`、`site-strategy`、`site-strategy-template`
  - 项目页：`strategy.md`（Isaac Wiki）、`mediawiki-wiki-gg.yaml`、converter 代码、explore scripts、`AGENTS.md`
  - 回写目标：4 个 spec delta 文件 + `AGENTS.md`
