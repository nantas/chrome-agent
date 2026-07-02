# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `capability-registry` spec 的 ADDED requirements
- [x] 1.2 确认 `explore-workflow` spec 的 ADDED requirements
- [x] 1.3 确认 `governance` spec 的 ADDED requirements

## 2. 核心实现任务

### Task 2.1: 创建 capability-registry.yaml

- [x] 2.1.1 (审计) 列出 `preprocessor.py` 中所有已有的 cleanup op name
- [x] 2.1.2 (审计) 列出 `infobox.py` 中所有已有的 infobox handler name
- [x] 2.1.3 (审计) 列出所有已有的特殊 capability（card_stats, link_fixer 等）
- [x] 2.1.4 (实现) 创建 `configs/capability-registry.yaml`，按 convert/extract/fetch 分组

### Task 2.2: 创建 capability_gate.py

- [x] 2.2.1 (实现) 创建 `scripts/explore/capability_gate.py`
- [x] 2.2.2 (实现) 实现 `check_requirements(scaffold, registry)`，检查 cleanup ops + infobox handlers
- [x] 2.2.3 (实现) 返回标准 gap dict 格式：`[{capability, issue, detail}]`

### Task 2.3: freeze.py 集成 gap check

- [x] 2.3.1 (实现) 在 `scripts/explore/freeze.py` 中 strategy.md 写入前调用 `check_requirements`
- [x] 2.3.2 (实现) 检测到 gap 时写 `capability-gap.yaml` 并 exit 5
- [x] 2.3.3 (测试) 创建 test_freeze_gap.py 验证阻断和通过两种场景

### Task 2.4: doctor --check capabilities

- [x] 2.4.1 (实现) 在 `scripts/chrome-agent-cli.mjs` doctor 命令中新增 `capabilities` 子检查
- [x] 2.4.2 (实现) 校验 registry 的 `implemented_in` 路径存在性
- [x] 2.4.3 (实现) 校验 registry ↔ `openspec/specs/` 一致性
- [x] 2.4.4 (实现) 校验 registry ↔ `AGENTS.md` §2 一致性

### Task 2.5: 治理文档更新

- [x] 2.5.1 (实现) AGENTS.md §0.5 新增 C11 约束
- [x] 2.5.2 (实现) GOVERNANCE.md 新增 §7 派生文档同步原则
- [x] 2.5.3 (实现) 创建 `docs/playbooks/capability-extension.md`（决策树 + gap report 模板 + 工作流）

## 3. 收敛与验证准备

- [x] 3.1 `doctor --check capabilities` 对当前代码库通过（注册表完整）
- [x] 3.2 `freeze.py` 在当前已注册网站策略上不阻断
- [x] 3.3 `capability_gate.py` 单元测试通过
- [x] 3.4 `python3 scripts/test_runner.py all` 全绿

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`
- [x] 4.2 生成 `writeback.md`
- [x] 4.3 执行 writeback
