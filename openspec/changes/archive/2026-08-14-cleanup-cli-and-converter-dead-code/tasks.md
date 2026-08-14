# Tasks

> 规范真源：
> - `specs/fetch/spec.md`（A+B：ADDED `failure-envelope-single-implementation` + `pool-lifecycle-single-orchestration`）
> - `specs/pipeline-infobox/spec.md`（C：REMOVED `render-infobox-table-uses-shared-lib` + `handler-implementation-stays-in-converter`）
>
> 三候选行为不变、低风险。C10 触发（A+B 改 cli.mjs tracked file）。D（cli.mjs 6 大 handler 抽取）明确排除。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖范围：fetch delta（ADDED 2 requirement，4 scenario）+ pipeline-infobox delta（REMOVED 2 requirement，含 reason + migration）已写完
- [x] 1.2 确认依赖前置：
  - A：`crawlInternalError`(cli.mjs:2230) 已存在（泛化基础）；10 处 `generateHandoff` + failure `makeResult` 已定位
  - B：`runObscuraPreflight`/`startObscuraServe`/`concurrentFetch`/`stopObscuraServe`/`findAvailablePort` 已存在；3 处 caller 已定位（runScrape:2667、runBatch:3061、crawl_scrapling.mjs via api.pool）
  - C：converter.py dead code 精确边界已由 audit 给出（line 273-293、343-350、391-519、54-68、`_strip_html`）；infobox.py SSOT 不动
- [x] 1.3 影响面盘点：A 改 cli.mjs ~10 处 + builder；B 改 cli.mjs 2 处 + crawl_scrapling.mjs 1 处 + bundle 构造；C 删 converter.py ~130 行；C10 触发

## 2. 核心实现任务

### Slice A — handoff envelope：泛化 builder + 10 处 delegate + 静态守卫（RED → GREEN）

覆盖 `failure-envelope-single-implementation`。

- [x] 2.1.A RED：新增 `tests/cli-failure-envelope-discipline.test.mjs`（node:test）——grep cli.mjs，对每个 `generateHandoff(` 调用点检查其后续 ~10 行内是否紧跟 `makeResult("...","failure"` 或 `makeResult(...,  "failure"`），标记为内联 failure envelope 残留；断言**无残留**（crawl-prefixed internalFailure 薄壳 caller 豁免）。当前运行：**失败**（10 处内联块均残留）。
  - 完成标准：守卫测试就绪，精确列出 10 处残留。
- [x] 2.2.A GREEN：(1) 在 cli.mjs 泛化 `crawlInternalError` → `internalFailure({command, target, repoRef, runDir, reason, summary, stderr, enginePath, artifacts, strategy, reportPath, emitReport, workflow})`（union of 10 处字段）；`crawlInternalError` 变为 `return internalFailure({command:"crawl", ...})` 薄壳。(2) 10 处内联块逐个改 delegate（含 runCrawlSitemapDiscovery 的 5 处、runExplore 的 3 处等），每处 diff 改前改后的 handoff/result 确认 byte-identical。重跑 2.1.A：**通过**。
  - 完成标准：守卫测试绿；10 处 delegate；crawl suite + 受影响 handler 测试全绿。

### Slice B — obscura pool：抽 withObscuraPool + 3 处 caller + 静态守卫（RED → GREEN）

覆盖 `pool-lifecycle-single-orchestration`。

- [x] 2.1.B RED：新增 `tests/cli-pool-lifecycle-discipline.test.mjs`（node:test）——grep cli.mjs + crawl_scrapling.mjs，断言 `startObscuraServe(` 的调用点仅在 `withObscuraPool` 定义内、或 `runObscuraFetch`（单页，out of scope）内，不得在 runScrape/runBatch/runCrawlScrapling handler 体内联。当前运行：**失败**（runScrape/runBatch 仍内联）。
  - 完成标准：守卫测试就绪，列出内联残留。
