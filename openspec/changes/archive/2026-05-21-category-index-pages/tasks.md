# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `category-page-detection` spec 的实现边界：在 `assemble.py` Phase C 中，已有 `ns == 14` 检测逻辑，验证是否覆盖 URL-based 和 title-based 两种场景
- [x] 1.2 确认 `category-children-discovery` spec 的实现路径：API-based 已实现（`client.query(categorymembers)`），需新增 manifest-based fallback
- [x] 1.3 确认 `category-index-generation` spec 的输出格式：当前 API-based 使用 `## Pages` / `## Subcategories` 子标题，需简化为纯列表

## 2. 核心实现任务

- [x] 2.1 **manifest-based fallback 实现**：在 `assemble.py` 的 category index 生成块中，当 `client is None` 或 API 调用返回空结果时，从 manifest 聚合同 `target_directory` 下的所有非 ns=14 页面，生成索引列表
  - 实现：提取 `_generate_manifest_category_index(title, target_dir, manifest, domain)` 辅助函数
  - 验证：`client=None` 时 Category 页面输出包含子页面列表

- [x] 2.2 **简化索引格式**：移除 `## Pages` / `## Subcategories` 子标题，改为扁平列表。仅保留 frontmatter + `# Category:<Name>` 标题 + 子页面链接列表
  - 实现：修改 assemble.py L115-135 的列表生成逻辑
  - 验证：输出不包含 `## Pages` 等二级标题

- [x] 2.3 **覆盖保证**：确保 Phase C 的 Category 索引写入（覆盖模式）在 Phase B 内容写入之后执行，无论 `client` 是否为 None
  - 实现：将 `if client is not None:` 守卫条件改为始终执行，API 调用部分保留 try/except
  - 验证：`client=None` 时 Category 页面不再输出 Phase B 的空内容

- [x] 2.4 **链接路径正确性**：manifest-based 生成的链接应使用正确的相对路径，同目录下用 `filename.md`，跨目录用 `dir/filename.md`
  - 实现：复用现有 API-based 代码中的路径解析逻辑（L132-143）
  - 验证：链接在 Markdown 渲染中可正确跳转

## 3. 收敛与验证准备

- [x] 3.1 使用 `outputs/test-100-extraction-v3/` 数据作为回归测试基线，验证修改后 `modes/index.md` 包含 `Daily_Challenges` 等子页面链接
- [x] 3.2 确认非 Category 页面（如 `modes/Daily_Challenges.md`）内容未受影响
- [x] 3.3 确认 `client` 可用时 API-based 路径仍然正常工作（不破坏现有功能）

## 4. 验证与回写收敛

- [x] 4.1 基于 v3 基线测试数据运行完整管线，对比修改前后 `modes/index.md` 内容
- [x] 4.2 检查所有 ns=14 页面的输出，确认均已生成索引
- [x] 4.3 无回写目标（本次为纯代码修复），标记 writeback 为 N/A
