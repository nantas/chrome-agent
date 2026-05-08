# Design

## Context

Change 1 (`mediawiki-api-strategy-composition`) 已冻结 5 个策略接口（Protocol）和默认实现。Change 2 在这些接口上新增 5 个 StS2 专用策略实现、L6 验证层、跨 namespace 发现与输出支持。

当前默认实现（`AllPagesDiscoveryStrategy`, `WikitextOnlyAcquisitionStrategy`, `ExactTitleLinkResolver`, `SimpleSubstitutionTemplateProcessor`, `FrontmatterDrivenListPageAssembler`）基于 balatro 场景，假设：wikitext 自包含所有内容、wiki 内链使用完整标题、单 namespace 封闭发现。这些假设全部与 slaythespire.wiki.gg (ns=3000) 冲突。

StS2 场景的结构性差异：
- 自定义命名空间 ns=3000，大量页面标题格式为 `Slay the Spire 2:PageName`
- wiki 内链使用短名（`[[Bash]]` 而非 `[[Slay the Spire 2:Bash]]`）
- 跨 namespace 引用（StS2 页面引用 StS1 ns=0 内容）
- DRUID infobox 图片和 DPL 动态表格只在渲染后 HTML 中存在
- 多参数结构化模板（含 Lua 调用）

## Goals / Non-Goals

**Goals:**

1. 实现 `CategoryMembersDiscoveryStrategy`：基于 `list=categorymembers` + `cmnamespace` 过滤的页面发现，同时支持 ns=0 和 ns=3000
2. 实现 `HybridAcquisitionStrategy`：检测 `#invoke`/`#dpl` 后自动补充 `prop=text` 和 `prop=images`
3. 实现 `ShortNameLinkResolver`：短名索引 + 平衡括号解析器 + `os.path.relpath` + 跨 namespace 解析
4. 实现 `StructuredTemplateProcessor`：多参数模板展开（位置参数 + 命名参数）+ Lua 感知
5. 实现 `HybridListPageAssembler`：优先从渲染 HTML 提取表格，frontmatter 作为 fallback
6. 实现 L6 验证层：`validate_links()` + `validate_content_integrity()` + `validate_images()`，管线自动运行 + `--validate` 独立命令
7. 支持跨 namespace 输出目录结构：`StS2/` / `StS1/` 顶层目录，文件名剥离 namespace 前缀
8. 更新 StS2 策略文件 `content_profile` 和 `template_map`
9. balatro 回归验证通过（默认策略输出不变）

**Non-Goals:**

- 不修改 Change 1 冻结的 5 个 Protocol 接口签名
- 不修改 balatro 策略文件的默认行为
- 不新增 CLI 子命令（只扩展 `--validate` flag）
- 不实现 Change 3 的 `ContentProfileDetector` 自动探测
- 不解决非 StS2 特有的问题（如通用 MW 表格语法覆盖）

## Decisions

### 1. 跨 namespace 发现：独立调用 + 统一 manifest

**方案 A（选择）**: `CategoryMembersDiscoveryStrategy.discover_pages()` 对每个目标 namespace 独立调用 `categorymembers`，然后将结果合并为一个统一 manifest。每个 page dict 增加 `namespace` 字段。

**方案 B（放弃）**: 使用 `list=allpages` 一次获取所有 namespace。放弃原因：`allpages` 无法利用 StS2 已知的分类结构，且 `apnamespace` 只支持单个 namespace。

### 2. 目录结构：namespace 作为顶层目录

**方案 A（选择）**: 输出目录顶层为 `StS2/` / `StS1/`，内部按分类组织。文件名剥离 namespace 前缀。链接解析时从 manifest 读取 `namespace` 字段计算跨目录相对路径。

**方案 B（放弃）**: 混合目录 + 前缀文件名。放弃原因：结构不清晰，后续整理困难，且与用户明确要求"文件夹结构反映 wiki 组织结构"冲突。

### 3. 短名索引构建时机

**方案 A（选择）**: `ShortNameLinkResolver` 在 `__init__` 中接收完整 manifest，构建 `short_title_index`（`{short_name: full_title}`）。解析时先查 exact match，再查 short index，再查 namespace-prefixed match。

