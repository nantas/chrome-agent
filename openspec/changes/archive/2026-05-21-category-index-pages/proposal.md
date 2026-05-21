# Proposal

## 问题定义

MediaWiki 的 `Category:` 命名空间页面被提取管线当作普通内容页抓取，但这些页面的正文为空——分类列表由 MediaWiki 动态渲染，不包含在 wikitext 正文中。当前输出结果（如 `modes/index.md`）只有 frontmatter 和空标题，无实际内容。

期望行为：`Category:` 页面应被转换为该分类下所有子页面的索引列表，作为目录页输出。

## 范围边界

**In scope:**
- 检测 `Category:` 命名空间的页面（通过 URL 或 frontmatter `title` 字段中的 `Category:` 前缀）
- 从 Category 页面提取子页面链接列表（或从已有提取结果中按分类聚合）
- 将 Category 页面输出为简单索引：frontmatter + 标题 + 子页面列表（无额外格式）

**Out of scope:**
- 不修改 MediaWiki API 管线的页面发现逻辑
- 不改变内容页（非 Category 页面）的提取行为
- 不引入分类层级遍历（子分类递归）

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `category-index-renderer`: 在内容转换阶段识别 Category 命名空间页面，将其渲染为分类索引（列出该分类下所有已知子页面），替代当前的空页面输出

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

- **提取输出**：所有 `Category:` 页面的输出从空内容变为有意义的索引列表
- **下游消费**：使用提取结果的系统可获得完整的分类-页面映射
- **向后兼容**：不影响现有非 Category 页面的输出格式
- **性能**：无显著影响，索引生成仅在已有提取结果上进行

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/` 现有提取能力规范
  - 项目页：`docs/architecture/05-converter-architecture.md`、`docs/architecture/02-pipeline-flow.md`
  - 回写目标：无（纯代码行为修复）
