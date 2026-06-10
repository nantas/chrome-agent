# Design

## Context

chrome-agent 已通过 testing-governance change 建立了测试基础设施（`tests/` 目录、`test_runner.py`、站点样本回归、C9 硬约束）。但 openspec 开发流程（schema → proposal → specs → design → tasks → apply → verify）与 TDD 方法论之间存在脱节——opsx-apply 不引导测试先行，opsx-verify 不运行测试套件，治理文档不描述 TDD 方法。

本次 change 不新增代码功能，纯粹对齐 schema + 治理文档。

## Goals / Non-Goals

**Goals:**
- 让 schema 的 instruction 字段自动引导 TDD 流程（所有新 change 生效）
- 让 opsx-verify（项目级）自动运行测试套件并按 J3 分级报告
- 让治理文档（AGENTS.md、08-tech-stack）明确 TDD 方法论
- 条件排除纯文档任务（不强制测试）

**Non-Goals:**
- 不修改 openspec 框架源码（框架不支持 schema-level verification phase）
- 不修改全局 `~/.pi/agent/prompts/opsx-verify.md`（用项目级覆盖）
- 不修改 TDD skill 本身
- 不新增代码模块或测试文件

## Decisions

### D1: Schema instruction 注入（L1 层）

**决策**: 修改 `orbitos-change-v1/schema.yaml` 的 3 个 instruction 字段。

- `tasks.instruction`：增加 vertical slice 分解规则 + 条件排除
- `apply.instruction`：增加 TDD RED→GREEN 执行约束 + 条件排除
- `verification.instruction`：增加 J3 测试完备检查规则 + 条件排除

**理由**: schema instruction 是 openspec 框架的一等机制——`openspec instructions apply` 直接返回 `apply.instruction` 给 agent。不需要改框架代码。

### D2: 项目级 opsx-verify prompt（层 2）

**决策**: 创建 `.pi/prompts/opsx-verify.md` 项目级覆盖，增加步骤 3.5 运行 `test_runner.py`。

**理由**: 全局 prompt 不能改（维护成本高），但 pi 支持项目级覆盖。`scripts/test_runner.py` 是 chrome-agent 特有的，放在项目级比全局合理。

### D3: TDD 方法论转写到 08-tech-stack

**决策**: 在 `08-tech-stack.md` §4 新增"TDD 约定"段落，转写 TDD skill 的 4 条核心原则（vertical slice、anti-horizontal、behavior over implementation、refactor after GREEN），不引用 skill 文件路径。

**理由**: 08-tech-stack 是人读文档，skill 是 agent 读的，受众不同。AGENTS.md C9 引用 08-tech-stack 而非 skill，保持人读文档的自包含性。

### D4: tasks template 微调

**决策**: `templates/tasks.md` §2 段落增加"测试"引导占位，但保持弹性骨架不强制固定段落。

**理由**: instruction 定规则，template 定骨架。模板太死板会迫使小 change 填无意义段落。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| Schema instruction 文本过长 | agent 上下文开销增加 | instruction 精炼，每条 <200 字 |
| 项目级 prompt 与全局 prompt 后续分化 | 全局 prompt 更新时需同步项目级 | 项目级只覆盖差异部分，不复制全文 |
| 纯文档任务误判为代码任务 | 浪费时间写无意义测试 | 条件排除规则基于文件扩展名判断 |
