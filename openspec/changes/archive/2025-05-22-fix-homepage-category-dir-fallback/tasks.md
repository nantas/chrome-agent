# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/homepage-discovery-category-extraction/spec.md` 覆盖 `_build_homepage_manifest()` 的 if/else 两个分支的 cat_dir 回退逻辑
- [x] 1.2 确认 `specs/convert-target-conflict-detection/spec.md` 覆盖 pre-scan 检测、主循环跳过、日志输出三个环节
- [x] 1.3 确认 `specs/isaac-strategy-dir-completeness/spec.md` 覆盖策略文件补全
- [x] 1.4 确认三处修改点无共享可变状态（discovery、convert、strategy 文件互不依赖）

## 2. 核心实现任务

### 2.1 cat_dir 自动回退（`discovery_homepage.py`）

- [x] 2.1.1 在 `_build_homepage_manifest()` 的 `for cat in categories` 循环中，`cat_dir` 解析后增加回退逻辑：
  ```python
  if not cat_dir:
      cat_dir = cat_name.lower().replace(" ", "-")
      log.warning("Category '%s' has no dir mapping in strategy, auto-fallback to '%s'",
                  cat_name, cat_dir)
  ```
  **验证**: 无策略映射的分类名产生正确的目录名（如 "Completion Marks" → "completion-marks"）

- [x] 2.1.2 将 if 分支（第 265 行）的 `if cat_dir:` 条件删除，改为无条件赋值：
  ```python
  assigned_pages[idx]["target_directory"] = cat_dir
  ```
  **验证**: 已有 dir 映射的分类行为不变；无映射的分类 target_directory 被正确更新

- [x] 2.1.3 确认 else 分支（新增 entry）的 `target_directory: cat_dir` 已自动使用回退值（无需额外改动）
  **验证**: 新增分类 entry 的 target_directory 非空

### 2.2 target_path 冲突检测（`convert.py`）

- [x] 2.2.1 在 `run_convert()` 的 redirect pre-scan 之后，增加 target_path 冲突 pre-scan：
  - 构建 `target_path → [page titles]` 映射
  - 发现冲突时（同一 path 有 >1 个页面），保留首个（按 manifest 顺序），其余加入 `conflict_titles` set
  - 对每个冲突路径 emit `log.error` 报告冲突详情
  **验证**: 两个页面指向同一路径时，后者被标记为 conflict

- [x] 2.2.2 在主循环中，redirect 检查之后增加 conflict 检查：
  ```python
  if title in conflict_titles:
      results[title] = {"title": title, "status": "target_conflict"}
      failed_count += 1
      log.error("Skipping '%s': target path conflict", title)
      continue
  ```
  **验证**: 冲突页面被跳过，不写文件，不覆盖已写入的内容

### 2.3 Isaac 策略文件补全（`strategy.md`）

- [x] 2.3.1 在 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 的 `api.homepage.categories` 列表中添加：
  ```yaml
  - {name: "Completion Marks", dir: "completion_marks"}
  - {name: "Attributes", dir: "attributes"}
  ```
  **验证**: 策略加载后 `strategy_cat_dir` 包含这两个映射

### 2.4 测试

- [x] 2.4.1 新增测试: 分类无 dir 映射时自动回退到标准化目录名
  - 输入: categories 含 `{name: "Completion Marks", page_title: "Completion Marks", type: "list_page"}`，strategy 无 dir 映射
  - 断言: manifest 中 "Completion Marks" entry 的 `target_directory == "completion-marks"`, `target_filename == "index.md"`, `is_list_page == True`

- [x] 2.4.2 新增测试: 已有 dir 映射的分类不受自动回退影响
  - 输入: categories 含 `{name: "Items", page_title: "Items"}`, strategy 有 `{name: "Items", dir: "items"}`
  - 断言: `target_directory == "items"`, 无 warning 日志

- [x] 2.4.3 新增测试: target_path 冲突时后续页面被跳过
  - 输入: manifest 含两个 page 指向同一路径 `items/index.md`
  - 断言: 第二个 page 的 result status == "target_conflict", 文件内容为第一个 page 的转换结果

- [x] 2.4.4 新增测试: 无冲突时不产生误报
  - 输入: manifest 含多个 page 指向不同路径
  - 断言: 无 conflict 状态，所有 page 正常转换

- [x] 2.4.5 新增测试: 策略有 dir 映射时优先使用映射值
  - 输入: strategy 有 `{name: "Completion Marks", dir: "completion_marks"}`
  - 断言: `target_directory == "completion_marks"`（非 auto-fallback 的 "completion-marks"）

## 3. 验证

### 3.1 最小验证集（5 个页面，纯内存测试）

用已有的 Isaac wiki `page_manifest.json` 中的 5 个条目构造最小 manifest，调用 `_build_homepage_manifest()` 断言输出：

| 页面 | 验证内容 | 预期 |
|------|----------|------|
| Items | 被覆盖的受害者，策略有 dir 映射 | `items/index.md`，内容正确 |
| Completion Marks | 策略有 dir 映射（补全后） | `completion_marks/index.md`，独立目录 |
| Attributes | 策略有 dir 映射（补全后） | `attributes/index.md`，独立目录 |
| Bosses | 对照：原有 dir 映射不受影响 | `bosses/index.md`，行为不变 |
| Trinkets | 对照：原有 dir 映射不受影响 | `trinkets/index.md`，行为不变 |

不需要网络和文件 I/O，不需要重跑完整管线。

- [x] 3.1.1 构造最小 manifest 输入（从真实 page_manifest.json 提取 5 个页面的数据）
- [x] 3.1.2 调用 `_build_homepage_manifest()` 并断言 5 个页面的 target_path 均正确
- [x] 3.1.3 构造 2 页面同路径的 manifest 片段，调用 `run_convert()` 并断言冲突检测生效
- [x] 3.1.4 运行全部测试：`python3 -m pytest scripts/pipeline/tests/ -v -k "cat_dir_fallback or target_conflict"`

## 4. 收敛与回写

- [x] 4.1 基于真实实现结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行回写目标，记录可审计证据
