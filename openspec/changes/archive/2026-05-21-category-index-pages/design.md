# Design

## Context

`scripts/pipeline/pipeline/phases/assemble.py` 已有 Category 页面索引生成逻辑（~L58-135），通过 MediaWiki API `categorymembers` 端点获取分类成员并写入 `index.md`。但在 v3 基线测试中，`modes/index.md`（来自 `Category:Modes`）仍输出为空页面——仅有 frontmatter 和标题。

根因分析：Phase B（HTML→Markdown 转换）将 Category 页面当作普通内容页处理，输出包含 `# Category:Modes` 标题的空 Markdown。Phase C 的 category index 生成代码依赖 `client`（MediaWiki API 客户端），当 `client is None` 时整个 category 块被跳过，Phase B 的空输出被直接写入磁盘且不被覆盖。

用户需求：Category 页面应作为简单索引，列出该分类下所有子页面，不需要额外格式。

## Goals / Non-Goals

**Goals:**
- Category 页面始终生成有意义的索引内容，不依赖 MediaWiki API 客户端是否可用
- 索引格式简单：frontmatter + 标题 + 子页面列表（无额外格式）
- 利用管线已积累的 manifest 数据（`pages` 数组中每页的 `target_directory` 归属）聚合分类成员，作为 API 调用的 fallback 或替代

**Non-Goals:**
- 不引入新的 MediaWiki API 调用
- 不改变内容页的提取行为
- 不处理子分类递归
- 不改变 Phase B converter 对 Category 页面的处理（它仍会生成空内容，由 Phase C 覆盖）

## Decisions

### D1: Phase C assemble 中增加 manifest-based fallback

在现有 API-based category index 生成之后，增加一个 fallback 路径：遍历 manifest 中 `target_directory` 与 category 页面相同的所有非 Category 页面，生成索引列表。

逻辑：
1. 对每个 `ns == 14` 的 manifest 页面，先尝试 API 方式（现有逻辑）
2. 若 `client is None` 或 API 调用失败或返回空结果，则从 manifest 聚合
3. manifest 聚合：找到所有 `target_directory` 与该 Category 页面相同的 manifest 条目，按标题排序，生成链接列表

### D2: 简化索引格式

Category 索引输出格式：

```markdown
---
title: "Category:<Name>"
source_url: "<original_url>"
---
# Category:<Name>

- [Page Title 1](filename.md)
- [Page Title 2](filename.md)
```

不加 `## Pages` 等子标题，不加描述段落，仅保留简单列表。

### D3: 覆盖 Phase B 输出

Phase C assemble 的 Category 索引写入使用 `w` 模式（覆盖），这已与现有代码一致。关键变更是确保 Category 索引**始终被生成**，即使 API 客户端不可用。

## Risks / Migration

- **Risk**: manifest 中 `target_directory` 可能不完全对应 MediaWiki 的 Category 归属（manifest 的目录分配来自 discovery 阶段的分类逻辑，可能包含手动分配）
  - **Mitigation**: 这是已有行为——discovery 阶段已基于 Category 归属分配目录，manifest 数据可信
- **Risk**: API-based 和 manifest-based 两种路径可能产生不同结果
  - **Mitigation**: manifest-based 仅在 API 不可用或返回空时作为 fallback
- **Migration**: 无需迁移，这是对空页面输出的修复
