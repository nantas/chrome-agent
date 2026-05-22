# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 范围：`specs/page-assignment/spec.md` 定义的 Step 3.5 fallback requirement — 5 个 scenario
- [x] 1.2 确认依赖前置条件：`fix-boi-config-issues` 的 exact-1-match 逻辑已就位（当前代码已含）

## 2. 核心实现任务

### 2.1 实现 Step 3.5 fallback（spec: page-assignment → source-category-fallback-after-mw）

- [x] 2.1.1 在 `assign_pages()` 中，Step 3 之后、Step 4 之前插入 Step 3.5
  - 文件：`scripts/pipeline/pipeline/page_assigner.py`
  - 位置：`_apply_mw_category_matching(...)` 调用之后、`# Step 4: Default assignment` 之前
  - 逻辑：
    ```python
    # Step 3.5: Source-category first-match-wins fallback
    # for pages still unassigned after MW matching
    # (handles multi-match pages with no MW categories)
    for page in result:
        if page.get("assignment_method") is None:
            source_cats = set(page.get("source_categories", []))
            for cat_name in assignment_priority:
                if cat_name in source_cats:
                    target_dir = cat_name_to_dir.get(cat_name)
                    if target_dir:
                        target_file = title_to_filepath(page["title"], 0)[1]
                        page["target_directory"] = target_dir
                        page["target_filename"] = target_file
                        page["assigned_category"] = cat_name
                        page["assignment_method"] = "source_category_fallback"
                        log.info("Page '%s' assigned to '%s' (source category fallback: '%s')",
                                 page["title"], target_dir, cat_name)
                    break
    ```
  - 验证：对 BOI 站点运行 homepage discovery — 确认 71 个 misc 页面减少（`activated item` 等进入 items）

### 2.2 更新模块文档

- [x] 2.2.1 更新 `page_assigner.py` 模块 docstring
  - 文件：`scripts/pipeline/pipeline/page_assigner.py`
  - 当前 L2-3：`Uses a priority chain: manual overrides > source category match > MW category tags`
  - 更新为：`Uses a priority chain: manual overrides > source category match > MW category tags > source category fallback > default (misc)`
  - 更新 L26-30 Priority chain 注释以包含 Step 3.5

## 3. 收敛与验证准备

- [x] 3.1 准备 spec-to-implementation 验证证据
  - 检查点：Step 3.5 代码位于 `assign_pages()` 中 `_apply_mw_category_matching` 与 Step 4 之间
  - 检查点：新 `assignment_method` 值 `"source_category_fallback"` 在 manifest 中可见
- [x] 3.2 准备 task-to-evidence 验证证据
  - 检查点：module docstring 已更新
- [x] 3.3 准备运行时验证证据
  - 对 BOI 站点运行 `chrome-agent crawl` → 确认 manifest 中无 `default` 方法的页面显著减少
  - `misc` 目录页面数从 ~164 降至 ~93（减少 71 页）
- [x] 3.4 标记回写目标
  - `openspec/specs/page-assignment/spec.md` — 合并 spec delta

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标，合并 spec delta 到 live spec
