# Tasks

> 规范真源：`specs/convert/spec.md` · MODIFIED `convert-kernel-three-layer-interface`（新增 `apply_post_conversion_ops` 入口 + 5 个 scenario：`post-ops-have-one-implementation-in-kernel`、`convert-page-full-includes-post-op-step`、`cv3-and-cv4-honor-same-post-ops-for-real-strategies`、`escape-artifact-cleanup-is-uniform-safety-net`，原 `cv4-class-entry-is-declared-and-proven` 保留）。
> 行为变更：CV4（pipeline）开始应用此前跳过的 post-ops。4 站策略受影响，site-samples 回归把关。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖范围：`convert` 能力的 `convert-kernel-three-layer-interface` requirement 已写完 MODIFIED block（含 5 个 scenario）
- [x] 1.2 确认依赖前置：`convert_page_full`（converter.py:984）已存在；post-op 源代码在 `sample_converter._apply_extraction:140-205`；CV4 调用点 `convert.py:_process_html_page` 的 `convert_body` 之后
- [x] 1.3 影响面清单已盘点：4 站实际受影响（balatrowiki、bindingofisaacrebirth、slaythespire、vampire.survivors）——均含 cleanup ops；bindingofisaacrebirth 额外 url_conversion+youtube_cleanup。注：多数策略的 text_normalization 用不兼容 schema（描述性字符串/dict），代码只认 fix_spaces/normalize_blank_lines/deduplicate_words key，静默忽略——site-samples 回归清单

## 2. 核心实现任务

### Slice A — 抽取 post-op 函数到 kernel + 单测（RED → GREEN）

覆盖 scenario `post-ops-have-one-implementation-in-kernel`。

- [x] 2.1.A RED：新建 `tests/lib/test_post_conversion_ops.py`，针对 `apply_post_conversion_ops(md, rules)` 写单测：每个 config key 的 on/off（`fix_spaces`/`normalize_blank_lines`/`deduplicate_words`、`url_conversion`、`youtube_cleanup`、`strip_empty_parens`/`fix_separators`/`normalize_internal`、escape-artifact 清理）。当前运行：**ImportError**（函数尚未存在）。
  - 完成标准：单测就绪，因 `apply_post_conversion_ops` 不存在而失败。
- [x] 2.2.A GREEN：在 `scripts/lib/extraction/converter.py` `convert_page_full` 之后新增 `apply_post_conversion_ops(md, extraction_rules) -> str`，把 `sample_converter._apply_extraction:140-205` 的 post-op 块原样搬入（含 `re` import 复用）。重跑 2.1.A：**通过**。
  - 完成标准：post-op 单测全绿；函数为纯函数（无 self/I/O）。

### Slice B — `convert_page_full` 接入 post-op + CV3 删内联块（RED → GREEN）

覆盖 scenario `convert-page-full-includes-post-op-step` + `post-ops-have-one-implementation-in-kernel`（CV3 侧）。

- [x] 2.1.B RED：`tests/test_convert_equivalence.py` 新增 `RULES_WITH_POSTOPS` fixture（启用 text_normalization/url_conversion/youtube_cleanup + 3 cleanup ops）+ HTML 加触发内容（相对图、`/wiki/` 内链、YouTube 块、空括号、相邻链接）。新增断言：`convert_page_full(HTML, RULES_WITH_POSTOPS)` 应与「手动跑 4 步 + apply_post_conversion_ops」一致；且 CV3 `_apply_extraction(HTML, RULES_WITH_POSTOPS, set())` 应 ≡ `convert_page_full(HTML, RULES_WITH_POSTOPS)`。当前运行：CV3 仍内联 post-op，断言**可能过或不过**——关键看 convert_page_full 是否已调 post-op（尚未调，故 convert_page_full 产出 ≠ CV3，RED）。
  - 完成标准：fixture 就绪；`test_cv3_explore_mirror_matches_kernel` 的 RULES_WITH_POSTOPS 变体失败（convert_page_full 没跑 post-op）。
- [x] 2.2.B GREEN：(1) `convert_page_full` 末尾加 `md = apply_post_conversion_ops(md, extraction_rules)`；(2) `sample_converter._apply_extraction` 删除 `md = _convert_page_full(...)` 之后的整段 post-op 块，改为直接 `return _convert_page_full(html, extraction_rules)`（保留 `known_pages` 形参不破坏签名）。重跑：既有 `test_cv3_explore_mirror_matches_kernel`（RULES）绿 + 新 RULES_WITH_POSTOPS 变体绿。
  - 完成标准：CV3 侧等价证明全绿；`_apply_extraction` 无 markdown 变换逻辑（invariant I2 履行）。

