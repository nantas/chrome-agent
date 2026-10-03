# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md`、`docs/architecture/03-strategy-schema.md`、`docs/architecture/05-converter-architecture.md`、`docs/architecture/07-explore-workflow.md`、`docs/architecture/08-tech-stack.md`
- `additional_context_refs`: `CONTEXT.md`、`CONTEXT-MAP.md`、`docs/GOVERNANCE.md`、`docs/adr/0013-four-dimensional-domain-model.md`、`handoffs/20261003-crawl-darkestdungeon-wiki-gg-dd2/handoff.md`、`openspec/changes/archive/2026-10-03-fix-crawl-strategy-conversion-and-self-checks/verification.md`

## Source of Truth

- 行为规范真源：本 change 的 `specs/convert/spec.md`、`specs/explore-workflow/spec.md`、`specs/strategy-schema/spec.md`；归档时同步永久规范。
- 项目页面只承担上下文输入、治理展示与结果回写，不替代 spec delta。
- convert 内核与预处理共享所有执行路径；站点变体经配置声明，不另建 DD2 转换器。

## 回写目标

- `writeback_targets`: 上述五个 architecture 页面，以及 `CONTEXT-MAP.md` 中共享转换/来源审计边界；handoff 仅补充状态与证据，保留历史现场记录。
- `writeback_owner`: 本 change 实施者。
- `writeback_timing`: 实施验证后、归档前；回写前解析并读取 `spec_standard_ref`。

## 同步约束

- 冲突以 specs 为准，页面只回写摘要、状态和证据链接。
- 采用既有本地治理绑定；提案阶段不执行跨仓回写。
- 新增能力配置/模块时同步 capability registry、schema 及等价测试；归档前 capabilities doctor 通过。
- 修改 CLI/runtime/skill 时才触发 C10 全局同步；本提案不要求为离线验证修改 CLI。
- 当前 P-5～P-7 的 preprocessor、配置、测试和 DD2 样本为未提交工作；实施前记录快照，按本 change 评估并显式接纳相关部分，不覆盖无关并行改动。
- 永久规范和生产代码在本提案阶段不修改；实施后不自动重新抓取或发布正式采集产物。

## 待确认项

- 无阻塞项。用户要求按已讨论方案创建单一 change，授权范围覆盖根因修复、自检、标题规范化与离线全量验证。
- 标准引用沿用上一 change；实施回写时重新验证可访问性，无法读取则记录回写缺口。
