# Verification

## 验证结论

**PASS** — 三个候选（A handoff envelope / B obscura pool / C infobox dead code）全部实现并验证；4 个新 spec scenario（fetch ADDED 2 requirement × 2 scenario）+ 2 个 REMOVED（pipeline-infobox）全有可执行证据；86 node + 123 python 测试绿；2 个静态纪律测试（A/B）mutation 证明非恒真；C 删 130 行 dead code 后 convert 产出不变（equivalence + cleanup consistency 双重守卫）；C10 触发（cli.mjs tracked file 被改）。

## Spec-to-Implementation Coverage

### fetch delta（ADDED 2 requirement）

规范真源：`specs/fetch/spec.md`。

| Scenario | 实现位置 | 证据 |
| --- | --- | --- |
| `failure-envelope-single-implementation::all-internal-failure-sites-delegate-to-builder` | `cli.mjs::internalFailure`（新增 builder）+ `crawlInternalError`（薄壳化）+ 10 处 delegate | `tests/cli-failure-envelope-discipline.test.mjs`——静态守卫 grep cli.mjs，断言无 generateHandoff+makeResult-failure 内联块（internalFailure body 豁免）；RED 时列 11 残留，GREEN 后 0 |
| `failure-envelope-single-implementation::failure-envelope-byte-identical` | builder 的 envelope 构造（generateHandoff + makeResult failure + {workflow,engine_path,handoff_path,handoff_summary}）与原 10 处内联块字段一致 | 10 处 delegate 逐处 diff：字段 union 覆盖（command/reason/summary/stderr/exitCode/enginePath/workflow/artifacts/reportPath）；crawl suite + 受影响 handler 测试全绿 |
| `pool-lifecycle-single-orchestration::all-pool-callers-delegate-to-withObscuraPool` | `cli.mjs::withObscuraPool`（新增）+ runScrape/runBatch delegate + crawl_scrapling.mjs via `api.pool.withObscuraPool` | `tests/cli-pool-lifecycle-discipline.test.mjs`——静态守卫断言 startObscuraServe 仅在 withObscuraPool/runObscuraFetch 定义内或 api.pool 注入；RED 时列 2 内联，GREEN 后 0 |
| `pool-lifecycle-single-orchestration::pool-output-and-fallback-byte-identical` | withObscuraPool 返回 {result, extractionMethod, fallbackReason} | 三处 caller 各取所需字段；extractionMethod/fallbackReason 语义与原内联一致（obscura_preflight_unavailable / err.message） |

### pipeline-infobox delta（REMOVED 2 requirement）

规范真源：`specs/pipeline-infobox/spec.md`。

| REMOVED Requirement | Reason | 证据（删除安全） |
| --- | --- | --- |
| `render-infobox-table-uses-shared-lib` | convert 期 infobox 渲染路径不可达（preprocess 先剥容器）；SSOT 是 infobox.py | converter.py 删 130 行（_render_infobox_table/_apply_infobox_handler/7 handler/__init__ 配置读取/_render_block div-handler 分支）；test_convert_equivalence（CV3/CV4/CV5 等价）+ test_convert_cleanup_consistency（2 测试，断言 infobox 被**去除**）全绿 |
| `handler-implementation-stays-in-converter` | handler 方法全不可达；extract_infobox 用 infobox.py 自身的 _apply_bs4_handler | 同上；7 handler 删除后无悬挂引用（_strip_html 纯 infobox 作用域一起删） |

## Task-to-Evidence Coverage

| Task | 证据 |
| --- | --- |
| Slice A（handoff envelope） | RED: discipline test 列 11 残留 → GREEN: internalFailure builder + 10 delegate + crawlInternalError 薄壳化 → discipline 绿 |
| Slice B（obscura pool） | RED: discipline test 列 2 内联 → GREEN: withObscuraPool + 2 cli.mjs delegate + crawl_scrapling via api.pool + bundle 加 withObscuraPool → discipline 绿 |
| Slice C（infobox dead code） | 删 130 行（精确边界：__init__ 配置读取 / dispatch 触发块 / _render_block div-handler 分支 / _render_infobox_table + _apply_infobox_handler + 7 handler）；convert equivalence 5/5 + cleanup consistency 2/2 + 全量 123/123 绿 |
| 2.4.D 全量测试 | node 86/86 + python 123/123 |
| 2.6.D doctor capabilities | result: success（C 的 REMOVED 未破坏 registry） |
| 3.3 C10 触发 | git diff 含 chrome-agent-cli.mjs（tracked file，A+B 改动）+ converter.py（C，非 tracked） |
| 3.5 D 排除 | diff 的 scripts/lib/ 仅 crawl_scrapling.mjs（pool delegate，非 handler 整体移动）；6 大 handler（runExplore 等）未移入 lib/ |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| internalFailure builder | `scripts/chrome-agent-cli.mjs::internalFailure`（+ crawlInternalError 薄壳） | failure-envelope-single-implementation / Slice A |
| withObscuraPool helper | `scripts/chrome-agent-cli.mjs::withObscuraPool`（+ api.pool 注入） | pool-lifecycle-single-orchestration / Slice B |
| dead code 删除 | `scripts/lib/extraction/converter.py`（删 130 行，dead refs = 0） | pipeline-infobox REMOVED / Slice C |
| A 静态守卫 | `tests/cli-failure-envelope-discipline.test.mjs` | failure-envelope all-internal-failure-sites-delegate |
| B 静态守卫 | `tests/cli-pool-lifecycle-discipline.test.mjs` | pool-lifecycle all-pool-callers-delegate |
| C 守卫（既有） | `tests/test_convert_equivalence.py` + `tests/pipeline/test_convert_cleanup_consistency.py` | pipeline-infobox REMOVED（产出不变） |
| 全量测试 | node 86/86 + python 123/123 | task 2.4.D |
| C10 触发 | git diff --name-only 含 cli.mjs | task 3.3 |

## 缺口与阻塞项

**无缺口，无阻塞。**

- 4 个 fetch scenario + 2 个 pipeline-infobox REMOVED 全有可执行证据。
- J3 测试完备：改动模块（cli.mjs / crawl_scrapling.mjs / converter.py）均有测试（2 新静态守卫 + 既有 crawl suite + convert equivalence + cleanup consistency）。
- **C 的 audit 瑕疵（已澄清）**：subagent audit 提到 `test_infobox_source_dir.py`，实际仓库无此文件（find 确认 tests/ 无任何 *infobox* 测试）。不影响 C 的安全性——convert equivalence（断言 infobox 被**去除**而非渲染）+ cleanup consistency（2 测试）+ 全量 123/123 是充分守卫。
- C10 同步是归档前置（task 4.3）：cli.mjs tracked file 被改 → cp runtime + 刷 hash。
- **D 候选明确排除**（task 3.5 证据：diff 的 lib/ 仅 crawl_scrapling.mjs pool delegate，无 handler 整体移动）。
