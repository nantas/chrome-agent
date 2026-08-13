# Writeback

## 回写摘要

- change：`unify-convert-post-ops-into-kernel`
- 回写结论：**PASS，spec delta 归档时提升为 frozen；其余回写为订正/记录**。CV3/CV4 markdown 层 post-op 分歧已消除（统一到 kernel `apply_post_conversion_ops`）；行为变更（CV4 开始应用 post-op）经单元 + 等价证明保证正确，site-samples 因缺缓存样本未端到端覆盖（已披露）。
- 关键结果：新增 kernel 公开入口 `apply_post_conversion_ops`；`convert_page_full` 增第 5 步；CV4 显式调用；CV3 `_apply_extraction` 薄壳化（invariant I2 履行）；等价证明加 `RULES_WITH_POSTOPS` fixture 绑定真实策略；registry 3 处归属订正；123/123 测试绿。

## Capability / Spec 增量摘要

| Capability | 变更类型（New/Modified/Removed/Renamed） | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `convert` | Modified | `openspec/changes/unify-convert-post-ops-into-kernel/specs/convert/spec.md`（归档提升为 `openspec/specs/convert/spec.md` frozen 增量） | MODIFIED `convert-kernel-three-layer-interface`：新增第 4 个公开入口 `apply_post_conversion_ops` + `convert_page_full` 第 5 步 + 4 个新 scenario（post-ops-have-one-implementation-in-kernel、convert-page-full-includes-post-op-step、cv3-and-cv4-honor-same-post-ops-for-real-strategies、escape-artifact-cleanup-is-uniform-safety-net）；原 cv4-class-entry-is-declared-and-proven 保留 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | PASS — 5 scenario 全有证据 | `verification.md` § Spec-to-Implementation Coverage |
| Task-to-Evidence | PASS — Slice A-D 全绿，CV4 RED 精确复现缺陷 | `verification.md` § Task-to-Evidence Coverage |
| 测试完备（J3） | PASS — 3 个改动模块均有对应测试 | `verification.md` § 缺口与阻塞项 |
| 行为变更 | 披露但非阻塞 — site-samples 未覆盖（缺样本），正确性由等价证明保证 | `verification.md` § 缺口与阻塞项 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `openspec/specs/convert/spec.md`（归档提升） | `convert-kernel-three-layer-interface` requirement | 归档时 MODIFIED block 提升为 frozen（+ `apply_post_conversion_ops` 入口 + 4 scenario） |
| `openspec/specs/explore/explore-scaffold.md::apply-extraction-uses-shared-lib` | 无文本改动（记录） | 该 requirement 声明 4 步、未提 post-op；代码现回归该语义（`_apply_extraction` 薄壳化）。spec 与代码现已一致，无需编辑 |
| `configs/capability-registry.yaml` | 3 处 `cleanup_ops.implemented_in` | 已改：`strip_empty_parens`/`fix_separators`/`normalize_internal` 从 `sample_converter.py` → `converter.py`（doctor capabilities 已过） |
| `docs/architecture/00-target-architecture.md` §3.1 | CV3 mirror 行 post-op 归属措辞 | 归档时订正（post-op 不再属 CV3 mirror，归 kernel；措辞校准，维度坐标不变） |
| `scripts/pipeline/pipeline/phases/convert.py:165` | proxy 注释 | 已订正（proxy 声称变真） |
| C10 全局副本 | — | **不回写**：本 change 不触碰 C10 tracked files |

## 回写执行结果

| 目标页 | 执行结果（成功/失败/跳过） | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `openspec/specs/convert/spec.md` | 跳过（归档时执行） | — | — | spec delta 提升在 `/opsx-archive` 归档步骤；verification.md 已确认 delta 就绪 |
| `configs/capability-registry.yaml` | 成功（已改） | 本 change | 实施 agent | 3 处 `implemented_in` → converter.py；`doctor --check capabilities` = success |
| `convert.py:165` 注释 | 成功（已订正） | 本 change | 实施 agent | proxy 声称措辞校准为事实 |
| `explore-scaffold.md` | 跳过（无需改） | — | — | spec 文本与代码现一致，无编辑 |
| `00-target-architecture.md §3.1` | 跳过（归档时订正） | — | — | 归档步骤处理措辞校准 |
| C10 全局副本 | 跳过（不触发） | — | — | `git diff --name-only` 不含 tracked files |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（`00-target-architecture.md` §3.1 + 不变量 I2 + §4.3、`05-converter-architecture.md`、`convert-kernel-three-layer-interface`）
- [x] `verification.md` 已生成且无阻塞项（行为变更已披露，非阻塞）
- [x] 回写目标页已确认存在且可编辑（convert spec / capability-registry 由归档流程管理；explore spec 无需改）
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致（仅 Modified `convert`）

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/convert/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息（如 unify-html-converter / fold-standalone 的细节）
- 不触发 C10 全局同步（已核实）
- 不为受影响站点补 site-samples 缓存样本（out of scope，见 verification 缺口项）
