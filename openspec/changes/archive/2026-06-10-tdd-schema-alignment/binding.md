# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: Orbitos Spec Standard v0.3（`openspec/specs/` 下现有冻结能力规范）
- `project_page_ref`:
  - `AGENTS.md` §0.5 C9 测试义务（扩展引用 TDD 方法论）
  - `docs/architecture/08-tech-stack.md` §4（新增 TDD 约定段落）
  - `openspec/schemas/orbitos-change-v1/schema.yaml`（tasks/apply/verification instruction 修改）
  - `openspec/schemas/orbitos-change-v1/templates/tasks.md`（模板结构调整）
  - `.pi/prompts/opsx-verify.md`（项目级覆盖，增加 test_runner + J3）
- `additional_context_refs`:
  - `~/.agents/skills/tdd/SKILL.md`（TDD 方法论真源，转写引用到 08-tech-stack）
  - `~/.pi/agent/prompts/opsx-verify.md`（全局 verify prompt，了解当前硬编码逻辑）

## Source of Truth

- 行为规范真源：`openspec/changes/tdd-schema-alignment/specs/` 下的能力规范文件
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §0.5 C9：扩展引用 TDD vertical slice 方法论
  - `docs/architecture/08-tech-stack.md` §4：新增"TDD 约定"段落（转写 TDD skill 核心原则）
  - `openspec/schemas/orbitos-change-v1/schema.yaml`：修改 `tasks.instruction`、`apply.instruction`、`verification.instruction`
  - `openspec/schemas/orbitos-change-v1/templates/tasks.md`：§2 增加测试子任务引导
  - `.pi/prompts/opsx-verify.md`：新增步骤 3.5（运行 test_runner + J3 分级）
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: implement 阶段完成后，verification 通过后回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（Orbitos Spec Standard v0.3）
- [x] 已确认项目页引用（AGENTS.md + 08-tech-stack + schema.yaml + template + 项目级 prompt）
- [x] 已确认回写目标与权限（五处修改，均在本仓库内）
- [x] 已确认异常处理与冲突策略（schema 条件排除纯文档任务，J3 分级）
