# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 capability spec 的实现范围
  - `pipeline-converters`: infobox source_dir 参数透传
- [x] 1.2 确认依赖前置条件
  - 无外部依赖，修改均在 `scripts/lib/extraction/` 内部
  - 前序 change `link-fallback-redirect-skip` 无代码冲突（不同文件/函数）

## 2. 核心实现任务

- [x] 2.1 `infobox.py` — `_extract_selectolax()` 接收 `source_dir`
  - 文件: `scripts/lib/extraction/infobox.py`
  - 覆盖 spec: `specs/pipeline-converters/spec.md` → `infobox-link-source-dir-passthrough`
  - 变更: 签名加 `source_dir: str = ""`；L290、L335 处 `render_inline_children_fn(node)` 改为 `render_inline_children_fn(node, source_dir=source_dir)`
  - 验证: LSP references 确认无其他调用方受影响

- [x] 2.2 `infobox.py` — `extract_infobox()` 透传 `source_dir`
  - 文件: `scripts/lib/extraction/infobox.py`
  - 变更: 签名加 `source_dir: str = ""`；selectolax 分支调用处传入 `source_dir=source_dir`
  - 验证: grep 确认 `extract_infobox` 所有调用方

- [x] 2.3 `converter.py` — `_render_infobox_table()` 传入 `source_dir`
  - 文件: `scripts/lib/extraction/converter.py`
  - 变更: `extract_infobox(...)` 调用加 `source_dir=source_dir`
  - 验证: LSP references 确认 `_render_infobox_table` 已接收 `source_dir` 参数

## 3. 收敛与验证准备

- [x] 3.1 运行 BOI 100-page baseline 测试
  - 命令: `bash tests/e2e/boi-100-baseline.sh`
  - 预期: broken links 从 8 显著下降（Infobox 内的 Ending 链接被修复）
- [x] 3.2 抽查产出文件中 Infobox 链接格式
  - `outputs/test-100-extraction/bosses/Ultra_Greed.md` L17 应包含 `../endings/index.md`

## 4. 验证与回写收敛

- [x] 4.1 基于测试结果生成或更新 verification.md
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标
