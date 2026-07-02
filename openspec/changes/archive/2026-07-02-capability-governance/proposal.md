# Proposal

## 问题定义

chrome-agent 的能力扩展主要来自 explore 工作流——发现新站点时，agent 倾向于"先爬下来再说"，功能开发与 explore 耦合在一起，导致：

1. **能力不可见**：没有机器可读的能力注册表。新代码写了、新 cleanup op 加了，但除作者无人知晓
2. **架构退化的入口敞开**：没有机制阻止 agent 在 explore 过程中突破架构边界（如建 `xxx_html_to_markdown.py` 绕过 shared kernel）
3. **文档与代码漂移**：SSOT（代码/配置）变更后，派生文档（AGENTS.md §2、architecture docs、specs）无自动检查机制
4. **缺少能力扩展工作流**：explore 发现新能力需求时，没有标准的 "产 gap report → 走 openspec change" 流程，只能直接写 strategy.md

根因：**能力注册和治理没有成为架构的一部分**——有代码、有文档，但中间缺少一个可验证的 SSOT 层。

## 范围边界

**包含**：
- 新增 `configs/capability-registry.yaml` 作为能力注册 SSOT
- 新增 `scripts/explore/capability_gate.py` 检查探索需求是否被已有能力覆盖
- 修改 `scripts/explore/freeze.py` 集成 capability gate 阻断
- 新增 `chrome-agent doctor --check capabilities` 检查项
- 新增 AGENTS.md C11 约束 + GOVERNANCE.md §7 派生文档同步原则
- 新增 `docs/playbooks/capability-extension.md` 操作手册

**不包含**：
- 不修改 openspec change 归档流程（doctor 检查作为归档前手动步骤）
- 不添加 CI 集成（目前无 CI）
- 不修改 explore CLI 的其他子命令

## Capabilities

### New Capabilities

- `capability-registry`: 机器可读的能力注册表 + doctor 一致性检查

### Modified Capabilities

- `explore-workflow`: freeze 前集成 capability gate 阻断；新增 capability_gate 模块
- `governance`: 新增 C11 硬件约束；新增派生文档同步原则

## Impact

| 受影响的文件 | 变更类型 |
|-------------|---------|
| `configs/capability-registry.yaml` | 新增（SSOT） |
| `scripts/explore/capability_gate.py` | 新增 |
| `scripts/explore/freeze.py` | 修改（集成 gap check） |
| `scripts/chrome-agent-cli.mjs` | 修改（新增 doctor capabilities 检查） |
| `AGENTS.md` §0.5 | 新增 C11 |
| `docs/GOVERNANCE.md` | 新增 §7 |
| `docs/playbooks/capability-extension.md` | 新增 |

## 关联绑定

- 关联 binding: [binding.md](./binding.md)
