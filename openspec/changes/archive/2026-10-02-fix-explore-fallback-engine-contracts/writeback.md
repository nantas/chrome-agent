# Writeback

## 回写摘要

- change：fix-explore-fallback-engine-contracts。
- 回写结论：仓库内绑定目标已同步，apply 已完成；尚未归档或提交。
- 关键结果：修正 Obscura stdout 契约、CloakBrowser 懒预检与清单版本安装、doctor 错误传播和可选 readiness、Explore 诊断链。真实原站点经 CloakBrowser 得到正文，Explore 仍为待策略审查的 partial_success。

## Capability / Spec 增量摘要

| Capability | 类型 | 永久 spec | 增量 |
| --- | --- | --- | --- |
| engine-execution-contracts | New | openspec/specs/engine-execution-contracts/spec.md | stdout 获取、预检解析、各尝试阶段及证据、pending 与 handoff 边界 |
| engine-health-reporting | New | openspec/specs/engine-health-reporting/spec.md | 完整逐引擎报告、检查器协议校验、非阻塞可选缺失与阻塞异常 |

永久规范已按 ADDED requirements 回填，未重复定义已有安装、freshness 或正文准入要求。

## 验证结论与证据入口

| 维度 | 结论 | 证据 |
| --- | --- | --- |
| Spec-to-Implementation | 六项 requirement 均有实现与回归 | [verification.md](verification.md) 对应表 |
| Task-to-Evidence | RED/GREEN、全量回归与真实运行分开记录 | [verification.md](verification.md) 对应表与 evidence_map |
| 真实执行 | 挑战页均拒绝，CloakBrowser 正文通过；未冻结策略 | outputs/fallback-contracts-validation/explore-live.json |
| 健康与能力 | doctor/capabilities success | outputs/fallback-contracts-validation/doctor-after-live.json、capabilities.json |

## 回写目标与字段映射

| 目标 | 区块 | 内容 |
| --- | --- | --- |
| docs/architecture/06-engine-selection.md | Fallback 执行与版本就绪契约 | 两适配器调用、清单安装、可选 readiness |
| docs/architecture/07-explore-workflow.md | Probe 尝试证据 | 阶段、落盘、pending、handoff、后续 Gate |
| docs/architecture/04-cli-reference.md | doctor 健康报告与 Explore 诊断 | checks.blocking、dispatch_allowed、结果语义 |
| docs/architecture/08-tech-stack.md | 引擎执行契约回归 | 测试入口、隔离方式、真实契约验证限制 |
| openspec/specs/engine-execution-contracts/spec.md | Requirements | 三项 ADDED requirements |
| openspec/specs/engine-health-reporting/spec.md | Requirements | 三项 ADDED requirements |

## 回写执行结果

| 目标 | 结果 | 日期 | 执行人 | 说明 |
| --- | --- | --- | --- | --- |
| docs/architecture/06-engine-selection.md | 成功 | 2026-10-02 | Codex | 已追加适配和版本契约，并链接永久规范 |
| docs/architecture/07-explore-workflow.md | 成功 | 2026-10-02 | Codex | 已追加可复核尝试证据与 Gate 语义 |
| docs/architecture/04-cli-reference.md | 成功 | 2026-10-02 | Codex | 已记录健康字段及结果语义 |
| docs/architecture/08-tech-stack.md | 成功 | 2026-10-02 | Codex | 已记录测试边界及真实验证要求 |
| openspec/specs/engine-execution-contracts/spec.md | 成功 | 2026-10-02 | Codex | 三项 requirement 已回填 |
| openspec/specs/engine-health-reporting/spec.md | 成功 | 2026-10-02 | Codex | 三项 requirement 已回填 |

C10：已比对并同步 runtime 与 skill 全局副本，installed-hash 已刷新为当前 HEAD。CLI 仍由全局 launcher 指向仓库运行，不复制 CLI 到全局。引擎版本清单未变；没有新增实现模块需要注册。

## 回写前置条件

- [x] 已读取 binding 指定的 spec_standard_ref：repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md（本机 resolver 位置为 obsidian-mind 仓库）。
- [x] verification.md 已生成；本 change 的实现验证无阻塞项，站点草稿质量和本地 HTTP 限制已明确披露。
- [x] 仓库内目标存在且可编辑；新增 spec 目录随实际规范回填创建，不建立空壳。
- [x] capability/spec 增量与 proposal 一致。

本 change 按 repo-local binding 执行，无外部项目页写入目标；不声称完成跨仓治理页面同步。

## 不回写的内容

不把完整 proposal/design/tasks 复制到架构文档；不修改引擎版本清单、不升级既有引擎、不冻结或发布站点策略。package-lock.json 的既有修改、未跟踪站点草稿和 outputs 不纳入修复代码提交。

## 归档收尾

2026-10-02，用户授权归档并整理提交。21 项任务全部完成，两项永久规范与 delta requirements 一致，严格校验和 capabilities 检查通过。归档至 `openspec/changes/archive/2026-10-02-fix-explore-fallback-engine-contracts/`；提交范围仅含本 change 的代码、测试、规范和文档，排除既有 package-lock 修改与站点草稿。
