# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/04-cli-reference.md`、`docs/architecture/08-tech-stack.md`
- `additional_context_refs`: `docs/GOVERNANCE.md`、`docs/playbooks/chrome-agent-global-install.md`、`openspec/specs/sitemap-driven-crawl/spec.md`、`outputs/handoffs/20261003T011045-crawl-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/handoff.md`

## Source of Truth

- 行为规范真源：本 change 的 `specs/sitemap-driven-crawl/spec.md`；归档后回填 `openspec/specs/sitemap-driven-crawl/spec.md`。
- 项目页面仅承担上下文输入、治理展示与结果回写，不替代 spec delta 作为实现与验证依据。
- 维度归属：discover / CLI sitemap discovery / generic / XML（gzip 为输入编码）；不新增独立业务能力或站点变体。

## 回写目标

- `writeback_targets`: `docs/architecture/04-cli-reference.md`（gzip 与错误证据行为）、`docs/architecture/08-tech-stack.md`（真实读取边界回归测试）。
- `writeback_owner`: 本 change 的实施者。
- `writeback_timing`: 实现验证通过后、归档前；先读取 `spec_standard_ref`，再按项目治理完成回写。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准；回写仅同步结论、状态、摘要与链接。
- 修改 CLI 后执行 C10：同步 runtime 与 skill 全局副本，installed-hash 刷新为当前 HEAD；CLI 本身不是全局复制目标。
- 保留工作区已有未提交变更；不修改站点策略或其他活动 change。
- 外部标准引用沿用近期已归档 change 的绑定；本轮仅创建提案，未读取外部标准，不声称已完成回写检查。

## 待确认项

- 无阻塞提案的范围问题：用户已确认通用 gzip 支持、回归测试及失败报告证据链接修正。
- 实施后回写前需验证上述外部标准可解析并读取；若无法访问，记录具体缺口，不伪称已完成。