- [x] 2.2.B GREEN：(1) cli.mjs 新增 `withObscuraPool(repoRoot, urls, workers, timeout, fn) → {results, fallbackReason, extractionMethod}`（D3 签名）。(2) runScrape(2667)、runBatch(3061) 改 delegate；crawl_scrapling.mjs 的 pool 块改 delegate（经 `api.pool.withObscuraPool`）。(3) cli.mjs bundle 构造处 `api.pool` 加 `withObscuraPool`（grouped seam 保持）。(4) 每处 byte-identical 验证（fallback reason + 产出）。重跑 2.1.B：**通过**。
  - 完成标准：守卫测试绿；3 处 delegate；crawl suite（含 obscura parallel 路径）全绿。

### Slice C — infobox dead code：删 ~130 行 + REMOVED spec（GREEN，既有测试即守卫）

覆盖 `pipeline-infobox.md` REMOVED + convert 产出不变。

- [x] 2.1.C 删除 `scripts/lib/extraction/converter.py` 的 dead code（按 design D5 精确边界）：line 273-293（`_render_block` div-handler 分支）、343-350（触发块）、391-519（`_render_infobox_table` + `_apply_infobox_handler` + 7 handler）、54-68（`__init__` infobox 配置读取）、`_strip_html`。删除要完整（漏删留悬挂引用 → NameError）。
- [x] 2.2.C 跑 convert 守卫测试确认 GREEN：`.venv/bin/python -m unittest tests.test_convert_equivalence tests.pipeline.test_convert_cleanup_consistency`（若路径名不对，用 discover）。两组测试均应绿（dead code 不影响产出；它们本就断言 infobox 被**去除**而非渲染）。若红 → audit 有误或删多了 → 回退该部分重审。
  - 完成标准：convert equivalence（CV3/CV4/CV5）+ cleanup consistency + infobox SSOT 测试全绿。
- [x] 2.3.C 确认 `HtmlToMarkdownConverter.__init__` 的 `infobox` config 键被忽略（向后兼容——caller 仍可传，不报错）。grep 确认无 caller 因删 `__init__` 读取而 break。

### Slice D — 收尾核验（无 registry 改动；本 change 无配置 SSOT 变化）

- [x] 2.4.D 全量测试：`node --test tests/*.test.mjs` + `.venv/bin/python -m unittest discover -s tests`，全绿
- [x] 2.5.D 确认行为不变：A 的 handoff/result、B 的 pool 产出、C 的 convert Markdown（byte-identical 证据收集）
- [x] 2.6.D doctor --check capabilities（确认 C 的 REMOVED 未破坏 registry 一致性——pipeline-infobox.md 的 requirement 与 capability-registry 若有交叉引用）

## 3. 收敛与验证准备

- [x] 3.1 全量 node + python 测试绿（Slice D 已含；最终确认）
- [x] 3.2 行为不变证据：A/B/C 各自 byte-identical 断言结果
- [x] 3.3 确认 C10 触发条件：`git diff --name-only` 含 `chrome-agent-cli.mjs`（A+B 改动）
- [x] 3.4 准备 C10 同步证据：runtime.mjs 与 global 副本 diff（应空）+ installed-hash 刷新前后值
- [x] 3.5 D 候选排除确认：本 change diff 不含 6 大 handler 抽取（runExplore/runBootstrapStrategy/runBatch/runCrawlSitemapDiscovery/runCrawlSitemapExtraction/runCrawlMediawikiApi 的整函数移动）；runBatch 仅 pool 块改 delegate，非整函数抽取

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`：spec-to-implementation（fetch 2 ADDED scenario + pipeline-infobox 2 REMOVED reason 各证据）+ task-to-evidence（Slice A/B/C 测试输出 + byte-identical）+ C10 同步证据
- [x] 4.2 生成 `writeback.md`：回写目标 = fetch spec delta（归档提升）+ pipeline-infobox.md REMOVED（归档时从 frozen spec 删除）+ C10 全局同步（runtime cp + installed-hash 刷新）
- [x] 4.3 归档前执行 C10 同步：cp runtime + 刷 installed-hash 至 HEAD；`openspec status` apply-ready；归档提交提升 fetch delta + 删除 pipeline-infobox.md 的 2 requirement + C10 同步在同 commit
