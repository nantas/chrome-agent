# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md`、`docs/architecture/04-cli-reference.md`、`docs/architecture/05-converter-architecture.md`、`docs/architecture/07-explore-workflow.md`、`docs/architecture/08-tech-stack.md`
- `additional_context_refs`: `CONTEXT.md`、`CONTEXT-MAP.md`、`docs/GOVERNANCE.md`、`docs/adr/0013-four-dimensional-domain-model.md`、`docs/playbooks/chrome-agent-global-install.md`、`handoffs/20261003-crawl-darkestdungeon-wiki-gg-dd2/handoff.md`

## Source of Truth

- 行为规范真源：本 change 的 `specs/convert/spec.md`、`specs/fetch-strategy-selector/spec.md`、`specs/explore-workflow/spec.md`；归档回填对应永久规范。
- 项目页面仅承担上下文输入、治理展示与结果回写，不替代 spec delta。
- 维度：convert / scrapling_traversal / config_driven / HTML 为共享 convert 内核的镜像；self_check 属 explore 质量验证，不建立站点转换器分叉。

## 回写目标

- `writeback_targets`: 上述五份 architecture 项目页面；`CONTEXT-MAP.md`（crawl 到共享内核及自检来源边界）。
- `writeback_owner`: 本 change 实施者。
- `writeback_timing`: 实现及验证后、归档前；先读取 `spec_standard_ref`。

## 同步约束

- 页面与 spec 冲突时以 specs 为准；只回写结论、状态与证据链接。
- 新增能力实现模块同步 `configs/capability-registry.yaml` 与等价证明；归档前通过 capabilities doctor。
- 修改 CLI 触发 C10，按全局安装 playbook 同步 runtime/skill 并将 installed-hash 刷新为当前 HEAD；不将 CLI 误复制成 launcher。
- 保留已有未提交策略、registry、DD2 样本和 handoff；不修改其他 active change。
- 外部标准引用沿用最近归档 change 的 binding；本次提案未执行治理回写，不声称已读取该外部标准。

## 待确认项

- 无阻塞项。用户于 2026-10-03 确认 P-1～P-4 合并一个 change，并明确同意已匹配策略转换失败时禁止通用降级。
- 实施后回写前验证外部标准可解析并读取；不可访问时记录缺口。
