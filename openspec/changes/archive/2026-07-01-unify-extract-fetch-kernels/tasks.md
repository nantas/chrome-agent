# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `extract-kernel` spec 的 REMOVED requirement（`context-parameter`）——验证仅 2 个调用方
- [x] 1.2 确认 `extract-kernel` spec 的 ADDED requirements（`convert-page-full` + `extract-infobox-via-kernel`）
- [x] 1.3 确认 `fetch-kernel` spec 的 REMOVED requirement（`mjs-mediawiki-api-fetch`）——定位 `.mjs` 调用链
- [x] 1.4 确认 `fetch-kernel` spec 的 MODIFIED requirement（`fetch-via-pipeline-kernel`）

## 2. 核心实现任务

### Task 2.1: 删除 preprocessor `context` 参数

- [x] 2.1.1 (验证) `grep -rn "context=" scripts/` 确认仅 `sample_converter.py` + `convert.py` 两处
- [x] 2.1.2 (实现) 删除 `preprocessor.py` 的 `context` 参数和 if-else 分支
- [x] 2.1.3 (实现) 更新 `sample_converter.py:154`: 去掉 `context="explore"`
- [x] 2.1.4 (实现) 更新 `convert.py:171`: 去掉 `context="explore"`
- [x] 2.1.5 (回归) 跑 `python3 scripts/test_runner.py all` 确认通过

### Task 2.2: 移动 `_apply_extraction` 到 `converter.py`

- [x] 2.2.1 (实现) 在 `converter.py` 新增 `convert_page_full(html, extraction_rules)`
- [x] 2.2.2 (实现) 修改 `sample_converter.py` `_apply_extraction` → 委托调用 `convert_page_full`
- [x] 2.2.3 (回归) 跑 `python3 scripts/test_runner.py site-samples` 确认输出不变

### Task 2.3: 统一 .mjs MediaWiki fetch

- [x] 2.3.1 (验证) 定位 `.mjs` 中 `runMediawikiApiFetch` 的所有调用点（`runEngineFetch` + crawl helper）
- [x] 2.3.2 (实现) 替换 `runMediawikiApiFetch` 为 pipeline delegate（spawn `python3 -m scripts.pipeline` 或直接 import）
- [x] 2.3.3 (验证) `.mjs` 返回格式兼容下游 convert 路径
- [x] 2.3.4 (回归) 跑 `.mjs` 相关的集成测试或手动验证

## 3. 收敛与验证准备

- [x] 3.1 `grep -r "context=" scripts/` 不命中 `preprocess_html` 调用
- [x] 3.2 `grep _apply_extraction scripts/` — `sample_converter.py` 保留薄包装（仅 post-processing），已无 orchestrator 逻辑
- [x] 3.3 `python3 scripts/test_runner.py all` 全绿 (80 tests, .venv)
- [x] 3.4 pipeline + explore 路径输出等价验证 — `TestMirrorEquivalence` 通过

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`
- [x] 4.2 生成 `writeback.md`
- [x] 4.3 执行 writeback
