# Proposal

## 问题定义

100 页端到端测试（`tests/e2e/boi-100-baseline.sh`）暴露了 `fix-pipeline-quality-gaps` change 未覆盖的 7 个结构性缺陷。这些缺陷分为两类：

**核心管线缺陷（P0-P3）**：
1. **List page 目录分配 Bug**：`_build_homepage_manifest()` 中所有 list page 的 `target_directory` 全部为 `"items"`，导致 Bosses/Characters/Monsters 等分类页的 index.md 写入错误目录
2. **Exclude 不彻底 + Assembly 覆盖**：排除的 Version History 页面通过 `source_category: "Items"` 漏入 manifest，分配到 `items/` 目录后被 assembly 的 list_page 处理逻辑覆盖写入 `items/index.md`
3. **Assembly 生成孤儿 index**：`taxonomy.list_pages` 中 Mechanics/Cards 等条目对应的页面未被 homepage discovery 发现，但 assembly 仍为它们创建了空壳 index.md
4. **括号文件名 Markdown 冲突**：106 处 broken link 因文件名中 `)` 被 Markdown 链接语法解析为结束符而断裂

**转换器质量缺陷（P4-P5）**：
5. **YouTube "Load video" 残留**：oEmbed fallback HTML 未被清理，页面底部出现 UI 控件文本
6. **首图选择错误**：frontmatter `image` 字段取了装饰图标（Font_TeamMeat）而非实际物品图

## 范围边界

**范围内**：
- 修复 `_build_homepage_manifest()` 中 category 到 directory 的映射逻辑
- 修复 `orchestrator.py` 排除过滤逻辑（支持按页面标题匹配 + 增强 source_category 检查）
- 修复 `assemble.py`：list_page 处理前检查 manifest 存在性；index.md 写入防覆盖保护
- 修复 `link_fixer.py`：括号文件名 URL-encode 处理
- 修复 `converter.py`：clean_html 中清理 YouTube fallback 文本；frontmatter image 应用 skip_patterns 过滤
- 更新 `fix-pipeline-quality-gaps` 中已修改但未覆盖本问题的 spec delta

**范围外**：
- 不修改 `sample_converter.py`（explore 路径）
- 不处理 Unavailable images（P7 — wiki 服务端资源问题）
- 不统一 `fix-pipeline-quality-gaps` 与本次修改的 spec 文件（另开 spec delta）
- 不修改 `page_assigner.py` 的核心分类算法

## Capabilities

### New Capabilities

（无新增能力——全部为既有能力的修正与加固）

### Modified Capabilities

- `homepage-driven-discovery`：修复 `_build_homepage_manifest()` 中 list page 目录分配映射错误；增强 exclude_categories 过滤逻辑（按页面标题匹配 + 避免被 source_category 别名穿透）
- `mediawiki-api-extraction-pipeline`：修复 `assemble.py` 中孤儿 index 生成问题（跳过 manifest 中不存在的 list_page 条目）；添加 index.md 写入防覆盖保护（仅处理 `is_list_page=true` 的页面）
- `pipeline-converters`：修复 `link_fixer.py` 中括号文件名 URL-encode；修复 `converter.py` 中 YouTube "Load video" 残留清理；修复 frontmatter `image` 字段应用 skip_patterns 过滤
- `pipeline-registry`：与 assemble 的孤儿保护联动——确保 `taxonomy.list_pages` 条目与发现到的页面对齐

## Capabilities 待确认项

- [x] 能力清单已与用户确认：测试结果讨论中已明确所有能力边界

## Impact

| 影响维度 | 详情 |
|---------|------|
| 管线行为 | homepage discovery 的 list page 目录正确分配；assembly 不再生成孤儿 index；排除过滤更加严格 |
| 输出质量 | 括号文件名链接正确生成；YouTube 残留消失；frontmatter image 选择正确 |
| 向后兼容 | 无 API 变更；CLI 接口不变；策略 schema 不变（排除逻辑增强，schema 兼容） |
| 验证 | 通过已建立的 `tests/e2e/boi-100-baseline.sh` 基线对比验证 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `openspec/specs/pipeline/pipeline-discovery.md`
  - `openspec/specs/pipeline/pipeline-core.md`
  - `openspec/specs/pipeline/pipeline-conversion.md`
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`
