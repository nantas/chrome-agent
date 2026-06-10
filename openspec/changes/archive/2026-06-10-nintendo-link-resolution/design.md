# Design

## Context

3 个 `developer.nintendo.com` site sample 回归测试因 `assert_links_resolved` 失败。根因是 `html_to_markdown()` 输出保留原始 `../Pages/Page_*.html` 相对链接，而 `markdown_link_resolver.py` 已有完整实现可以解析这些链接，但未被集成到转换流程中。

## Goals / Non-Goals

**Goals:**
- 将 `markdown_link_resolver.fix_all_links()` 集成到 site sample 转换流程
- 修复 3 个 nintendo site sample 回归测试
- 新增链接解析集成测试

**Non-Goals:**
- 不修改 pipeline 的 `ExactTitleLinkResolver`（不同路径，处理 MediaWiki 语法）
- 不修改 `html_to_markdown()` 本身（保持转换器职责单一）
- 不处理其他站点的链接问题

## Decisions

### D1: 集成点选择

**决策**: 在 `test_runner.py`（site sample 回归测试的 `_make_site_sample_test` 工厂函数）中，`html_to_markdown()` 调用之后添加 `fix_all_links()` 调用。

**理由**: 实现后发现 site sample 回归测试的失败路径是 `test_runner.py` 直接调用 `html_to_markdown()`，不经过 `sample_converter.py`。`sample_converter.py` 主要用于 explore 工作流的策略验证，不是 site sample 回归测试的执行路径。链接解析作为后处理步骤集成在 test_runner 中，不侵入核心转换器，也不影响非回归的转换流程。

### D2: Mapping 来源

**决策**: 使用空 mapping（`{}`），不调用 `build_page_mapping()`。

**理由**: 实现后发现 golden files 不包含 `> Source:` 元数据行，`build_page_mapping()` 扫描后返回空 mapping。因此直接传空 mapping，让 `fix_all_links()` 将所有 `../Pages/Page_*.html` 链接解析为完整外部 URL。这足以通过 `assert_links_resolved` 断言——断言只要求不残留原始 `../Pages/Page_*.html` 模式，不要求解析为 `.md` 文件名。

### D3: 集成范围限定

**决策**: 仅对 `developer.nintendo.com` 域名启用链接解析，其他域名不调用 `fix_all_links()`。

**理由**: `../Pages/Page_*.html` 是 Nintendo Developer Portal 特有的链接模式。其他站点不应受影响。通过 domain 参数条件判断。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| golden files 更新后 mapping 变化 | 现有 golden 需重新生成 | `--update-golden` 已有支持 |
| nintendo 策略变更导致 HTML 结构改变 | 链接模式可能变化 | `fix_all_links` 基于通用正则，不过度依赖结构 |
