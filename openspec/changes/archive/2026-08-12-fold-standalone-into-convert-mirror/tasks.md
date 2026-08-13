# Tasks

> 涉及 `scripts/pipeline/standalone.py`（Python）与 `00-target-architecture.md`（文档）。代码任务拆 vertical slice（RED→GREEN）；纯文档任务独立。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/convert/spec.md` 覆盖：`standalone-orchestrator-delegates-to-cv4-mirror`（3 scenario）+ `convert-kernel-three-layer-interface`（1 scenario）
- [x] 1.2 确认 `convert_single_page` 签名与 raw/page_info 字段需求（见 convert.py），确认 ApiClient 在 `fetch_and_convert` 中的 mock 边界

## 2. 核心实现任务

### Slice A — standalone 折叠（修 preprocess 漂移）

- [x] 2.1 (RED) `tests/test_standalone_convert.py`：mock ApiClient，构造含 `#catlinks` 的 HTML + `extraction_config={"cleanup":["strip_footer"]}`，调 `fetch_and_convert(mode="html")`，断言输出不含 "Categories" 文本。折叠前确认 FAIL（漂移存在）
- [x] 2.2 (GREEN) 重写 `fetch_and_convert` HTML 分支：组装 `raw={"html","images","content_acquisition":"html_rendered"}` + `page_info`，委托 `convert.convert_single_page`，写回 `result["content"]`；删除重复的 frontmatter/card_stats/title 编排
- [x] 2.3 (验证) `.venv/bin/python -m unittest tests.test_standalone_convert` GREEN；`.venv/bin/python -m unittest discover -s tests` 全套绿

### Slice B — reconvert_file 对齐内核

- [x] 2.4 (GREEN) `reconvert_file` 无 source_url 分支改用 `convert_page_full(body, extraction_config or {})`；有 source_url 分支转调新 `fetch_and_convert`（自动获益）；保留 frontmatter 重建
- [x] 2.5 (验证) 现有 pipeline/tests 全绿；`reprocess_pages` 循环（调 `fetch_and_convert`）回归无破坏

### Slice C — 三层接口声明（纯文档，C3）

- [x] 2.6 在 `docs/architecture/00-target-architecture.md` §3.1「目标模块」表后补「内核三层接口」声明段落（类/函数/full-orchestration 三层用途，CV4 直接用类的理由），引用 spec 的 `convert-kernel-three-layer-interface`
- [x] 2.7 §3.1 目标模块表 CV4 行补注「直接用类入口（声明，见三层接口）」；补 standalone 变体声明行（B 轴 pipeline-standalone，equivalence 指针指向 `tests/test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel`，因 standalone ≡ CV4）

## 3. 收敛与验证准备

- [x] 3.1 证据清单：regression test 由 RED→GREEN、全套测试绿、standalone.py 行数净减、preprocess 漂移消除的 grep 证据
- [x] 3.2 回写摘要：`00-target-architecture.md` §3.1 两处改动点；CONTEXT.md 评估（standalone 是否需补术语）

## 4. 验证与回写收敛

- [x] 4.1 生成 verification.md（spec→code 映射 + 全量测试复跑 + 漂移修复证据）
- [x] 4.2 生成 writeback.md（00-target-architecture §3.1 改动确认；CONTEXT.md 评估结论）
- [x] 4.3 执行 writeback；`doctor --check capabilities`（C11 归档前置）；归档 `archive/2026-08-12-fold-standalone-into-convert-mirror/`，回填 convert delta 到 `openspec/specs/convert/spec.md`
