# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 3 个 capability spec 文件已创建且无占位符（`tdd-schema-injection`, `test-runner`, `strategy-schema`）

## 2. 核心实现任务

### 2.1 Schema instruction 注入（`tdd-schema-injection`）

- [x] 2.1.1 修改 `openspec/schemas/orbitos-change-v1/schema.yaml` 的 `tasks` artifact instruction
  - 增加规则：涉及代码的任务必须拆为 vertical slice（测试子任务 → 实现子任务 → 通过）；纯文档任务可独立存在
  - 验证：创建一个测试 change，确认 `openspec instructions tasks --change <test>` 输出包含 vertical slice 规则

- [x] 2.1.2 修改 `schema.yaml` 的 `apply` phase instruction
  - 增加规则：涉及代码的任务遵循 TDD——先写/更新测试（RED）→ 实现（GREEN）→ 重构；纯文档任务直接执行
  - 验证：`openspec instructions apply --change <test>` 输出包含 TDD 约束

- [x] 2.1.3 修改 `schema.yaml` 的 `verification` artifact instruction
  - 增加 J3 测试完备检查规则：新增模块无测试 = CRITICAL；修改模块未更新测试 = WARNING；纯文档变更不检查
  - 验证：`openspec instructions verification --change <test>` 输出包含 J3 规则

### 2.2 Tasks template 调整（`tdd-schema-injection`）

- [x] 2.2.1 修改 `openspec/schemas/orbitos-change-v1/templates/tasks.md` §2
  - §2 段落增加引导："涉及代码的任务拆为 vertical slice：每个任务包含测试子任务（RED）和实现子任务（GREEN）"
  - 保持弹性骨架，不强制固定段落格式
  - 验证：模板文件 review

### 2.3 项目级 opsx-verify prompt（`test-runner`）

- [x] 2.3.1 创建 `.pi/prompts/opsx-verify.md` 项目级覆盖
  - 基于全局 prompt，在步骤 3 后增加步骤 3.5：
    - 检查 `scripts/test_runner.py` 是否存在
    - 运行 `python3 scripts/test_runner.py all`
    - 按 J3 分级将结果纳入验证报告（新增模块无测试 = CRITICAL，修改模块未更新测试 = WARNING）
  - 验证：对已完成 change 运行 `/opsx-verify`，确认测试结果出现在报告中

### 2.4 治理文档更新（`strategy-schema`）

- [x] 2.4.1 扩展 `AGENTS.md` §0.5 C9
  - 约束文本追加："代码任务遵循 vertical slice TDD（详见 `08-tech-stack.md` §4 TDD 约定）"
  - 验证：文档 review

- [x] 2.4.2 在 `docs/architecture/08-tech-stack.md` §4 新增"TDD 约定"段落
  - 四条原则：vertical slice、anti-horizontal slicing、behavior over implementation、refactor after GREEN
  - 每条配简短说明
  - 验证：文档 review

## 3. 收敛与验证准备

- [x] 3.1 运行 `openspec schema validate orbitos-change-v1` 确认 schema 仍有效
- [x] 3.2 运行 `python3 -m unittest discover -s tests -v` 确认现有测试未受影响
- [x] 3.3 创建测试 change，验证全链路：`openspec instructions tasks` 含 TDD → `openspec instructions apply` 含 TDD → `openspec instructions verification` 含 J3

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 `verification.md`
- [x] 4.2 基于 verification 结论生成 `writeback.md`
- [x] 4.3 执行文档回写（见 2.1-2.4），记录回写证据
