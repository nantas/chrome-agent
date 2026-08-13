# Verification

## 验证结论

**PASS（含行为变更披露）** — 5 个 spec scenario 全有可执行证据；CV3/CV4 分歧已消除；全量 123 测试绿。**但 site-samples 回归无法完整行使行为变更**：4 受影响策略中仅 `developer.nintendo.com`（3 样本，且 `text_normalization: []` 实际 no-op）有缓存样本，其余全部 skip（无缓存 HTML/golden）。行为变更的正确性由 post-op 单测（20/20）+ 等价证明（CV3≡CV4≡kernel，含启用分歧 key 的 fixture）共同保证，而非端到端 site-samples。

## Spec-to-Implementation Coverage

规范真源：`specs/convert/spec.md` → MODIFIED `convert-kernel-three-layer-interface`（5 scenario）。

| Scenario | 实现位置 | 证据 |
| --- | --- | --- |
| `cv4-class-entry-is-declared-and-proven`（保留） | `convert.py:163`（class 直用）+ `test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel` | 既有不变量，本 change 未破坏：CV4 仍直用 class、证明仍绿 |
| `post-ops-have-one-implementation-in-kernel`（新增） | `converter.py:1033`（`apply_post_conversion_ops` 唯一实现）+ `sample_converter.py:147`（`_apply_extraction` 仅 `return convert_page_full(...)`，无内联变换） | `tests/lib/test_post_conversion_ops.py`（20/20）+ `_apply_extraction` 源码无 `re.sub`（invariant I2 履行） |
| `convert-page-full-includes-post-op-step`（新增） | `converter.py:1024`（`md = apply_post_conversion_ops(md, extraction_rules)` 作为第 5 步） | `test_cv3_explore_matches_kernel_with_postops`（CV3 经 convert_page_full 自动获 post-op） |
| `cv3-and-cv4-honor-same-post-ops-for-real-strategies`（新增） | CV4 `convert.py:182`（`md_content = apply_post_conversion_ops(...)` 显式调用） | `test_cv4_pipeline_mirror_matches_kernel_with_postops`——**RED 时精确暴露缺陷**（CV4 保留 `( )`，kernel 已 strip），GREEN 后 CV3≡CV4≡kernel |
| `escape-artifact-cleanup-is-uniform-safety-net`（新增） | `converter.py:apply_post_conversion_ops` 无条件块 | 字面量 `*`（RULES fixture 的 `3 * 5`）在 CV3≡CV4≡kernel 三路均存活；cleanup 只触 backslash-escape，inert 于字面量 |

## Task-to-Evidence Coverage

