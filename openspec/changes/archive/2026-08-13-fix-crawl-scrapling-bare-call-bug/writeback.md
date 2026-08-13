# Writeback

## 回写摘要

- change：`fix-crawl-scrapling-bare-call-bug`
- 回写结论：**PASS，无需对外项目页回写**。本 change 是 spec 内部能力修复，回写目标仅 `openspec/specs/`（归档时 spec delta 提升为 frozen）；无外部项目页/治理页需同步。
- 关键结果：修复 `scripts/lib/crawl_scrapling.mjs:328` 的裸调用缺陷（默认 crawl 路径的 `ReferenceError`）；在 `fetch` 能力的 `crawl-scrapling-orchestrator-is-a-seam-module` 契约上钉死调用点 `api.` 前缀纪律 + `markdown:true` 分支回归覆盖。

## Capability / Spec 增量摘要

| Capability | 变更类型（New/Modified/Removed/Renamed） | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `fetch` | Modified | `openspec/changes/fix-crawl-scrapling-bare-call-bug/specs/fetch/spec.md`（归档时提升为 `openspec/specs/fetch/spec.md` 的 frozen 增量） | MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`：新增 **Call-site discipline** 段（所有经 `api` bundle 注入的 helper SHALL 通过 `api.` 前缀引用，裸调用 FORBIDDEN）+ 2 个 scenario（`all-bundled-helpers-called-via-api-prefix`、`markdown-true-branch-produces-artifacts-not-reference-error`）；保留原 3 个 scenario |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | PASS — 5 个 scenario 全部有可执行证据 | `verification.md` § Spec-to-Implementation Coverage |
| Task-to-Evidence | PASS — 全部 task 完成，含回退验证（临时回退修复 → 2 测试失败含 ReferenceError；恢复 → 5/5 绿） | `verification.md` § Task-to-Evidence Coverage |
| 测试完备（J3） | PASS — 修改模块 `crawl_scrapling.mjs` 已有对应测试文件，且本次新增 2 用例 | `verification.md` § 缺口与阻塞项 |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `openspec/specs/fetch/spec.md`（归档提升） | `crawl-scrapling-orchestrator-is-a-seam-module` requirement | 归档时把本 change 的 MODIFIED requirement block 提升进 frozen spec（新增 Call-site discipline 段 + 2 scenario） |
| C10 全局副本（`~/.agents/scripts/...`） | — | **不回写**：本 change 不触碰 C10 tracked files（`git diff` 仅 `crawl_scrapling.mjs` + 测试） |

## 回写执行结果

| 目标页 | 执行结果（成功/失败/跳过） | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `openspec/specs/fetch/spec.md` | 跳过（归档时执行） | — | — | spec delta 提升在 `/opsx-archive` 归档步骤完成；当前 `verification.md` 已确认 delta 就绪 |
| C10 全局副本 | 跳过（不触发） | — | — | `git diff --name-only` 不含 tracked files；binding.md 已记录 C10 不触发 |
| 外部项目页（架构审查报告） | 跳过（外部临时文件） | — | — | `architecture-review-20260813-154550.html` 是 `/var/folders/...` 临时文件，无回写协议 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`（`docs/GOVERNANCE.md` §3、ADR 0013 §4.4、`crawl-scrapling-pages-scope/spec.md`）
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑（`openspec/specs/fetch/` 由归档流程管理）
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致（仅 Modified `fetch`）

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/fetch/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息（如原 extract change 的细节）
- 不回写架构审查报告（外部临时文件）
- 不触发 C10 全局同步（已核实）
