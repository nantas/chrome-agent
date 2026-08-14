# Design

## Context

三个独立核实成立的清理候选，合并为一个 change。A+B 是 cli.mjs 内部 DRY（重复 envelope / 重复 pool 编排），C 是 converter.py dead code 删除 + 对应 frozen spec requirement 废弃。三者行为不变、主题统一（架构再审查后续清理）。

规范真源：
- A+B → `specs/fetch/spec.md`（ADDED `failure-envelope-single-implementation` + `pool-lifecycle-single-orchestration`）
- C → `specs/pipeline-infobox/spec.md`（REMOVED `render-infobox-table-uses-shared-lib` + `handler-implementation-stays-in-converter`）

## Goals / Non-Goals

**Goals:**
- A：泛化 `crawlInternalError` → `internalFailure` builder；10 处内联块 delegate；`crawlInternalError` 变 crawl 薄壳 caller
- B：抽 `withObscuraPool`；3 处（runScrape/runBatch/crawl_scrapling.mjs via api.pool）改 caller
- C：删 converter.py ~130 行 dead code；REMOVED pipeline-infobox.md 的 2 个 requirement
- 三者都加静态守卫测试（A: grep 残留内联块；B: grep 残留内联 pool 生命周期；C: 既有 equivalence/cleanup 测试即守卫）

**Non-Goals:**
- D（cli.mjs 6 大 handler 抽取）——独立后续
- `infobox.py` SSOT / preprocessor / extract_card_stats ——不动
- success-path makeResult / generateHandoff 成功用例——不动
- `runDoctor`/`runObscuraFetch` 的非 pool obscura 用法——不动

## Decisions

**D1 — A 的 builder 签名（union of 10 处字段）**。`internalFailure({command, target, repoRef, runDir, reason, summary, stderr, enginePath, artifacts, strategy, eventMsg, resultMsg, reportPath, emitReport, workflow})`。逐处核实 10 个内联块的 `{workflow, engine_path, handoff_path, handoff_summary}` + artifacts 差异——builder 用可选参数覆盖 union。`crawlInternalError` 现签名是其子集，变为 `return internalFailure({command:"crawl", ...})` 薄壳。落点：cli.mjs 内部（紧邻 generateHandoff/makeResult），不抽 lib/（避免过度工程；这两个 builder 是 cli.mjs 专属）。

**D2 — A 的静态守卫**。新增测试（node:test，落 tests/）：grep cli.mjs 源码，对每个 `generateHandoff(` 调用点检查其后续 N 行内是否紧跟 `makeResult("...","failure"`——若是则标记为「内联 failure envelope 残留」，断言无残留（crawl-prefixed 薄壳 caller 豁免：它调 internalFailure 不直接 generateHandoff）。这把 `failure-envelope-single-implementation` 的 `all-internal-failure-sites-delegate-to-builder` scenario 变成可执行断言。

**D3 — B 的 withObscuraPool 落点 + 签名**。`withObscuraPool(repoRoot, urls, workers, timeout, fn) → {results, fallbackReason, extractionMethod}`，落 cli.mjs 内部 helper。三处 caller 差异：
- runScrape/runBatch：直接调（cli.mjs 内部）
- crawl_scrapling.mjs：经 `api.pool.withObscuraPool` 注入（延续 New #2 grouped seam；bundle 构造处 `api.pool` 加 `withObscuraPool`）

`fn` callback 收到 `{serveHandle, prefetchedHtml}` 并返回 per-command 结果（runScrape 调 convertTraversalToMarkdown；runBatch 写 htmlPath + 建 results；crawl_scrapling 调 convertTraversalToMarkdown）。fallback reason bookkeeping 统一为返回 `{fallbackReason, extractionMethod}`。

**D4 — B 的静态守卫**。测试 grep cli.mjs + crawl_scrapling.mjs，断言 `startObscuraServe(` 的调用点要么在 `withObscuraPool` 定义内，要么在 `runObscuraFetch`(单页 fetch，out of scope) 内——不得在 runScrape/runBatch/runCrawlScrapling 的 handler 体内联。这把 `pool-lifecycle-single-orchestration` 的 `all-pool-callers-delegate` scenario 变成可执行断言。

**D5 — C 的删除边界（精确，来自 audit）**。删 `converter.py`：
- line 273-293：`_render_block` 内的 div-handler 分支（`if self._infobox_enabled ... _apply_infobox_handler`）
- line 343-350：dispatch 里的触发块（`if self._infobox_enabled and tag == self._infobox_tag`）
- line 391-519：`_render_infobox_table` + `_apply_infobox_handler` + 7 handler（`_strip_html`/`_extract_image_value`/`_count_images`/`_extract_cur_id`/`_dedup_pools`/`_simplify_collection`/`_extract_tags`）
- line 54-68：`__init__` 的 infobox 配置读取（`_infobox_enabled`/`_infobox_selector`/`_infobox_field_selector`/`_infobox_label_selector`/`_infobox_value_selector`/`_infobox_tag`/`_infobox_class_list`/`_infobox_handlers`）
- `_strip_html` 纯 infobox 作用域（仅被 handler 族引用），一起删

**边界完整性约束**：删除要完整——漏删 line 293 分支会留悬挂引用（`_apply_infobox_handler` 调用点残留 → NameError）。删后 `HtmlToMarkdownConverter.__init__` 不再读 `infobox` config 键（caller 仍可传，被忽略——向后兼容）。

**D6 — C 无新测试，既有测试即守卫**。`test_convert_equivalence.py`（CV3/CV4/CV5 等价，infobox 被**去除**）+ `test_convert_cleanup_consistency.py`（断言 infobox 容器不出现）。删除后这两组测试应全绿（dead code 不影响产出）。若红，说明 audit 有误或删多了——回退该部分。

## Risks / Migration

**风险**：
- *低。* A：10 处 envelope 字段 union 化时，若某处有独特字段被遗漏 → 该处产出变化。缓解：逐处 diff 改前改后的 handoff/result（byte-identical 断言）；静态守卫抓残留。
- *低。* B：三处 fallback reason 语义差异（`parallelFallbackReason` vs `fallbackReason` vs `extractionMethod`）。缓解：withObscuraPool 返回结构覆盖 union，caller 各取所需；byte-identical 断言。
- *极低。* C：删 dead code，既有测试守卫。audit 已静态证明不可达；最坏情况 = 某测试红 → 说明删多了 → 回退。

**迁移**：无外部调用方感知。`HtmlToMarkdownConverter.__init__` 的 `infobox` config 键变为被忽略（向后兼容——CV3/CV4/CV5 仍可传，不报错）。

**C10 全局同步**：**触发**（A+B 改 `chrome-agent-cli.mjs` tracked file）。归档前 cp runtime + 刷 hash（与 New #2 同模式）。

**验证锚点**：
- `node --test tests/*.test.mjs`（A/B 静态守卫 + 既有 crawl suite）
- `.venv/bin/python -m unittest discover -s tests`（C：convert equivalence + cleanup consistency + 全量）
- `node scripts/chrome-agent-cli.mjs doctor`（C10 同步后健康）
- byte-identical：A 的 handoff/result、B 的 pool 产出、C 的 convert Markdown
