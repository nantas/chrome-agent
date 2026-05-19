# Proposal

## 问题定义

explore 路径的 `sample_converter.py` 和 pipeline 路径的 `html_to_markdown.py` 各有独立的 infobox 提取和 HTML 预处理实现，形成双实现分裂（Dual Implementation 模式）：

1. **Infobox 提取**：`_extract_infobox()`（BS4, 119行）与 `infox_renderer.render_infobox_table()`（selectolax, 136行）功能重复但实现完全独立，handler 查找逻辑和默认值不一致
2. **HTML 预处理**：`_apply_extraction()` Phase 1-4（BS4, 128行）与 `clean_html()`（selectolax, 25行）职责重叠但功能集差异大
3. **策略 YAML 解析**：`_load_extraction_rules()` 仍有独立的 frontmatter 解析（Change 1 已创建 `lib/strategy_loader.py` 但未替换此调用方）

后果：对 infobox 渲染的任何改进都需要同步更新两处代码，Architecture Gate 只校验 pipeline 侧，explore 侧的 infobox 变化无法被检测。

## 范围边界

### 包含

- 新建 `lib/extraction/infobox.py`：统一 infobox 提取，支持 BS4 + selectolax 双解析器
- 新建 `lib/extraction/preprocessor.py`：统一 explore 路径的 HTML 预处理
- `sample_converter.py`：`_apply_extraction()` 改为 4 步顺序调用 `lib/extraction/`
- `infox_renderer.py`：删除，`html_to_markdown.py` 直接导入 `lib.extraction.infobox`
- `html_to_markdown.py`：`_render_infobox_table()` 改为调用 `lib.extraction.infobox.extract_infobox()`
- `sample_converter._load_extraction_rules()`：改用 `lib.strategy_loader`

### 不包含

- `html_to_markdown.py` 文件移动到 `lib/extraction/converter.py` → Change 3（随包重命名一次完成）
- `clean_html()` 统一 → Change 2 不改动（selectolax 紧耦合）
- handler 实现从 `html_to_markdown.py` 移出 → Change 3（紧耦合于当前类）
- orchestrator 拆分 / 包重命名 → Change 3
- Phase 文件重命名 → Change 4

## Capabilities

### New Capabilities

- `unified-infobox-extraction`: 统一 infobox 提取引擎，支持 BeautifulSoup 和 selectolax 双解析器，配置驱动选择器和 handler，替换 `_extract_infobox()` 和 `infox_renderer.render_infobox_table()`
- `unified-html-preprocessing`: 统一 explore 路径的 HTML 预处理（infobox 移除、cleanup_selectors 剥离、lazyload 修复、cleanup 操作列表、内容选择），替换 `_apply_extraction()` Phase 1-4

### Modified Capabilities

- `sample-converter`: `_apply_extraction()` 重写为 4 步顺序调用共享库，删除 `_extract_infobox()`、`_apply_field_handler()`、`_load_extraction_rules()` 三个私有函数
- `pipeline-infobox-rendering`: `html_to_markdown.py` 的 `_render_infobox_table()` 改为调用 `lib.extraction.infobox.extract_infobox()`，删除 `infox_renderer.py`

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 文件 | 操作 | 风险 |
|------|------|------|
| `scripts/lib/extraction/infobox.py` | 新建 | 中（合并两套渲染逻辑） |
| `scripts/lib/extraction/preprocessor.py` | 新建 | 中（合并预处理逻辑） |
| `scripts/explore/sample_converter.py` | 修改 | 中（核心函数重写） |
| `scripts/mediawiki-api-extract/converters/infox_renderer.py` | 删除 | 低（仅 1 个调用方） |
| `scripts/mediawiki-api-extract/converters/html_to_markdown.py` | 修改 | 低（仅改 import 和 `_render_infobox_table`） |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：`docs/plans/2026-05-19-structure-refactor-and-docs.md`（Change 2 状态回写）
