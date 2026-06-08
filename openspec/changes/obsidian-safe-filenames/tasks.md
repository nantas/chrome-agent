# tasks.md — obsidian-safe-filenames

## 总览

将"输出到 Obsidian vault 时文件名/路径不得包含空格"提升为显式治理约束。

## 任务

- [ ] **T1** — 更新 `title_to_filepath()` docstring，显式声明空格替换目的
  - 文件：`scripts/pipeline/strategies/__init__.py`
  - 证据：docstring 中包含 Obsidian 兼容性说明

- [ ] **T2** — 更新 `raw_to_cache_filename()` docstring，显式声明空格替换目的
  - 文件：`scripts/pipeline/pipeline/cache.py`
  - 证据：docstring 中包含 Obsidian 兼容性说明

- [ ] **T3** — 在 `page_assigner.py` 返回前添加 target_directory / target_filename 空格断言
  - 文件：`scripts/pipeline/pipeline/page_assigner.py`
  - 要求：断言失败为 pipeline error，不静默写入

- [ ] **T4** — 在 `convert.py` 文件写入前添加 target_directory / target_filename 空格断言
  - 文件：`scripts/pipeline/pipeline/phases/convert.py`
  - 要求：防御性校验，与 T3 形成双层保障

- [ ] **T5** — 策略 schema 中对 `api.homepage.categories[].dir` 添加不含空格约束
  - 文件：策略 schema 定义文件（待定位）
  - 要求：`pattern: '^[^ ]+$'` 或等效校验

- [ ] **T6** — 验证所有现有策略文件的 `categories[].dir` 无空格
  - 命令：`grep -r "dir: .* " sites/strategies/`（应无命中）

- [ ] **T7** — 提交 PR，关联本 spec
