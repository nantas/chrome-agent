# Proposal

## 问题定义

chrome-agent 的 openspec 开发流程与 TDD 方法论存在三个结构性脱节：

1. **opsx-apply 是 horizontal slicing**：`schema.yaml` 的 `apply.instruction` 只说"按顺序实现任务"，不要求先写测试。Agent 实现完全部代码后到 opsx-verify 才检查测试，结果是"先写代码最后补测试"的反模式。

2. **tasks 模板没有测试位置**：`templates/tasks.md` 的 §2 "核心实现任务"只有"拆分最小可交付实现任务"，不引导将测试作为每个任务的一部分。产生的 tasks.md 自然是纯实现任务列表。

3. **opsx-verify 不运行测试套件**：`~/.pi/agent/prompts/opsx-verify.md` 是硬编码的 8 步流程，从不调用 `scripts/test_runner.py`。J3 分级规则只在 verification.md 人工报告里出现，不在独立验证流程中自动执行。

4. **治理文档缺失 TDD 方法论**：`AGENTS.md` C9 和 `08-tech-stack.md` §4 说"要有测试"但没说"怎么写测试"。vertical slice、RED→GREEN、行为优先于实现等原则完全缺席。

## 范围边界

**In scope**：
- 修改 `schema.yaml` 的 `tasks.instruction`、`apply.instruction`、`verification.instruction` 注入 TDD + J3 规则
- 修改 `templates/tasks.md` §2 增加测试子任务引导
- 创建项目级 `.pi/prompts/opsx-verify.md` 增加 test_runner 运行 + J3 分级步骤
- 扩展 `AGENTS.md` C9 引用 TDD vertical slice 方法论
- 在 `08-tech-stack.md` §4 新增"TDD 约定"段落（转写 TDD skill 核心原则）

**Out of scope**：
- 修改全局 `~/.pi/agent/prompts/opsx-verify.md`（维护成本高，用项目级覆盖）
- 修改 openspec 框架源码（框架不支持 schema-level verification phase）
- 修改 `~/.agents/skills/tdd/SKILL.md`（TDD skill 内容不变，只引用）
- 创建新 schema（沿用 `orbitos-change-v1`）

## Capabilities

### New Capabilities
- `tdd-schema-injection`: 在 orbitos-change-v1 schema 的 tasks/apply/verification instruction 中注入 TDD vertical slice 约束和 J3 测试完备检查规则，使所有新 change 自动遵循 TDD 流程

### Modified Capabilities
- `test-runner`: 项目级 opsx-verify prompt 增加 test_runner 调用步骤，使独立验证自动运行测试套件并按 J3 分级报告结果
- `strategy-schema`: AGENTS.md C9 扩展引用 TDD vertical slice 方法论，08-tech-stack §4 新增 TDD 约定段落

## Capabilities 待确认项

- [x] 能力清单已确认——来自 grill session 逐项决策
- [x] 注入层级 L1（schema）+ 层 2（项目级 prompt）已确认
- [x] 条件排除纯文档任务已确认
- [x] TDD 方法论转写（不引用 skill 路径）已确认

## Impact

| 影响面 | 说明 |
|--------|------|
| `openspec/schemas/orbitos-change-v1/schema.yaml` | 修改 3 个 instruction 字段 |
| `openspec/schemas/orbitos-change-v1/templates/tasks.md` | §2 段落调整 |
| `.pi/prompts/opsx-verify.md` | 新建项目级覆盖 |
| `AGENTS.md` §0.5 C9 | 扩展引用 |
| `docs/architecture/08-tech-stack.md` §4 | 新增段落 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md 回写目标章节
