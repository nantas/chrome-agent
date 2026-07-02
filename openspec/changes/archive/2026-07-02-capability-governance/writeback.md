# Writeback

## Change: capability-governance

### Writeback Targets

| Target | Status | Detail |
|--------|--------|--------|
| `AGENTS.md` §0.5 C11 | ✅ Done | 新增约束：能力注册同步 |
| `docs/GOVERNANCE.md` §7 | ✅ Done | 派生文档同步原则 + 同步表 |
| `docs/playbooks/capability-extension.md` | ✅ Done | 创建（决策树 + gap report + 工作流）|
| `openspec/specs/capability-registry/` | ⚠️ Pending archive | Spec 在 change dir，归档时创建 |
| `openspec/specs/explore-workflow/` | ⚠️ Pending archive | Delta spec 已写，归档时合并 |
| `openspec/specs/governance/` | ⚠️ Pending archive | Delta spec 已写，归档时合并 |

### 未完成项

1. **Spec 归档**：`openspec/changes/capability-governance/specs/` 下的 spec 需在 `openspec archive` 时回写到 `openspec/specs/`
2. **doctor 全绿**：归档后 `doctor --check capabilities` 应无 warning

### 执行状态

所有 implementation 任务已完成。spec 归档为 openspec 归档流程的标准行为，在 `/opsx-archive` 时执行。
