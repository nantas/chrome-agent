# Proposal

## 问题定义

架构再审查报告（2026-08-13）的 New #3/#4/#5 三个候选，经独立核实与 reachability audit 后确认全部成立。三者主题统一（架构再审查后续清理）、行为不变、低风险，合并为一个 change。第四个候选（cli.mjs 6 个大 handler 抽取 = 原 C4 剩余）是不同物种（新增 seam 模块而非清理），明确排除，独立后续。

**A — handoff envelope 半生抽取（New #3）**：cli.mjs 有 10 处 `generateHandoff({...}) + makeResult("failure", {workflow, engine_path, handoff_path, handoff_summary})` 内联块，模式完全一致。团队已抽了 `crawlInternalError`(cli.mjs:2230) 但只覆盖其中 1 处，其余 9 处各自重写同一 envelope。一次失败 result 形状的变更 = 10 处编辑而非 1 处。

**B — obscura-serve-pool 生命周期 ×3（New #4）**：obscura engine 有一个 serve-pool 生命周期（preflight → guard ok+workerOk → findAvailablePort → startObscuraServe → concurrentFetch → stopObscuraServe → catch fallback），但三处内联编排：`runScrape`(cli.mjs:2667)、`runBatch`(cli.mjs:3061)、`crawl_scrapling.mjs`。一处 preflight guard 或 stop-on-throw 顺序的 bug 要修三次。

**C — infobox 渲染 dead code（New #5）**：subagent reachability audit 确认 `converter.py` 内 `HtmlToMarkdownConverter` 的 infobox 渲染子系统（`_render_infobox_table` + `_apply_infobox_handler` + 7 handler 方法 + `__init__` infobox 配置读取 + `_render_block` 内的 div-handler 分支，**~130 行**，比报告估的 ~110 更多）在所有声明路径中不可达：
- CV3/CV4 在 convert 前用 `preprocess_html` 剥掉了 infobox 容器（`infobox.selector`）→ convert_body 看不到 infobox tag
- CV5 调 `convert_html_to_markdown(wiki_domain="")` 空 config → `_infobox_enabled=False`
- 唯一启用 infobox 的策略 `bindingofisaacrebirth` 同时配了 selector → preprocessor 先剥掉 → convert 期分支仍不可达

convert 期渲染路径已被架构演变为 `(preprocess 去除容器) + (convert_page_full Step-1 经 infobox.py BS4 路径独立提取)` 取代，converter 内的副本是历史遗留，与 SSOT `infobox.py` 重复。

## 范围边界

**In scope**（A+B+C）：
- **A**：泛化 `crawlInternalError` → `internalFailure({command, target, repoRef, runDir, reason, summary, stderr, enginePath, artifacts, strategy})` builder；10 处内联块改 delegate（含 runCrawlSitemapDiscovery 的 5 处、runExplore 的 3 处等）。`crawlInternalError` 变为 crawl-specific 薄壳 caller
- **B**：抽 `withObscuraPool(repoRoot, urls, workers, fn) → {results, fallbackReason}`（落 cli.mjs 内部 helper，经 `api.pool` 注入 crawl_scrapling.mjs，延续 New #2 grouped seam）；3 处改 caller
- **C**：(1) `openspec/specs/pipeline/pipeline-infobox.md` REMOVED 2 个 requirement（`render-infobox-table-uses-shared-lib`、`infobox-handler-callbacks`），reason = 架构演进；(2) 删 `converter.py` ~130 行（精确边界见 design：line 273-293 div-handler 分支、343-350 触发块、391-519 `_render_infobox_table`+`_apply_infobox_handler`+7 handler、54-68 `__init__` infobox 配置读取、`_strip_html` 纯 infobox 作用域一起删）

**Out of scope**：
- **D（cli.mjs 6 大 handler 抽取）**——独立后续 change（建议它自己再拆，先抽最大 1-2 个试水）
- `makeResult` 的 success 路径（44 处里的非 failure）；`generateHandoff` 的成功用法；handoff 文档生成本身
- `runDoctor`(cli.mjs:3466) 的 `runObscuraPreflight(false)` 单纯探测；`runObscuraFetch`(981) 单页 fetch
- `infobox.py`（SSOT，BS4 路径）；`preprocessor.py` 剥离逻辑；`extract_card_stats`；`bindingofisaacrebirth` 策略的 `infobox.enabled` 配置（仍有效，由 infobox.py SSOT 服务）

**不变性**：三候选都承诺行为不变（A：handoff/failure result 字节不变；B：pool 产出/fallback 不变；C：convert 产出不变，dead code 本就不可达）。

## Capabilities

### New Capabilities

_(无)_

### Modified Capabilities

- `fetch`: A+B 候选的 spec 依据——若 internalFailure builder 与 withObscuraPool 抽取引入新的 spec 级 requirement（如「failure envelope 单一实现」「pool 生命周期单一编排」），在 fetch 能力下声明；若判定为纯内部重构无 spec 级契约变化，则仅代码改动无 fetch spec delta（design.md 定夺）
- `extract`: C 候选——`pipeline-infobox.md` 的 2 个 requirement REMOVED（归档时从 frozen spec 删除），原因是 convert 期 infobox 渲染路径废弃，infobox 提取的 SSOT 是 `infobox.py`（已由 `unified-infobox-extraction` / `shared-infobox-renderer` specs 覆盖）。若 REMOVED 需归入 extract 能力 delta 则在此声明

## Capabilities 待确认项

- [ ] 能力清单已与用户确认（A+B 可能 Modified `fetch` 或纯代码无 delta；C REMOVED 归 `extract` 或 `pipeline-infobox` 专题 spec——specs 阶段用 question 确认归属）
- [x] 范围已与用户确认（A+B+C，排除 D，调研报告 + question 已确认）

## Impact

- **代码**：
  - A：`cli.mjs`（`crawlInternalError` 泛化为 `internalFailure` + 10 处 delegate，~150-200 行净减）
  - B：`cli.mjs`（+`withObscuraPool` helper + 2 处 caller 改写）+ `crawl_scrapling.mjs`（pool 块改 caller，经 `api.pool` 注入）+ `cli.mjs` bundle 构造处（`api.pool` 加 `withObscuraPool`）
  - C：`converter.py`（删 ~130 行 dead code）
- **测试**：现有 crawl suite + convert equivalence + cleanup consistency 全绿（行为不变）；A/B 可选加 internalFailure/withObscuraPool 单测；C 无新测试（dead code 删除，既有测试已断言 infobox 被去除）
- **规范**：`pipeline-infobox.md` REMOVED 2 requirement（C）；可能 `fetch`/`convert` delta（A/B/C 视 specs 阶段定夺）
- **C10 全局同步**：**触发**（A+B 改 `chrome-agent-cli.mjs` tracked file）。归档前 cp runtime + 刷 hash
- **风险**：低。A 纯 DRY；B 纯编排合并；C 删除不可达代码。均有测试守卫

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：target-arch §4.4 + 不变量 I2、`pipeline-infobox.md`、`convert-kernel-three-layer-interface`、C10 playbook
  - 项目页：架构再审查报告 New #3/#4/#5、调研报告（本会话）、各代码精确边界
  - 回写目标：`pipeline-infobox.md` REMOVED + 可能 `fetch`/`convert` delta + C10 全局同步
