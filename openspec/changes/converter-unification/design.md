# Design

## Context

两条 HTML→Markdown 转换路径在仓库中独立存在、零代码共享。前一个 change（`fix-pipeline-quality-gaps`）修复了 infobox 表格渲染、NoneType 安全等问题，使两条路径的质量可比。但架构层面的重复未消除：

- `_render_infobox_table()` 的逻辑在 `html_to_markdown.py` 中内联
- `_extract_infobox()` 在 `sample_converter.py` 中有独立的实现
- Architecture Gate 需要同时校验两个文件
- 修 bug 和加功能都需要两处同步

本 change 通过三步推进：提取共享模块 → explore 路径委托 → Gate 简化。

## Goals / Non-Goals

**Goals:**
- 将 infobox 表格渲染逻辑提取为 `converters/infox_renderer.py` 共享模块
- 修复 Basement 页面 `****` 空标签 bug
- `sample_converter.py` 的 HTML→MD 转换委托给 `HtmlToMarkdownConverter`
- 移除 `markdownify` 依赖（不再被调用）
- Architecture Gate 从双文件校验回退为单文件校验
- 清理 `_detect_dead_config_dual()` 和 `partial_coverage` 跟踪逻辑

**Non-Goals:**
- 不替换 selectolax 为 BeautifulSoup
- 不重写 `HtmlToMarkdownConverter` 的全部渲染逻辑
- 不改动 explore 路径的页面获取、self-check、auto-remediation 等非转换逻辑
- 不修改 `_pipeline_legacy.py` 这类已删除的死代码

## Decisions

### D1: infobox_renderer.py 放在 converters/ 子包中

**Decision**: 共享模块 `infox_renderer.py` 放在 `scripts/mediawiki-api-extract/converters/` 下，与 `html_to_markdown.py` 同层级。

**Rationale**: `converters/` 子包是 pipeline 路径的内部包，所有转换器都在这里。`sample_converter.py` 通过相对路径 import 即可使用。不创建新包层级，不引入外部依赖。

### D2: sample_converter 保留 _apply_extraction() 整体结构，仅替换转换步骤

**Decision**: `sample_converter.py` 的 `_apply_extraction()` 保留其预处理逻辑（HTML 清理、lazyload 修复、decompose 操作等），仅在最终调用 `markdownify.markdownify()` 的地方替换为 `HtmlToMarkdownConverter.convert_body()`。

**Rationale**: `_apply_extraction()` 的预处理逻辑（BeautifulSoup 操作）是针对 explorer 路径的 HTML 获取方式优化的。完全放弃 BeautifulSoup 需要重写整个预处理链，风险大于收益。渐进式替换更可验证。

### D3: Architecture Gate 回退到单文件但不完全 revert

**Decision**: Architecture Gate 的 `_PIPELINE_FILES` 回退到单文件，移除 `partial_coverage` 跟踪，但保留前一个 change 中引入的 `file_name` 参数化和 `files_checked` 输出字段（为 future-proof 留接口）。

**Rationale**: `partial_coverage` 是双文件时代的产物，现在不需要了。但 `files_checked` 和 `file_name` 参数化是好的模式，保留不删。

### D4: infobox_renderer 函数签名使用 selectolax 节点

**Decision**: 共享模块 `render_infobox_table()` 接受 selectolax `Node` 对象作为第一个参数。

**Rationale**: `HtmlToMarkdownConverter` 已经用 selectolax 解析了 HTML。`sample_converter.py` 调用前也需要用 selectolax 解析需要渲染的部分。两者共享 selectolax 节点类型，不需要兼容 BeautifulSoup。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Explore 路径的输出格式变化 | High | Medium | 格式变化在 verifiation 阶段已展示给用户（label 加粗、alt 文本不同），用户认可 |
| sample_converter 的 self-check 依赖旧格式 | Medium | Medium | Self-check 逻辑（image count、table row matching）可能因格式变化触发 false positive——需要运行一次 explore 确认 |
| markdownify 移除后其它模块依赖它 | Low | Low | 仓库中只有 sample_converter.py 导入 markdownify；全局 grep 确认 |
| 共享模块的 import 路径在 Python 3.9 下失效 | Low | Medium | 使用相对 import + sys.path 设置，与现有模式一致 |
