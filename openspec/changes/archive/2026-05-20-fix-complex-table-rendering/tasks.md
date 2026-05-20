# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/table-grid-parser/spec.md` 所有 requirements 可映射到 converter.py 中的具体代码改动
- [x] 1.2 确认 `specs/table-transpose-config/spec.md` 的 strategy schema 扩展与 converter 配置读取路径对齐
- [x] 1.3 确认 `specs/pipeline-converters/spec.md` 中 REMOVED Requirements 对应的旧代码位置（`_is_simple_markdown_table` 方法、fallback 分支）
- [x] 1.4 准备单元测试结构：在 `scripts/pipeline/tests/` 下创建 `test_table_grid.py` 测试文件（若 tests 目录不存在则创建）

## 2. 核心实现任务

### 2.1 新增 `_build_table_grid()` 方法

- [x] 2.1.1 在 `HtmlToMarkdownConverter` 类中新增 `_build_table_grid(self, node, source_dir)` 方法
  - **Spec 覆盖**: `table-grid-parser/spec.md` Requirement: build-table-grid-from-html
  - **实现路径**: `scripts/lib/extraction/converter.py`，在 `_render_table()` 之前插入
  - **验证**: 调用 `_render_inline_children()` 渲染单元格；col_spans 字典正确追踪 rowspan；所有行等宽

- [x] 2.1.2 实现 colspan/rowspan 展开逻辑
  - colspan: 在当前行中重复内容 c 次，占用 c 个列位置
  - rowspan: 在 `col_spans[col] = (rowspan - 1, content)` 中注册
  - 每行开始前递减 `col_spans` 中的 remaining_rows，consumed 后删除条目
  - **验证**: 单元测试 — 覆盖 colspan-only、rowspan-only、混合、空表、200 列上限场景

- [x] 2.1.3 实现 max_cols 安全上限（200 列）
  - 动态计算 max_cols，超过 200 时 log warning 并截断
  - **验证**: 构造 201 列的测试表，确认 log 输出且输出为 200 列

### 2.2 新增 `_render_grid_as_table()` 方法

- [x] 2.2.1 在 `HtmlToMarkdownConverter` 类中新增 `_render_grid_as_table(self, grid, header_row_count)` 方法
  - **Spec 覆盖**: `table-grid-parser/spec.md` Requirement: render-grid-as-markdown-table
  - **实现路径**: `scripts/lib/extraction/converter.py`
  - **验证**: 输入 `[["A", "B"], ["1", "2"]]` → 输出 2 行 Markdown 表（header + separator + body）

- [x] 2.2.2 实现 `|` 管道符转义
  - 单元格内容中的 `|` 替换为 `\|`
  - **验证**: 单元测试 — 输入 `["a | b"]` → 输出 `| a \| b |`

### 2.3 新增 `_transpose_grid()` 静态方法

- [x] 2.3.1 在 `HtmlToMarkdownConverter` 类中新增 `_transpose_grid(grid, header_row_count)` 静态方法
  - **Spec 覆盖**: `table-transpose-config/spec.md` Requirement: transpose-grid-method
  - **验证**: 2×3 转置为 3×2；多行表头用 ` → ` 连接

- [x] 2.3.2 实现多行表头合并逻辑
  - 将 grid 前 `header_row_count` 行按列合并（跳过空值，用 ` → ` 连接）
  - 合并后的值作为转置结果的首列（行标签）
  - 原始第一列（数据行标签）作为转置结果的表头
  - **验证**: Characters 表 3 行 header 转置后正确生成 "Rebirth → Isaac → Judas" 等标签

### 2.4 重构 `_render_table()` 方法

- [x] 2.4.1 替换 `_render_table()` 主体逻辑
  - **Spec 覆盖**: `pipeline-converters/spec.md` Requirement: table-rendering-refactored
  - 新流程: `_build_table_grid()` → 检查 transpose 阈值 → 可选 `_transpose_grid()` → `_render_grid_as_table()`
  - 读取 `self.config.get("table_options", {}).get("transpose_wider_than")` 判断是否转置
  - **验证**: 简单表输出不变；复杂表输出为标准 Markdown 表

- [x] 2.4.2 新增 `header_row_count` 检测逻辑
  - 遍历 `<tr>` 节点，计数连续的全 `<th>` 行直到遇到含 `<td>` 的行
  - **验证**: Characters 表 `header_row_count = 3`；简单 `th; td, td` 表 `header_row_count = 1`

### 2.5 删除旧代码

- [x] 2.5.1 删除 `_is_simple_markdown_table()` 方法
  - **Spec 覆盖**: `pipeline-converters/spec.md` Requirement: is-simple-markdown-table-check (REMOVED)
  - **验证**: grep 确认无残留引用

- [x] 2.5.2 删除 `_render_table()` 中的 fallback 分支（`fallback_lines` 列表渲染逻辑）
  - **Spec 覆盖**: `pipeline-converters/spec.md` Requirement: fallback-to-flat-list-rendering (REMOVED)
  - **验证**: 任何表格转换不再产生 `- cell | cell` 格式输出

### 2.6 更新 BOI 策略配置

- [x] 2.6.1 在 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 的 `extraction:` 块中添加 `table_options` 配置
  - **Spec 覆盖**: `table-transpose-config/spec.md` Requirement: boi-characters-strategy-config
  - 新增:
    ```yaml
    table_options:
      transpose_wider_than: 10
    ```
  - **验证**: YAML 语法正确；`parse_strategy()` 能正确解析新字段

### 2.7 单元测试

- [x] 2.7.1 创建 `scripts/pipeline/tests/test_table_grid.py`
  - **验证**: `pytest scripts/pipeline/tests/test_table_grid.py` 全部通过

- [x] 2.7.2 覆盖以下测试场景:
  - 简单 2×2 表（无 colspan/rowspan）→ 标准 Markdown 输出
  - colspan header（`<th colspan="2">`）→ 等宽 2 列 grid
  - rowspan 首列（`<th rowspan="2">`）→ 内容在后续行中重复
  - 混合 colspan + rowspan（Characters 表简化版）→ 等宽 grid
  - 空表 → 空字符串
  - `|` 管道符转义
  - transpose 2×3 → 3×2
  - transpose 多行 header → ` → ` 分隔
  - transpose_wider_than=10: 5 列表不转置，22 列表转置
  - 转置后渲染为标准 Markdown 表

## 3. 收敛与验证准备

- [x] 3.1 运行 `tests/e2e/boi-100-baseline.sh` 全量回归测试
  - 确认 Characters 页面输出为标准 Markdown 表格（不再有 `- cell | cell` 格式）
  - 确认 broken_links / empty_content 指标无退化
  - **验证**: validation_report.json 指标与基线一致或更优

- [x] 3.2 手动检查 `outputs/test-100-fixed/characters/index.md` 输出质量
  - 表格以 `| --- |` 分隔符格式呈现
  - 角色作为行、属性作为列（转置）
  - 表头包含 DLC → 角色 → 子角色层级信息
  - **验证**: 输出可读，无摊平列表

- [x] 3.3 检查其他列表页面（Items、Bosses 等）无回归
  - 随机抽取 5 个非 Characters 页面，确认表格输出不变或改善
  - **验证**: diff 对比重构前后的 md 输出

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
