# Writeback

## 回写摘要

- change：`explore-ki-lifecycle`
- 回写结论：KI Lifecycle 设计完成，行为规范冻结，待实现。将 KI 的分类、优先级、状态追踪和顺序修复流程标准化为 explore 工作流的 Phase 3。
- 关键结果：6 个 KI 按所属域（strategy/pipeline/self_check）和优先级（P0-P3）系统化管理，状态可追踪，修复顺序可控。

## Capability / Spec 增量摘要

| Capability | 变更类型（New/Modified/Removed/Renamed） | 对应 spec 文件 | 增量摘要 |
| --- | --- | --- | --- |
| `explore-ki-lifecycle` | New | `specs/explore-ki-lifecycle/spec.md` | 新增 KI 生命周期管理：分类（owner domain）、优先级（P0-P3）、状态机、顺序修复、文档追踪 |
| `sample-self-check` | Modified | `../../specs/sample-self-check/spec.md` | 自检输出增加 KI 分类和优先级标注 |
| `explore-workflow` | Modified | `../../specs/explore-workflow/spec.md` | 工作流增加 KI Lifecycle Phase（Phase 3） |
| `site-strategy` | Modified | `../../specs/site-strategy/spec.md` | KI 表 schema 扩展：Status/Priority/Owner/Resolution 列 |

## 验证结论与证据入口

| 验证维度 | 结论 | 证据入口 |
| --- | --- | --- |
| Spec-to-Implementation | 6/6 requirements 有对应 design + tasks | `verification.md` §Spec-to-Implementation |
| Task-to-Evidence | 全部 task 有验证方式定义 | `verification.md` §Task-to-Evidence |

## 回写目标与字段映射

| 目标页 | 同步字段/区块 | 回写内容 |
| --- | --- | --- |
| `openspec/specs/explore-ki-lifecycle/spec.md` | 整体 | 实现完成后从 change 归档到 frozen spec |
| `openspec/specs/sample-self-check/spec.md` | auto-remediation-extended | KI 分类字段附加到 check 输出 |
| `openspec/specs/explore-workflow/spec.md` | Phase 3 章节 | 新增 KI Lifecycle requirement |
| `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` | Known Issues 表 | 7 列表格 (已部分更新) |
| `.agents/skills/chrome-agent/SKILL.md` | Agent Gate 章节 | 新增 Gate #7 规则描述 |
| `AGENTS.md` | 治理规则 | KI 生命周期治理规则摘要 |

## 回写执行结果

| 目标页 | 执行结果（成功/失败/跳过） | 执行时间 | 执行人 | 结果说明/链接 |
| --- | --- | --- | --- | --- |
| `openspec/specs/explore-ki-lifecycle/spec.md` | 跳过（归档时执行） | — | — | 等待 `/opsx-apply` 实现后归档 |
| `openspec/specs/sample-self-check/spec.md` | 跳过 | — | — | 同上 |
| `openspec/specs/explore-workflow/spec.md` | 跳过 | — | — | 同上 |
| `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` | **已部分完成** | 2026-05-17 | agent | KI 表已扩展至 7 列，commit 08e3ea9 |
| `.agents/skills/chrome-agent/SKILL.md` | 跳过 | — | — | 同上 |
| `AGENTS.md` | 跳过 | — | — | 同上 |

## 回写前置条件

- [x] 已读取 `spec_standard_ref`
- [x] `verification.md` 已生成且无阻塞项
- [x] 回写目标页已确认存在且可编辑
- [x] capability/spec 增量摘要已核对 proposal 与 specs 一致

## 不回写的内容

- 不复制完整 `proposal.md`、`design.md`、`specs/*/spec.md`、`tasks.md` 正文
- 不写与本次 change 无关的历史信息
