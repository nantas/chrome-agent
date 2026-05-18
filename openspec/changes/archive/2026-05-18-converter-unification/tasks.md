# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认所有 3 个 capability spec 覆盖范围完整
  - `shared-infobox-renderer` (new) / `pipeline-converters` (modified) / `explore-architecture-gate` (modified)
- [x] 1.2 确认前一 change 的输出可用于本 change 的 baseline 对比

## 2. 核心实现任务

### 2.1 共享 infobox 渲染模块 (specs: shared-infobox-renderer)

- [x] 2.1.1 创建 `scripts/mediawiki-api-extract/converters/infox_renderer.py`
  - 从 `html_to_markdown.py::_render_infobox_table()` 提取完整逻辑
  - 暴露 `render_infobox_table(infobox_node, extraction_config, wiki_domain) -> str`
  - 函数签名使用 selectolax Node 作为节点类型
  - 修复 Basement 空标签 bug：label 文本为空时跳过该行
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.converters.infox_renderer import render_infobox_table"` 成功

- [x] 2.1.2 `html_to_markdown.py` 委托给共享模块
  - `_render_infobox_table()` 改为调用 `from .infox_renderer import render_infobox_table`
  - 除节点提取和结果返回外，不包含渲染逻辑
  - 验证: 对 The Sad Onion 执行 `convert_body()`，infobox 输出与之前一致

### 2.2 explore 路径委托 (specs: pipeline-converters)

- [x] 2.2.1 `html_to_markdown.py` 添加公共 API 入口
  - 模块级函数 `def convert_html_to_markdown(html: str, wiki_domain: str, extraction_config: dict | None = None) -> str`
  - 内部实例化 `HtmlToMarkdownConverter` 并调用 `convert_body()`
  - 验证: `convert_html_to_markdown(html, "test.com", {})` 返回 Markdown 字符串

- [x] 2.2.2 `sample_converter.py::_apply_extraction()` 替换转换步骤
  - 在 Phase 5（Content selection → markdownify）处，将 `markdownify.markdownify(str(content), ...)` 替换为 `HtmlToMarkdownConverter.convert_body(str(content), ...)`
  - 保留所有 Phase 1-4 的预处理逻辑（BeautifulSoup 操作、lazyload、cleanup 等）
  - 验证: explore 路径和 crawl 路径对同一页面的输出差异仅在 label 加粗和 alt 文本（已确认可接受）

- [x] 2.2.3 验证转换器替换不影响 self-check
  - 注: self-check 验证依赖实际站点访问，将在 3.1 节统一执行对比验证
  - 对 explore 阶段自检（S1-S12 检查点）运行一次，确认 image count、table row matching 等检查仍通过
  - 如有 false positive，调整 self-check 阈值
  - 验证: explore 流程的自检 summary 不含意外的 false positive

- [x] 2.2.4 清理 markdownify 依赖
  - 确认 `sample_converter.py` 不再导入或调用 `markdownify`
  - 全局 grep `markdownify` 确认仓库中无其他引用
  - 从 `scripts/explore/requirements.txt` 移除 `markdownify`（如无其他依赖）
  - 验证: `python3 -c "import markdownify"` 在非安装环境下应该失败（已移除依赖）

### 2.3 Architecture Gate 简化 (specs: explore-architecture-gate)

- [x] 2.3.1 `_PIPELINE_FILES` 缩减为单文件
  - `_PIPELINE_FILES` 只包含 `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - 移除 `scripts/explore/sample_converter.py` 条目
  - 验证: `architecture_gate.py` 中 `_PIPELINE_FILES` 长度为 1

- [x] 2.3.2 移除 partial_coverage 跟踪
  - `_detect_dead_config_dual()` 替换回 `_detect_dead_config()`（单文件版）
  - 返回值从 `tuple[list[str], list[dict]]` 恢复为 `list[str]`
  - 移除 `partial_coverage` 相关的日志和警告
  - `files_checked` 保留在 gate 输出中（仍报告校验文件列表）
  - 验证: 运行 Architecture Gate → 无 `partial_coverage` 字段，dead_config 是 `list[str]`

## 3. 收敛与验证准备

- [x] 3.1 对 3 个代表性的 BOI 页面执行对比验证
  - The Sad Onion: infobox 正确
  - Basement: `****` 空标签 bug 已修复
  - Items: 大 HTML 表格正确转换（5 tables）
  - The Sad Onion: 验证 infobox 表格正确
  - Basement: 验证 `****` 空标签 bug 已修复
  - Items: 验证大 HTML 表格正确转换
  - 对比两条路径的输出，确认只有 label 加粗和 alt 文本差异

- [x] 3.2 验证 Architecture Gate 单文件校验
  - Gate 报告的 `files_checked` 只包含 `html_to_markdown.py`
  - 无 `partial_coverage` 字段

- [x] 3.3 验证向后兼容性
  - `sample_converter.py` 的 CLI 子命令（apply, fetch-and-apply）参数签名不变
  - Explore 流程的 sample conversion + self-check 完成正常

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行回写:
  - 更新 `html_to_markdown.py`、`sample_converter.py`、`architecture_gate.py` 的状态
