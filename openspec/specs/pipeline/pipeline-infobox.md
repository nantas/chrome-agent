# Pipeline Domain: Infobox — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `shared-infobox-renderer` | frozen |
| `unified-infobox-extraction` | frozen |
| `pipeline-infobox-rendering` | frozen |
| `balanced-element-removal` | frozen |

Paths have been updated to reflect the current directory structure.

---

# Pipeline Infobox Specification

## Purpose

Defines the unified infobox extraction and rendering system, including dual-parser support (BeautifulSoup + selectolax), config-driven selectors, the shared infobox module, handler callback architecture, empty label handling, and balanced element removal for nested HTML cleanup.

---

## Requirements

### Requirement: shared-infobox-module

系统 SHALL 提供共享模块 `lib/extraction/infobox.py`，包含可移植的 infobox→Markdown table 逻辑，可被 `HtmlToMarkdownConverter` 和 `sample_converter.py` 共同导入。

模块暴露函数签名：
```python
def extract_infobox(html_or_node, config, wiki_domain, **kwargs) -> str
```

#### Scenario: shared-module-exists
- **WHEN** 检查仓库
- **THEN** `lib/extraction/infobox.py` SHALL 存在且可从两个调用方导入
- **AND** SHALL NOT 产生循环依赖

#### Scenario: infobox-table-output-identical
- **WHEN** 同一 infobox HTML 通过不同调用方传入
- **THEN** 输出 Markdown table SHALL 完全相同

### Requirement: basename-empty-label-fix

`****` 空 label bug SHALL 在共享模块中修复。

#### Scenario: empty-label-not-rendered
- **WHEN** infobox field 的 label 节点仅含 `<img>` 无文本
- **THEN** 该 field SHALL 被跳过

#### Scenario: labeled-field-with-image
- **WHEN** label 节点同时含文本和图片
- **THEN** label SHALL 为纯文本（忽略图片中的内容）

### Requirement: dual-parser-infobox-extraction

系统 SHALL 在 `lib/extraction/infobox.py` 中提供 `extract_infobox()` 函数，同时支持 raw HTML 字符串（BeautifulSoup 解析）和预解析的 selectolax Node 对象。

#### Scenario: BS4 mode from explore path
- **WHEN** `extract_infobox()` 以 raw HTML 字符串和 `parser="auto"` 调用
- **THEN** SHALL 使用 BeautifulSoup 解析，通过 `config.infobox.selector` 定位 infobox 容器

#### Scenario: Selectolax mode from pipeline path
- **WHEN** `extract_infobox()` 以 selectolax Node 对象调用
- **THEN** SHALL 直接使用该节点，不重新解析

### Requirement: config-driven-selectors

系统 SHALL 从 `extraction.infobox` 配置读取所有 infobox 选择器：`selector`、`field_selector`、`label_selector`、`value_selector`。

#### Scenario: default selector values
- **WHEN** `field_selector` 未在 config 中指定
- **THEN** 默认 SHALL 为 `"div.pi-data"`（wiki.gg 标准），非 `"tr"`

### Requirement: dual-handler-lookup

系统 SHALL 支持两种 handler 查找策略，按顺序尝试：(1) label 文本匹配，(2) `data-source` 属性匹配及 `ds(key)` 别名。

#### Scenario: handler found by label text
- **WHEN** `field_handlers` 包含匹配 field label 文本的 key
- **THEN** SHALL 应用该 handler

#### Scenario: handler found by data-source alias
- **WHEN** label 文本无匹配但 field 有 `data-source` 属性且 `field_handlers` 含 `ds(key)` 格式
- **THEN** SHALL 通过别名匹配应用 handler

### Requirement: nav-strip-config-driven

系统 SHALL 通过 infobox config 中的 `nav_strip_selectors` 支持配置驱动的 nav 元素移除。

#### Scenario: nav strip selectors configured
- **WHEN** `config.infobox.nav_strip_selectors` 包含选择器
- **THEN** 匹配元素 SHALL 从 value 单元格中移除

#### Scenario: nav strip selectors not configured
- **WHEN** `nav_strip_selectors` 缺失
- **THEN** 不执行 nav 移除（无硬编码 fallback）

