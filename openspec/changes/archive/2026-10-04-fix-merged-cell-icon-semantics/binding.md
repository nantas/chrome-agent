# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/05-converter-architecture.md`、`docs/architecture/03-strategy-schema.md`
- `additional_context_refs`: `docs/GOVERNANCE.md`、`openspec/changes/fix-conversion-structure-and-audit-fidelity/verification.md`、`handoffs/20261003-crawl-darkestdungeon-wiki-gg-dd2/handoff.md`

## Source of Truth

- 行为规范真源为本 change 的 `specs/`，归档时合并至永久规范。
- 项目页面只承担上下文输入、治理展示与结果回写，不替代 spec delta。

## 回写目标

- `writeback_targets`: 上述两个 architecture 页面及原 handoff 的 Crypt Keeper 后续状态。
- `writeback_owner`: 本 change 实施者。
- `writeback_timing`: 验证后、归档前；执行前解析并读取 spec_standard_ref。

## 同步约束

- 页面与 spec 冲突以 specs 为准；回写结论、状态、证据，不复制完整方案。
- 依赖 fix-conversion-structure-and-audit-fidelity 的实现及审计入口；实施前定位其当前状态（active 或 archive），保存工作区快照，不覆盖已有修改。两个 change 按前置、后续顺序同步规范。
- 新配置同步 schema、能力注册和文档；归档前 capabilities doctor 通过。仅本地回写，不涉及跨仓发布。
- 不自动重抓、覆盖正式 collection、提交或归档前置 change。

## 待确认项

无阻塞项。用户已要求按讨论方案创建后续 change；本阶段只生成实施前产物。
