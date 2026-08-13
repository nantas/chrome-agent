# Tasks

> **回溯性 change**：实现已于本 session 完成（commits `f03376d`、`ac08bba`、`42e2dcc`）。tasks 按 vertical slice 结构记录已执行的实现与验证，checkbox 勾选表示「已验证通过」。fanbox（候选 6）不归属任何能力，作为实现记录条目附于核心实现段。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/convert/spec.md` 的 `mirror-equivalence-golden-snapshot` 覆盖范围：CV3/CV4/CV5 ≡ CV1 内核，5 个 scenario（cv3/cv4/cv5 三等价 + fixture-discriminates-preprocessing + test-never-skips）
- [x] 1.2 确认 convert spec 永久文件指针已由 `archive/2026-08-12-cleanup-post-4d-drift/` 回填为 `test_convert_equivalence.py`，本 change 不再改 spec 永久文件

## 2. 核心实现任务

### Slice A — convert 镜像等价证明（候选 1，capability: convert）

- [x] 2.1 (RED) 探针验证当前代码下 CV3/CV4/CV5 与内核的等价性，确认 fixture 选择能让断言真实而非空转
- [x] 2.2 (GREEN) 实现 `tests/test_convert_equivalence.py`：3 用例（CV3≡kernel / CV4≡kernel 剥离声明的包装 / CV5≡kernel({})），内嵌 fixture 覆盖 /wiki/ 链接、rowspan/colspan 表格、列表、图片
- [x] 2.3 (RED→GREEN) 加判别元素 `#catlinks` + `cleanup:["strip_footer"]`，突变检查确认「CV4 跳过 preprocess」可被捕获；修正 `_unwrap_pipeline_body` 对「正文以标题开头时 CV4 不前置标题」的容错
- [x] 2.4 (GREEN) 加入 KI 字符哨兵：表格 `|`、字面 `*`（内核转义漂移哨兵）、带括号/撇号页面标题、KI-5 图链连排、tooltip 对
- [x] 2.5 (验证) `.venv/bin/python -m unittest tests.test_convert_equivalence` 3 用例绿；`.venv/bin/python -m unittest discover -s tests` 全套绿

### Slice B — fanbox helper 去重（候选 6，非能力实现记录）

- [x] 2.6 (GREEN) 提取 `scripts/lib/fanbox-shared.mjs`：10 个无状态 helper（sh/sleep/escapeXml/extractChineseText/extractActorNames/downloadCover/generateNfo/findTarget/cdpEval/cdpNav）
- [x] 2.7 (RED) 实现 `tests/fanbox-shared.test.mjs`（node:test，6 用例，覆盖纯 helper）
- [x] 2.8 (GREEN) 两脚本改为 import 共享层，保留各自差异（fetchWithRetry/fetchPostDetail/external 专属匹配逻辑）
- [x] 2.9 (验证) `node --check` 两脚本 + 共享层；`node --test tests/fanbox-shared.test.mjs` 6 用例绿；import/export 名交叉核对无 MISSING

## 3. 收敛与验证准备

- [x] 3.1 证据清单：commits `f03376d`/`ac08bba`/`42e2dcc`、unittest 99+51 绿、node 6+9 绿、spec→code 映射
- [x] 3.2 回写摘要：无新增回写目标（convert spec 永久文件已在删除批 change 回填；fanbox 无能力/架构页受影响）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 verification.md（spec→code 映射 + 全量测试复跑）
- [x] 4.2 基于 verification.md 结论生成 writeback.md（本 change 无新增回写，记录确认）
- [x] 4.3 归档：`openspec/changes/arch-review-followups` → `archive/2026-08-12-arch-review-followups/`，回填 convert delta 到 `openspec/specs/convert/spec.md`（本 change delta 为 scenario 细化，需合并入永久 spec）