**方案 B（放弃）**: 每次 `resolve()` 调用时实时计算。放弃原因：O(n) 每次查询效率低，且 manifest 在 Phase B 前已完全确定。

### 4. 平衡括号解析器实现

**方案 A（选择）**: 栈式平衡括号算法（来自 postmortem 文档的 `extract_markdown_links`），替代贪婪正则 `\[([^\]]+)\]\(([^)]+)\)`。

**方案 B（放弃）**: 更复杂的正则（如递归正则或平衡组）。放弃原因：Python `re` 模块不支持递归正则；栈式算法简单可靠且已在 postmortem 中验证。

### 5. HybridAcquisitionStrategy 的多源返回结构

**方案 A（选择）**: `fetch_page_content()` 返回 `dict` 包含 `wikitext`, `rendered_html`, `images` 字段。Phase B 的 `process_single_page()` 根据可用字段决定下游处理。

**方案 B（放弃）**: 定义 `PageContent` dataclass。放弃原因：当前代码使用纯 dict，引入 dataclass 会改变 Change 1 的接口契约（虽然 Protocol 签名允许，但保持 dict 更轻量）。

### 6. L6 验证层执行时机

**方案 A（选择）**: Phase C 结束后自动运行 L6 扫描器，同时支持 `--validate` 独立命令跳过 A/B/C 直接扫描已有输出。

**方案 B（放弃）**: 只在 `--validate` 时运行，默认不运行。放弃原因：用户要求"管线内工作流会自动运行"，且自动运行能在问题发生时立即暴露。

### 7. L6 扫描器失败策略

**方案 A（选择）**: Soft fail（记录警告到 `validation_report.json`，不中断管线）。

**方案 B（放弃）**: Hard fail（验证不通过则管线退出并返回错误码）。放弃原因：某些问题可能是预期行为（如外部链接、已删除页面），不应阻断整个爬取流程。

### 8. 表格转换的处理

`convert_wikitable_to_markdown` 保持为 `strategies.py` 中的模块级函数（非策略接口）。在 Change 2 中完善其实现（`!` 表头独立行识别、`!!` 多单元格分隔符），但不抽象为独立策略接口。理由：表格转换是纯机械操作，不因站点而异。

### 9. StS2 策略文件的 template_map 扩展

`template_map` 扩展基于实际 wikitext 采样确定，不在 design 阶段精确枚举。实现时从样本页面（如 `Bash`, `Strike`, `J.A.X.`）提取高频模板，然后补充到策略文件。

## Risks / Migration

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **短名冲突** | 不同 namespace 中可能存在同名短名（如 ns=0 和 ns=3000 都有 `Bash`） | `ShortNameLinkResolver` 优先解析到同 namespace 的短名，跨 namespace 只在显式配置时启用 |
| **跨 namespace 路径计算错误** | `../../StS1/...` 类相对路径在深层目录中可能计算错误 | 使用 `os.path.relpath` 进行精确计算，L6 链接扫描器验证 |
| **HybridAcquisitionStrategy API 调用翻倍** | 对含 `#invoke` 的页面需要 2-3 次 API 调用（wikitext + text + images） | 只在检测到动态内容时才补充请求；对静态页面保持单次请求；并发控制不变 |
| **CategoryMembersDiscoveryStrategy 分类遗漏** | 如果 `page_categories` 映射不完整，某些页面可能未被任何 category 覆盖 | 提供 `allpages` fallback 机制；L6 内容完整性检查捕获空目录 |
| **balatro 回归验证依赖网络** | 基线生成需要 balatro API 可用 | 执行前检查；如果 API 不可用，使用 Change 1 归档的已知好基线 |
| **L6 扫描器性能** | 对 1000+ 页面的输出目录进行全量扫描可能耗时 | 扫描器使用惰性加载和批量查询；imageinfo 查询每批 50 个文件 |
| **文件名冲突** | 同一分类下 ns=0 和 ns=3000 可能有同名页面（如 `Bash`） | 按 namespace 分顶层目录已隔离；manifest 中保留完整标题含 namespace |