### Slice C — CV4 接入 post-op（RED → GREEN）—— 行为变更点

覆盖 scenario `cv3-and-cv4-honor-same-post-ops-for-real-strategies`。

- [x] 2.1.C RED：`tests/test_convert_equivalence.py` 新增 `test_cv4_pipeline_mirror_matches_kernel_with_postops`：用 `RULES_WITH_POSTOPS` 调 `convert_single_page`，`_unwrap_pipeline_body` 后断言 ≡ `convert_page_full(HTML, RULES_WITH_POSTOPS)`。当前运行：CV4 不跑 post-op → **CV4 ≠ kernel，RED**（这是缺陷的核心证据）。
  - 完成标准：该断言失败，信息指向 CV4 缺 post-op。
- [x] 2.2.C GREEN：`convert.py::_process_html_page` 在 `md_content = converter.convert_body(...)` 之后加 `md_content = apply_post_conversion_ops(md_content, extraction_config or {})`（import 从 `scripts.lib.extraction.converter`）。订正 line 165 注释（proxy 声称变真，措辞校准）。重跑 2.1.C：**通过**。
  - 完成标准：CV4 等价证明全绿；CV3≡CV4≡kernel 对 RULES_WITH_POSTOPS 成立。

### Slice D — registry + escape sentinel 收尾（文档/配置）

覆盖 scenario `escape-artifact-cleanup-is-uniform-safety-net` + registry 订正。

- [x] 2.3.D `configs/capability-registry.yaml`：`strip_empty_parens`/`fix_separators`/`normalize_internal` 的 `implemented_in` 改指 `scripts/lib/extraction/converter.py`。跑 `chrome-agent doctor --check capabilities` 确认过。
- [x] 2.4.D 校核 escape-artifact：等价证明的 RULES_WITH_POSTOPS fixture 含一个 `*` 字面量，断言 CV3≡CV4≡kernel（两条路径都无条件清 escape，统一）。若 fixture 已在 Slice B 覆盖则无需额外。

## 3. 收敛与验证准备

- [x] 3.1 全量 convert 测试：`python3 -m unittest discover -s tests -v`（含 test_convert_equivalence.py + test_post_conversion_ops.py + 既有 converter 测试），全绿
- [x] 3.2 **site-samples 回归（行为变更把关）**：对每个配置分歧 key 的站点跑 `python3 scripts/test_runner.py site-samples --domain <domain>`，清单：bindingofisaacrebirth.wiki.gg、balatrowiki.org、slaythespire.wiki.gg、vampire.survivors.wiki（实际受影响的 4 站）。记录每站结果到 verification.md；失败站回到 design 评估
- [x] 3.3 确认 CV3 字节不变：对比 `_apply_extraction` 改前改后对一组样本的产出（explore 侧无行为变更，post-op 只搬家）
- [x] 3.4 确认 C10 不触发：`git diff --name-only` 仅含 converter.py / sample_converter.py / convert.py / capability-registry.yaml / tests，无 tracked files
- [x] 3.5 explore spec 后果记录：`openspec/specs/explore/explore-scaffold.md::apply-extraction-uses-shared-lib` 当前声明 4 步、post-op 不在其中（本 change 让 _apply_extraction 真正回归 4 步薄壳）——spec 文本无需改动（它本来就没提 post-op），在 verification.md 记录「spec 与代码现已一致」

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`：spec-to-implementation（5 scenario 各证据）+ task-to-evidence（Slice A-D 测试输出 + site-samples 各站结果）+ 行为变更披露（哪些站 pipeline 产出变了、是否破坏性）
- [x] 4.2 生成 `writeback.md`：回写目标 = convert spec delta（归档提升）+ explore-scaffold（记录无需改）+ capability-registry（已改）+ 00-target-architecture §3.1（post-op 归属措辞）；C10 不触发
- [x] 4.3 归档前修 convert spec 结构缺陷（`## ADDED Requirements`→`## Requirements` + 补 `## Purpose`）；`openspec status` apply-ready；归档提交提升 spec delta 为 frozen
