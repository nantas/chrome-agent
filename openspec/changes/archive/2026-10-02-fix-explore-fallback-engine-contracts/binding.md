# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/06-engine-selection.md`, `docs/architecture/07-explore-workflow.md`, `docs/architecture/04-cli-reference.md`, `docs/architecture/08-tech-stack.md`。
- `additional_context_refs`: `docs/GOVERNANCE.md`, `CONTEXT.md`, `docs/playbooks/chrome-agent-global-install.md`, `openspec/changes/archive/2026-10-02-fix-challenge-page-admission/verification.md`。
- 实测基线：commit b3092c3；目标 https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1；运行目录 `outputs/20261002T142323-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1`。

## Source of Truth

本 change 的 `specs/` 为行为规范真源；项目页面仅承担上下文输入、治理展示与结果回写，不替代 delta spec。已有 Explore 真源为 `openspec/specs/explore/explore-deep-discovery.md`，doctor 既有聚合规范为 `openspec/specs/infra/doctor.md`。新增契约 supplement 不重定义 repo freshness 或内容准入规则。

## 回写目标

- `writeback_targets`: 上述四个 project_page_ref；永久规范 `openspec/specs/engine-execution-contracts/spec.md` 与 `openspec/specs/engine-health-reporting/spec.md`。
- `writeback_owner`: 本 change 执行者。
- `writeback_timing`: 实施验证后同步项目页面；归档前回填永久规范。

## 同步约束

- 页面与 specs 冲突以 specs 为准；回写摘要与证据链接，不复制整份 artifacts。
- CLI 修改执行 C10 全局同步与 installed-hash 刷新；新增能力实现文件执行 C11 注册，归档前 capabilities 通过。
- 不升级引擎版本；安装缺失环境遵循既有 preflight，不用升级绕开 CLI 参数错误。
- 保留 package-lock.json 的既有改动及未跟踪站点草稿。
- 回写前读取 spec_standard_ref；无外部项目页写入目标。

## 待确认项

用户在收到四项修复方案后要求创建 change，范围已明确。无阻塞项；真实页面最终是否取得正文须由实施后的复验决定，不能作为既定事实。
