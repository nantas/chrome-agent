# Tasks

## 1. 前置验证

- [x] 1.1 Grep 所有策略文件确认 `field_selector` 无 `"tr"` 依赖
  - `grep -r "field_selector" sites/strategies/` — 确认全部为 `"div.pi-data"` 或未设置
  - 如发现 `"tr"` 依赖，需在 `extract_infobox()` 中保留 BS4 模式的 `"tr"` 默认值
  - Spec: `unified-infobox-extraction` / `config-driven-selectors`

- [x] 1.2 Grep 确认 `infox_renderer` 仅有 1 个调用方
  - `grep -r "infox_renderer" scripts/` — 预期仅在 `html_to_markdown.py` 中出现
  - Spec: `pipeline-infobox-rendering` / `infox-renderer-module`

## 2. 核心实现

- [x] 2.1 新建 `scripts/lib/extraction/__init__.py`
  - 空文件或简单 re-export

- [x] 2.2 实现 `scripts/lib/extraction/infobox.py` — `extract_infobox()`
  - 合并 `_extract_infobox()` (BS4) 和 `render_infobox_table()` (selectolax) 的逻辑
  - `parser="auto"` 自动检测输入类型
  - 支持 callback: `render_inline_children_fn`, `apply_handler_fn`
  - 支持 config-driven: `nav_strip_selectors`, `field_selector`, `label_selector`, `value_selector`
  - 双路径 handler 查找: label text → data-source alias
  - `field_selector` 默认值: `"div.pi-data"`
  - `from __future__ import annotations` 用于 Python 3.9 兼容
  - Specs: `unified-infobox-extraction` (全部 7 requirements)

- [x] 2.3 实现 `scripts/lib/extraction/preprocessor.py` — `preprocess_html()`
  - `context="explore"`: 6 步预处理（infobox 移除 → cleanup_selectors → lazyload → cleanup 操作 → 装饰图片移除 → 内容选择）
  - `context="pipeline"`: 占位符，当前不使用
  - 8 种 cleanup 操作全部 config-driven: `strip_fandom_infobox_tables`, `convert_ambox_to_text`, `unwrap_image_wrappers`, `strip_footer`, `strip_edit_links`, `strip_skip_links`, `strip_category_links`, `convert_nested_images`
  - 使用 BeautifulSoup 解析器（explore 路径标准）
  - `from __future__ import annotations` 用于 Python 3.9 兼容
  - Specs: `unified-html-preprocessing` (全部 7 requirements)

- [x] 2.4 重写 `scripts/explore/sample_converter.py` — `_apply_extraction()`
  - 替换为 4 步顺序调用:
    1. `extract_infobox(full_html, config)` → infobox Markdown
    2. `preprocess_html(full_html, config, context="explore")` → cleaned HTML
    3. `convert_html_to_markdown(cleaned_html, domain, config)` → body Markdown
    4. Prepend infobox + body → final Markdown
  - 删除 `_extract_infobox()` 函数
  - 删除 `_apply_field_handler()` 函数
  - 替换 `_load_extraction_rules()` → `lib.strategy_loader.parse_strategy()`
  - 验证: `grep "def _extract_infobox\|def _apply_field_handler" scripts/explore/sample_converter.py` 返回空
  - Specs: `sample-converter` (全部 3 requirements)

- [x] 2.5 修改 `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - `_render_infobox_table()`: import 改为 `from scripts.lib.extraction.infobox import extract_infobox`
  - 调用改为 `extract_infobox(node, self.config, self.wiki_domain, ...)`
  - 保持 callback 参数不变: `render_inline_children_fn=self._render_inline_children`, `apply_handler_fn=self._apply_infobox_handler`
  - 不修改 `clean_html()`
  - 不修改 handler 实现
  - Specs: `pipeline-infobox-rendering` / `render-infobox-table-uses-shared-lib`, `handler-implementation-stays-in-converter`

- [x] 2.6 删除 `scripts/mediawiki-api-extract/converters/infox_renderer.py`
  - 前置: 2.5 已完成（无残留 import）
  - 验证: `grep -r "infox_renderer" scripts/` 返回空
  - Spec: `pipeline-infobox-rendering` / `infox-renderer-module`

## 3. 验证

- [x] 3.1 运行现有测试通过
  - `python3 -m scripts.mediawiki-api-extract --help` — 管线入口正常
  - `python3 scripts/explore/main.py --help` — explore 入口正常
  - `python3 scripts/explore/sample_converter.py apply --help` — 样本转换 CLI 正常
  - `node --test tests/` — Node.js 测试通过

- [x] 3.2 对 BOI 站点样本页面验证 explore 路径产出
  - 使用 `sample_converter.py apply` 对 The Sad Onion 页面执行转换
  - 检查 infobox 表格渲染正确
  - 检查 cleanup 操作生效

- [x] 3.3 对 BOI 站点样本页面验证 pipeline 路径产出
  - 使用 `html_to_markdown.convert_body()` 对同一页面执行转换
  - 检查 infobox 表格渲染与 explore 路径一致
  - 检查 handler 回调正常工作

- [x] 3.4 确认零残留引用
  - `grep -r "_extract_infobox\|_apply_field_handler\|infox_renderer\|_load_extraction_rules" scripts/ --include="*.py"` — 预期仅在 `lib/extraction/` 注释中提及历史
  - `grep "def _extract_infobox\|def _apply_field_handler" scripts/explore/sample_converter.py` — 返回空

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据
