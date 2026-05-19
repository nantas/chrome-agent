# Design

## Context

Change 1 已完成：`lib/strategy_loader.py` 和 `lib/config_resolver.py` 已存在于 `scripts/lib/`。本 change 在此基础上新建 `lib/extraction/` 子包，统一 infobox 提取和 HTML 预处理的两套独立实现。

当前双实现状态：
- `sample_converter._extract_infobox()` (BS4, 119行) — explore 路径独占
- `infox_renderer.render_infobox_table()` (selectolax, 136行) — pipeline 路径独占（docstring 声称 "shared" 但仅有 1 个调用方）
- `sample_converter._apply_extraction()` Phase 1-4 (BS4, 128行) — explore 路径独占
- `html_to_markdown.clean_html()` (selectolax, ~25行) — pipeline 路径独占，本 change 不改动

## Goals / Non-Goals

**Goals:**
- 统一 infobox 提取到 `lib/extraction/infobox.py`，支持 BS4 和 selectolax 双解析器
- 统一 explore 路径预处理到 `lib/extraction/preprocessor.py`
- `sample_converter._apply_extraction()` 改为调用共享库，删除 `_extract_infobox()`、`_apply_field_handler()`
- `html_to_markdown._render_infobox_table()` 改用共享库，删除 `infox_renderer.py`
- `sample_converter._load_extraction_rules()` 改用 `lib.strategy_loader`

**Non-Goals:**
- 移动 `html_to_markdown.py` 文件到 `lib/extraction/converter.py` → Change 3
- 统一 `clean_html()` → 不做（selectolax 紧耦合于 `html_to_markdown` 类）
- 移动 handler 实现从 `html_to_markdown.py` → Change 3
- 拆分 orchestrator / 包重命名 → Change 3

## Decisions

### D1: Infobox 统一函数签名

`extract_infobox()` 接受 `html_or_node` 参数，通过 `parser="auto"` 自动检测类型：
- `str` → BS4 解析
- selectolax Node → 直接使用

签名与 `infox_renderer.render_infobox_table()` 向后兼容，新增支持 raw HTML 字符串输入（BS4 模式）。

回调函数 `render_inline_children_fn` 和 `apply_handler_fn` 保持可选，无回调时使用内置 fallback text extraction。

### D2: field_selector 默认值统一

当前 `sample_converter` 默认 `"tr"`，`infox_renderer` 默认 `"div.pi-data"`。

统一为 `"div.pi-data"`（wiki.gg 标准）。这是因为：
- 所有 wiki.gg 策略文件都使用 Fandom portable infobox 格式（`div.pi-data`）
- `"tr"` 是旧版 MediaWiki 表格 infobox 的选择器，当前无活跃策略使用

**影响评估**：需 grep 所有策略文件的 `field_selector` 确认无 `"tr"` 依赖。

### D3: Handler 查找策略合并

合并两种查找方式为顺序尝试：
1. label text 直接匹配
2. `data-source` 属性构造 `ds(key)` 格式匹配

这与当前 `sample_converter` 的行为一致，`infox_renderer` 的纯 data-source 匹配作为 fallback 已被覆盖。

### D4: preprocessor 不改动 clean_html

`html_to_markdown.clean_html()` 保持不变。理由：
- 使用 selectolax，与 `HtmlToMarkdownConverter` 类紧耦合
- 强行统一需在 preprocessor 中引入 selectolax + BS4 双路径，增加复杂度
- `clean_html()` 的职责（移除 UI 噪音）与 explore 预处理的职责（全量 cleanup）差异较大

### D5: _apply_extraction 重写为无状态 4 步

当前 `_apply_extraction()` 用单个 BeautifulSoup `soup` 对象贯穿所有 phase（可变状态）。重写后：
- Step A: `extract_infobox(full_html, config)` — 只读取，返回 Markdown 字符串
- Step B: `preprocess_html(full_html, config, context="explore")` — 执行所有 DOM 修改，返回清理后的 HTML
- Step C: `convert_html_to_markdown(cleaned_html, ...)` — 核心转换
- Step D: 拼接 infobox + body

两步在**同一份 HTML 字符串**上独立操作，不共享可变状态。代价是 BS4 解析两次（一次 extract_infobox，一次 preprocess_html 内部），但预处理是轻量操作，性能影响可忽略。

### D6: infox_renderer.py 删除而非保留 wrapper

删除 `infox_renderer.py`，理由：
- 仅有 1 个调用方（`html_to_markdown.py`）
- 保留 wrapper 增加维护负担，未来仍需确保 wrapper 与共享库同步
- 直接 import 更清晰：`from scripts.lib.extraction.infobox import extract_infobox`

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| infobox 产出格式变化（双实现合并） | 统一后 `field_selector` 默认值改为 `"div.pi-data"`，可能影响无显式配置的策略。需 grep 策略文件确认 |
| BS4 两次解析性能开销 | 可忽略：预处理是轻量字符串操作，且仅在 explore 路径（样本验证，非批量） |
| 删除 infox_renderer 后 import 断裂 | 全局 grep 确认零残留引用：`grep -r "infox_renderer" scripts/` |
| handler 通过回调传递，未来扩展需改两处 | Change 3 会将 handler 移入共享库，届时消除回调模式 |
