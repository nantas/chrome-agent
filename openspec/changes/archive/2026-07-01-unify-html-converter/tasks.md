# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `pipeline-converters` spec 的 REMOVED requirement（`fandom-html-to-markdown-module`）——删除文件后验证 `grep -r fandom_html_to_markdown scripts/` 无残留引用
- [x] 1.2 确认 `pipeline-convert-phase` spec 的 ADDED requirements（`cdp-path-uses-shared-kernel` + `mirror-equivalence-golden-snapshot`）——切换 import 后 CDP 路径走 converter kernel，golden snapshot 输出差异 = 0（spec 已修正为 wiki_domain=""）

## 2. 核心实现任务

### Task 2.0: converter.py 支持空 `wiki_domain`（前置条件）

- [x] 2.0.1 (实现) 修改 `HtmlToMarkdownConverter.__init__`: `wiki_domain` guard 从 `if not wiki_domain` 改为 `if wiki_domain is None`——允许空字符串
- [x] 2.0.2 (实现) `_to_markdown_link`: 链接 absolutization 前加 `if self.wiki_domain:` guard
- [x] 2.0.3 (实现) `/wiki/` 路径解析: 同上前置 guard（实现在 `_normalize_href` absolutization + `_to_markdown_link` early-return）
- [x] 2.0.4 (回归) 跑 `python3 -m unittest scripts.pipeline.tests.test_table_grid` 确认现有 wiki domain 路径不受影响（17/17 pass）

### Task 2.1: 删除死代码 fandom_html_to_markdown.py

- [x] 2.1.1 (验证) `grep -r fandom_html_to_markdown scripts/ tests/` 确认零引用
- [x] 2.1.2 (实现) 删除 `scripts/pipeline/converters/fandom_html_to_markdown.py`（git rm）
- [x] 2.1.3 (回归) 98 unit pass + 全量 site-samples 13 test OK（isaac.wiki.gg 无 cache 跳过）

### Task 2.2: CDP 路径切换到 converter.py 内核

- [x] 2.2.1 (验证) 确认 `convert_html.py` 只有一处 import（line 19）
- [x] 2.2.2 (实现) 替换 import 为 `from scripts.lib.extraction.converter import convert_html_to_markdown`
- [x] 2.2.3 (实现) 替换调用 → `convert_html_to_markdown(html, wiki_domain="")`
- [x] 2.2.4 (回归) `test_convert_html` unit 10/10 pass（实际验证 CDP 路径）

### Task 2.3: test_runner 切换到 converter.py

- [x] 2.3.1 (验证) 确认 `test_runner.py:198` 只有一处 import
- [x] 2.3.2 (实现) 替换 import
- [x] 2.3.3 (实现) 替换调用 → `convert_html_to_markdown(html, wiki_domain="")`

- [x] 2.3.4 (回归) site-samples golden diff（预期，selectolax 输出更优），无 crash；2.7.1 重新生成 golden

### Task 2.4: 删除 html_to_markdown.py

- [x] 2.4.1 (验证) 残留仅 preprocessor 注释 + 待删模块 + 孤儿测试（均已由 2.4.2/2.5.1/2.6.1 处理）
- [x] 2.4.2 (实现) 删除 `scripts/lib/extraction/html_to_markdown.py`（git rm）

### Task 2.5: 删除孤儿测试文件

- [x] 2.5.1 (实现) 删除 `tests/lib/test_html_to_markdown.py`（git rm，孤儿测试）

### Task 2.6: 更新残留引用

- [x] 2.6.1 (实现) 更新 preprocessor.py:27 docstring → `HtmlToMarkdownConverter (selectolax kernel)`

### Task 2.7: 重新生成 site-samples golden 文件

- [x] 2.7.1 (实现) `--update-golden` 重新生成 3 个 nintendo golden（其余 domain 无 cache 跳过）
- [x] 2.7.2 (回归) `test_runner all` 全绿（77 unit + 13 site-samples）；附带修复 `test_assertions.py` escaped-pipe 计列 bug + 新增 `tests/lib/test_md_table_assertions.py`

### Task 2.8: 添加 mirror equivalence golden snapshot 测试

- [x] 2.8.1 (实现) 新增 `tests/test_golden_convert.py`
- [x] 2.8.2 (实现) Bloody_Gust cache → explore `convert_html_to_markdown` vs pipeline `convert_body` 断言相同
- [x] 2.8.3 (回归) `tests.test_golden_convert` pass，差异 = 0

## 3. 收敛与验证准备

- [x] 3.1 `grep html_to_markdown scripts/` 仅命中 `convert_html_to_markdown` ✓
- [x] 3.2 `grep fandom_html_to_markdown scripts/ tests/` 空 ✓
- [x] 3.3 `test_runner all` 全绿（80 unit + 13 site-samples）
- [x] 3.4 `tests.test_golden_convert` pass（差异 = 0）

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`（spec-to-implementation + task-to-evidence + adjacent fix 记录）
- [x] 4.2 生成 `writeback.md`（回写摘要 + capability 增量 + 目标执行结果）
- [x] 4.3 执行 writeback：`05-converter-architecture.md` §2.2 删除 fandom 死代码行（唯一需改动项）；frozen spec 无 fandom 条款跳过；AGENTS.md §2 / 01-overview.md Stage 2 已同步跳过