| Task | 证据 |
| --- | --- |
| Slice A（抽函数+单测） | RED: ImportError → GREEN: `tests/lib/test_post_conversion_ops.py` 20/20 |
| Slice B（convert_page_full 接入+CV3 删内联） | `test_cv3_explore_mirror_matches_kernel` + `..._with_postops` 绿；`_apply_extraction` 收缩为 1 行 return；`import re` 已删（无死导入） |
| Slice C（CV4 接入=行为变更点） | **RED 复现缺陷**：CV4 输出 diff 显示保留 `( )`（kernel 已 strip）；GREEN：CV4 加 `apply_post_conversion_ops` 调用后 5/5 等价证明绿 |
| Slice D（registry+sentinel） | `capability-registry.yaml` 3 处 `implemented_in` → `converter.py`；`doctor --check capabilities` → `result: success`；escape sentinel 字面量 `*` 三路一致 |
| 3.1 全量测试 | `python -m unittest discover -s tests` → **123/123 pass** |
| 3.2 site-samples 回归 | `python scripts/test_runner.py site-samples` → 13 tests，3 PASS（nintendo）+ 10 skip；**4 受影响策略无缓存样本，skip**——行为变更未被端到端覆盖（见缺口） |
| 3.3 CV3 字节不变 | `test_cv3_explore_mirror_matches_kernel`（RULES + RULES_WITH_POSTOPS）= CV3≡kernel，post-op 逻辑逐字搬迁 |
| 3.4 C10 | `git diff --name-only` = converter.py / sample_converter.py / convert.py / capability-registry.yaml / test_convert_equivalence.py / test_post_conversion_ops.py；无 tracked files |
| 3.5 explore spec 一致性 | `apply-extraction-uses-shared-lib` 声明 4 步、未提 post-op；`_apply_extraction` 现为 convert_page_full 薄壳——代码回归 spec 声明的 4 步语义（post-op 是 kernel 第 5 步，归 convert spec 管）。explore spec 文本无需改 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| post-op 唯一实现 | `scripts/lib/extraction/converter.py:1033` `apply_post_conversion_ops` | scenario `post-ops-have-one-implementation-in-kernel` / Slice A |
| CV4 接入点 | `scripts/pipeline/pipeline/phases/convert.py:182` | scenario `cv3-and-cv4-honor-same-post-ops-for-real-strategies` / Slice C |
| CV3 薄壳化 | `scripts/explore/sample_converter.py:147`（`_apply_extraction` 1 行 return） | invariant I2 / Slice B |
| 等价证明（含分歧 key） | `tests/test_convert_equivalence.py`（RULES_WITH_POSTOPS + 2 新 CV3/CV4 断言） | scenario `cv3-and-cv4-honor-same-post-ops-for-real-strategies` |
| post-op 单测 | `tests/lib/test_post_conversion_ops.py`（20 用例） | scenario `post-ops-have-one-implementation-in-kernel` |
| registry 订正 | `configs/capability-registry.yaml`（3 cleanup_ops → converter.py） | Slice D / doctor capabilities success |
| 全量测试 | `python -m unittest discover -s tests` → 123/123 | task 3.1 |
| C10 不触发 | `git diff --name-only`（无 tracked files） | task 3.4 |

## 缺口与阻塞项

**无阻塞性缺口。** 行为变更的正确性由单元 + 等价证明保证。但有一项**诚实披露**：

- **site-samples 未覆盖行为变更**：实际受行为变更影响的 4 站（bindingofisaacrebirth、balatrowiki、slaythespire、vampire.survivors）在 site-samples 中**全部 skip**（无缓存 HTML/golden）。注：多数策略的 `text_normalization` 字段用了不兼容 schema（描述性字符串或 dict），代码只认 `fix_spaces`/`normalize_blank_lines`/`deduplicate_words` key，静默忽略——故实际触发行为变更的站点远少于「提及这些字段」的站点数。唯一跑的 developer.nintendo.com 用 `text_normalization: []`（no-op）。后果：本 change 对真实站点产出的端到端影响未被 site-samples 行使。缓解：(1) post-op 逻辑逐字搬迁，CV3 侧字节不变（等价证明）；(2) CV4 侧新行为 = CV3 既有行为（等价证明 CV3≡CV4≡kernel），即「pipeline 产出对齐 explore 既有产出」；(3) 若需更强信心，可后续为受影响站点补缓存样本（本 change out of scope）。

- **行为变更净效果**：CV4（pipeline 生产）对配置 `text_normalization`/`url_conversion`/`youtube_cleanup`/`cleanup:[strip_empty_parens|fix_separators|normalize_internal]` 的策略，产出 Markdown 将开始应用这些变换（此前跳过）。这是预期质量修复——让 pipeline 与 explore 一致（convert.py:165 的 proxy 声称终于为真）。非破坏性预期：post-op 都是规范化清理。

- **J3 测试完备**：修改的 3 个代码模块均有对应测试（converter.py → test_post_conversion_ops + 既有 converter 测试；sample_converter.py → test_convert_equivalence CV3；convert.py → test_convert_equivalence CV4 + test_standalone_convert）。无 CRITICAL/WARNING。

- **预存结构缺陷（归档时顺带修）**：`openspec/specs/convert/spec.md` 与 fetch spec 同病（`## ADDED Requirements` + 缺 `## Purpose`），`openspec archive` 会拒绝。归档前改为 `## Requirements` + 补 Purpose（task 4.3）。
