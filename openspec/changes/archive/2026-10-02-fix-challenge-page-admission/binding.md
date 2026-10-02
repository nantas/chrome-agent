# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md`, `docs/architecture/06-engine-selection.md`, `docs/architecture/07-explore-workflow.md`, `docs/architecture/04-cli-reference.md`
- `additional_context_refs`: `CONTEXT.md`, `docs/GOVERNANCE.md`, `docs/adr/0013-four-dimensional-domain-model.md`, `docs/playbooks/chrome-agent-global-install.md`
- 诊断入口：`outputs/handoffs/20261002T132315-crawl-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/handoff.md` 仅记录 strategy_gap；关联 probe HTML 与 `outputs/debug/20261002-extraction-config-validation/explore.json` 才证明挑战页误判。

## Source of Truth

- 本 change 的行为规范真源为 `specs/fetch-content-admission/spec.md` 和 `specs/explore/spec.md`。
- 现有 Explore 规范真源为 `openspec/specs/explore/explore-deep-discovery.md`；归档按 requirement 合并，不另建平行 explore/spec.md。
- 项目页面只承担上下文输入、治理展示与结果回写，不替代 spec delta。

## 回写目标

- `writeback_targets`: `docs/architecture/00-target-architecture.md`, `docs/architecture/06-engine-selection.md`, `docs/architecture/07-explore-workflow.md`, `docs/architecture/04-cli-reference.md`, `docs/architecture/08-tech-stack.md`, `CONTEXT.md`, `CONTEXT-MAP.md`。
- 归档目标：`openspec/specs/fetch-content-admission/spec.md`；`openspec/specs/explore/explore-deep-discovery.md`。
- `writeback_owner`: 本 change 执行者。
- `writeback_timing`: 实施验证后回写项目页面；归档时合并冻结规范。

## 同步约束

- 页面与 specs 冲突时以 specs 为准；回写结论、状态、摘要与证据链接，不复制整份 artifact。
- 新共享 fetch 准入模块须同步 capability registry、镜像关系及等价测试；归档前 doctor capabilities 通过。
- CLI 修改执行 C10 全局同步及 installed-hash 刷新；不升级引擎版本。
- 本地诊断 HTML 可能含临时挑战参数；正式 fixture 须脱敏、最小化，不依赖忽略目录。
- 保留已有 package-lock.json 改动及未跟踪站点草稿，不自动删除、覆盖或发布。
- 外部标准引用沿用前序归档 binding；本轮不执行外部回写，实施后的 writeback 前读取该标准。

## 待确认项

- 2026-10-02 用户要求基于已讨论方案创建 change；范围为共享准入、fallback、Explore 停止条件和 CLI 失败语义。
- 无阻塞设计项。HTML 受阻时独立 API 发现/恢复、站点策略发布、浏览器授权方式调整均不在范围内。
