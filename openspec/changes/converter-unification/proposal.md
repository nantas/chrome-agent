# Proposal

## 问题定义

两个 HTML→Markdown 转换器在仓库中独立存在且零代码共享：

| | Pipeline 路径 | Explore 路径 |
|---|---|---|
| **文件** | `converters/html_to_markdown.py` | `explore/sample_converter.py` |
| **解析器** | selectolax | BeautifulSoup |
| **转换方式** | 自定义渲染器 | markdownify 库 + 200+ 行预处理 |
| **配置消费** | 部分读取 extraction.*（本次 change 修复后） | 完整读取 extraction.* |
| **维护成本** | 双倍——修 bug 要改两个文件，加功能要改两个文件 |

前一个 change（`fix-pipeline-quality-gaps`）修复了 infobox 表格渲染等具体 bug，使两条路径的质量可比。但架构层面的重复没有消除：每次修改都需要在两处同步。Architecture Gate 需要同时校验两个文件，`partial_coverage` 的 warning 本身就在提醒"代码重复"这个问题。

本次 change 的目标：消除探索路径的独立转换逻辑，使其委托给 pipeline 路径的 `HtmlToMarkdownConverter`，最终将渲染引擎收敛为一个。

## 范围边界

**范围内：**
- 将 `_render_infobox_table()` 的 infobox 渲染逻辑提取为共享模块
- 修正 explore 路径的 sample_converter.py 委托给 HtmlToMarkdownConverter
- 更新 Architecture Gate 为单文件校验
- 清理 markdownify 依赖（如不再需要）
- 修复 Basement 页面的 `****` 空标签渲染 bug

**范围外：**
- 不替换 selectolax 为 BeautifulSoup（保留当前解析器选择）
- 不重写 `HtmlToMarkdownConverter` 的全部渲染逻辑
- 不改动 Phase B/Phase C 的管线结构
- 不修改 explore 路径的页面获取逻辑（probe_chain、API discovery 等）

## Capabilities

### New Capabilities

- `shared-infobox-renderer`: 将 `<aside class="portable-infobox">` 的表格渲染逻辑提取为独立模块，两个 converter 共享相同代码

### Modified Capabilities

- `pipeline-converters`: `HtmlToMarkdownConverter` 增加公共 API 入口供外部调用；修复 Basement 空标签 bug
- `explore-architecture-gate`: `_PIPELINE_FILES` 缩减为单一文件，不再需要 partial_coverage 跟踪

## Capabilities 待确认项

- [x] 能力清单已与用户确认：explore 阶段已讨论统一方案，用户同意以 HtmlToMarkdownConverter 为基础

## Impact

| 影响维度 | 详情 |
|---------|------|
| sample_converter.py | 标记 `_apply_extraction()` 和 `_extract_infobox()` 为 deprecated；内部委托给 HtmlToMarkdownConverter |
| Architecture Gate | `_PIPELINE_FILES` 从 2 个减为 1 个；去掉 partial_coverage 跟踪逻辑 |
| 依赖 | 如 sample_converter.py 不再使用 markdownify，可移除 `scripts/explore/requirements.txt` 中的 `markdownify` 和 `beautifulsoup4` |
| 行为 | explore 路径的输出格式会变化（label 加粗、alt 文本为 `image`、链接格式统一）——与前一个 change 的验证结果一致 |
| 向后兼容 | explore CLI（`sample_converter.py` 的 `apply`/`fetch-and-apply` 子命令）保持相同参数签名 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：
  - `openspec/specs/pipeline-converters/spec.md`
  - `openspec/specs/explore-architecture-gate/spec.md`
  - `openspec/specs/markdown-conversion-pipeline/spec.md`
- 已确认项目页：
  - `openspec/changes/fix-pipeline-quality-gaps/verification.md` — 两条路径质量对比证据
  - `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - `scripts/explore/sample_converter.py`