### Requirement: callback-based-handler-execution

系统 SHALL 接受可选回调函数 `render_inline_children_fn` 和 `apply_handler_fn`。

#### Scenario: callbacks provided (pipeline path)
- **WHEN** 两个回调都提供
- **THEN** SHALL 使用它们进行 label 渲染和 handler 应用

#### Scenario: no callbacks (explore path)
- **WHEN** 未提供回调
- **THEN** SHALL 使用内置文本提取 fallback

### Requirement: empty-label-skip

系统 SHALL 跳过空 label 的 infobox 字段。

#### Scenario: label node contains only images
- **WHEN** field 的 label 节点渲染为空字符串
- **THEN** 该 field SHALL 被排除

### Requirement: markdown-table-output

系统 SHALL 输出 `## Infobox` 前缀的 Markdown table。

#### Scenario: fields found
- **WHEN** 一个或多个字段被成功提取
- **THEN** 输出格式为 `## Infobox\n\n| Field | Value |\n| --- | --- |\n| **label** | value |`

#### Scenario: no fields found
- **WHEN** 无字段被提取
- **THEN** 输出为空字符串

### Requirement: render-infobox-table-uses-shared-lib

`HtmlToMarkdownConverter._render_infobox_table()` SHALL 调用 `lib.extraction.infobox.extract_infobox()`。

#### Scenario: infobox rendering during conversion
- **WHEN** `_render_infobox_table(node)` 被调用
- **THEN** SHALL 调用 `extract_infobox()` 并传递相同参数

#### Scenario: backward compatible callback signature
- **WHEN** 以 `render_inline_children_fn` 和 `apply_handler_fn` 回调调用
- **THEN** 输出 SHALL 与原 `infox_renderer` 行为一致

### Requirement: handler-implementation-stays-in-converter

`_apply_infobox_handler()` 和所有 handler 方法 SHALL 保留在 `html_to_markdown.py` 中，通过回调传递给 `extract_infobox()`。

### Requirement: infox-renderer-module-deprecated

`infox_renderer.py` 已被 `lib/extraction/infobox.extract_infobox()` 替代。原调用点 `from .infox_renderer import render_infobox_table` 已替换为 `from scripts.lib.extraction.infobox import extract_infobox`。

### Requirement: remove-balanced-element

系统 SHALL 提供 `remove_balanced_element(html: str, tag: str, attr_pattern: str) -> str`，通过深度计数移除平衡 HTML 元素，替代非贪婪正则 `.*?`。

方法步骤：
1. 查找匹配 `<tag ...attr_pattern...>` 的开标签
2. 跟踪嵌套深度（初始 1）
3. 遇到 `<tag>` 开标签时深度 +1
4. 遇到 `</tag>` 闭标签时深度 -1
5. 深度归零时移除整个元素
6. 返回处理后的 HTML

#### Scenario: remove-nested-toc-div
- **WHEN** 处理含嵌套 inner div 的 TOC div
- **THEN** 整个 TOC div（含嵌套内容）SHALL 被移除，后续内容保留

#### Scenario: remove-nested-edit-section-span
- **WHEN** 处理含嵌套 bracket 和 edit span 的 `mw-editsection` span
- **THEN** 整个 span SHALL 被移除，`mw-headline` span 保留

#### Scenario: no-match-returns-unchanged
- **WHEN** 无匹配开标签
- **THEN** 返回原始 HTML

#### Scenario: deeply-nested-content-table
- **WHEN** 处理含嵌套 inner table 的 nav-box table
- **THEN** 外层 nav-box table 及嵌套内容 SHALL 被移除

### Requirement: remove-all-matching-elements

系统 SHALL 提供 `remove_all_matching(html: str, tag: str, attr_pattern: str) -> str`，重复调用 `remove_balanced_element` 直到无匹配。

#### Scenario: remove-multiple-navbox-tables
- **WHEN** HTML 中包含 3 个 nav-box table
- **THEN** 全部 3 个 SHALL 被移除，中间内容保留

#### Scenario: remove-all-sidebar-dl
- **WHEN** 处理多个 `<dl>` 元素
- **THEN** 每个匹配的 `<dl>...</dl>` SHALL 被逐一移除
