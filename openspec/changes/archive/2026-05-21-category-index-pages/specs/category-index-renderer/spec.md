# Spec: category-index-renderer

> 修改既有提取管线的 Category 页面处理行为

## MODIFIED Requirements

### Requirement: category-page-detection

提取引擎 SHALL 在输出组装阶段（Phase C assemble）检测页面是否属于 MediaWiki 的 Category 命名空间。

检测依据：manifest 中页面的 `ns` 字段为 `14`（MediaWiki Category 命名空间编号）。Namespace 分类由上游 discovery phase 完成，assemble phase 直接使用 manifest 元数据。

#### Scenario: manifest-ns-detection

- Given manifest 中某页面 `ns` 字段为 `14`，`title` 为 `Category:Modes`
- When assemble phase 遍历 manifest 页面
- Then 引擎 SHALL 识别此为 Category 页面并进入索引渲染流程

#### Scenario: non-category-page-skipped

- Given manifest 中某页面 `ns` 字段为 `0`（主命名空间）
- When assemble phase 遍历 manifest 页面
- Then 引擎 SHALL NOT 对该页面执行 Category 索引渲染流程

### Requirement: category-index-generation

当检测到 Category 页面时，提取引擎 SHALL 生成一个索引页面，列出该分类下所有已提取的子页面。

索引输出格式：
```markdown
---
title: "Category:<Name>"
source_url: "<original_url>"
---
# Category:<Name>

- [Page Title 1](relative/path/to/Page_Title_1.md)
- [Page Title 2](relative/path/to/Page_Title_2.md)
```

规则：
- 列表项 SHALL 使用相对路径链接到对应的已提取 Markdown 文件
- 列表顺序 SHALL 按页面标题字母排序
- 若某子页面提取失败或不存在对应 `.md` 文件，该条目 SHALL 仍出现在列表中，但链接指向原始 wiki URL
- 索引内容 SHALL 仅包含子页面列表，不包含额外格式、描述或分类层级信息

#### Scenario: normal-category-page

- Given Category 页面 `Category:Modes` 包含子页面 `Daily_Challenges` 和 `Greed_Mode`
- And 这两个子页面已成功提取为 `modes/Daily_Challenges.md` 和 `modes/Greed_Mode.md`
- When 引擎生成索引
- Then 输出的 `modes/index.md` SHALL 包含指向这两个文件的相对路径链接列表

#### Scenario: missing-child-page

- Given Category 页面 `Category:Modes` 包含子页面 `Daily_Challenges` 和 `Greed_Mode`
- And `Daily_Challenges.md` 已存在，但 `Greed_Mode.md` 提取失败
- When 引擎生成索引
- Then `Daily_Challenges` 条目 SHALL 使用相对路径链接
- And `Greed_Mode` 条目 SHALL 使用原始 wiki URL 链接

#### Scenario: empty-category

- Given Category 页面 `Category:Empty` 下无任何已提取子页面
- When 引擎生成索引
- Then 输出的索引页 SHALL 仅包含 frontmatter 和标题，列表为空

### Requirement: category-children-discovery

提取引擎 SHALL 通过以下途径发现 Category 页面的子页面列表，按优先级尝试：

1. **API-based discovery**（首选）：使用 MediaWiki API `action=query&list=categorymembers` 查询，当 API 客户端可用时 MUST 使用此途径
2. **Manifest-based fallback**（降级）：当 API 客户端不可用、API 调用失败或返回空结果时，从 manifest 中聚合同 `target_directory` 下的所有非 `ns==14` 页面

#### Scenario: api-based-discovery

- Given API 客户端可用（`client is not None`）
- And `categorymembers` API 返回 `Daily_Challenges` 和 `Greed_Mode`
- When 引擎发现子页面
- Then 引擎 SHALL 使用 API 返回的成员列表

#### Scenario: fallback-to-manifest-aggregation

- Given API 客户端不可用（`client is None`）
- And manifest 中 `target_directory` 为 `modes` 的非 Category 页面包括 `Daily_Challenges`
- When 引擎发现子页面
- Then 引擎 SHALL 从 manifest 中聚合这些页面作为成员列表

#### Scenario: api-returns-empty

- Given API 客户端可用但 `categorymembers` 返回空结果
- And manifest 中 `target_directory` 为 `modes` 的非 Category 页面包括 `Daily_Challenges`
- When 引擎发现子页面
- Then 引擎 SHALL 回退到 manifest 聚合

### Requirement: non-category-pages-unchanged

提取引擎 SHALL NOT 修改非 `Category:` 命名空间页面的处理逻辑。所有内容页的提取、转换和输出行为 MUST 保持不变。

#### Scenario: regular-content-page

- Given 页面为普通内容页（非 Category 命名空间）
- When 提取引擎处理该页面
- Then 行为 SHALL 与引入此变更前完全一致
