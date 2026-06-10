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

**决策**: 在 `sample_converter.py`（site sample 转换流程）中，`html_to_markdown()` 调用之后添加 `fix_all_links()` 调用。

**理由**: site sample 回归测试走 `sample_converter.py` 路径，不走 pipeline。链接解析是后处理步骤，不应侵入核心转换器。`fix_all_links()` 需要 `build_page_mapping()` 提供 mapping，而 sample converter 有输出目录信息可用。

### D2: Mapping 来源

**决策**: 使用 `build_page_mapping(output_dir)` 扫描已有 `.md` golden files 构建 mapping。

**理由**: nintendo 的 golden files 已包含 `> Source:` 元数据行，`build_page_mapping` 可直接使用。不需要额外的 mapping 文件或配置。

### D3: 集成范围限定

**决策**: 仅对 `developer.nintendo.com` 域名启用链接解析，其他域名不调用 `fix_all_links()`。

**理由**: `../Pages/Page_*.html` 是 Nintendo Developer Portal 特有的链接模式。其他站点不应受影响。通过 domain 参数条件判断。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| golden files 更新后 mapping 变化 | 现有 golden 需重新生成 | `--update-golden` 已有支持 |
| nintendo 策略变更导致 HTML 结构改变 | 链接模式可能变化 | `fix_all_links` 基于通用正则，不过度依赖结构 |
