# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `docs/architecture/07-explore-workflow.md`, `docs/architecture/03-strategy-schema.md`, `docs/architecture/08-tech-stack.md`
- `additional_context_refs`: `CONTEXT.md`, `docs/GOVERNANCE.md`, `docs/adr/0013-four-dimensional-domain-model.md`, `configs/capability-registry.yaml`, `scripts/lib/extraction/schema.py`
- 诊断来源：`outputs/handoffs/20261002T103634-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/handoff.md`。
- 离线复现：`outputs/debug/20261002-scaffold-schema/repro.py`；该文件为本地忽略产物，实施时转为 tests 回归用例。

## Source of Truth

- 本 change 行为规范真源：`specs/explore-scaffold/spec.md`。
- 现有行为规范：`openspec/specs/explore/explore-scaffold.md` 的 template-content、auto-remediation-extended、ki-lifecycle-consumption；`openspec/specs/explore-scaffold/spec.md` 的样本推荐契约保持原样。
- cleanup 名称与实现真源：`configs/capability-registry.yaml`；schema 负责准入，生产端必须与其一致。
- 项目页面只承担上下文输入、治理展示与结果回写，不替代 specs 作为实现/验证依据。

## 回写目标

- `writeback_targets`:
  - `docs/architecture/07-explore-workflow.md`：模板配置准入、自动修复支持边界与 iterate 校验失败行为。
  - `docs/architecture/03-strategy-schema.md`：cleanup、cleanup_selectors、lazyload 的生产端约定。
  - `docs/architecture/08-tech-stack.md`：模板全集与真实生成/修复链路的回归覆盖。
  - `openspec/specs/explore/explore-scaffold.md`：归档时合并对应 requirement 块和新增 producer 准入要求，保留其它内容。
- `writeback_owner`: 本 change 执行者。
- `writeback_timing`: 实现验证完成后回写架构页；归档时合并冻结规范。

## 同步约束

- 页面与 specs 冲突时以 specs 为准，回写结论/状态/证据链接，不复制整份 artifact。
- 禁止为满足旧配置而降低 schema 严格度或只注册没有实现的 cleanup 名称。
- 默认不新增能力模块；如实施确需新增能力实现文件，执行 C11 注册同步与测试义务，归档前通过 capabilities 检查。
- 本次预期不修改 runtime/CLI/skill；若实际触及 C10 tracked files，必须同步全局副本及 installed-hash。
- 本仓回写目标已明确，不新增外部项目页回写；回写前按 spec_standard_ref 读取标准。

## 待确认项

- [x] 2026-10-02 用户回复“确认”，本 change 能力归属为已有 `explore-scaffold`，覆盖模板、反馈迭代及样本自动修复的配置生产契约。
- 实施时结合可定位的配置/样本证据决定 lazyload 修复是否可执行；不猜测属性或补造消费者能力。
