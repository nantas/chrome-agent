# Proposal: Explore KI Lifecycle

## 问题定义

在 explore 工作流的样本自检阶段，已知问题（Known Issues, KI）缺乏系统性的生命周期管理：

### 当前缺陷

| 缺陷 | 本 session 中的表现 |
|------|-------------------|
| **分类缺失** | KI-2（S5 版本号误报）归属不清——最初标记为"Self-Check"，但实际需要同时修改 strategy（entity ID 排除）和 self_check（URL hash 排除） |
| **优先级模糊** | 6 个 KI 同时存在，无明确的修复顺序。P0 问题（KI-6 ID 污染）和 P3 问题（KI-3 表格偏差）被同等对待 |
| **状态缺失** | strategy.md 的 Known Issues 表在 commit 55ac8d4 时只有 Issue/Impact/Mitigation 三列，无法追踪哪个问题已修复、哪个仍在排查 |
| **归属混乱** | KI-4（S8 模板标题）列在 strategy.md 中，但本质是 self_check 检查方法局限——表格中未区分"谁负责修" |
| **反模式** | 第一次修复 commit 55ac8d4 在架构违规未修复的情况下就写了 KI 表——KI 管理应在架构校验通过后、而非之前 |

### 期望行为

KI 应该有一个结构化的生命周期：

```
identified → classified → prioritized → fixed → verified → documented
                                    ↓
                              (not fixable)
                                    ↓
                              wontfix / open_systemic
```

## 范围边界

### 范围内

- KI 分类系统：按所有者域（strategy / pipeline / self_check）分类
- KI 优先级：P0（阻断接受）→ P3（装饰性/不可修复）
- KI 状态机：open → in_progress → resolved / wontfix / open_systemic
- strategy.md 的 Known Issues 表 schema 扩展（新增 Status、Owner、Priority 列）
- Agent 行为规则：KI 修复顺序、全量重测、迭代限制

### 范围外

- 不修改 S1-S12 检查项内容
- 不新增 self_check.py 检查项
- 不修改 sample_converter.py 转换逻辑

## Capabilities

### New Capabilities

- `explore-ki-lifecycle`: Known Issues 的生命周期管理——分类、优先级、状态追踪、修复验证流程

### Modified Capabilities

- `sample-self-check`: 自检结果中增加 KI 分类和优先级标注
- `explore-workflow`: 工作流增加 KI Lifecycle Phase（在 Architecture Gate 之后）
- `site-strategy`: 策略文件的 Known Issues 表 schema 扩展

## Impact

- **策略文件**: 所有包含 Known Issues 表的策略文件需扩展 schema（新增 3 列）
- **Agent 行为**: KI 修复遵循分类→优先级→顺序修复→全量重测流程
- **向下兼容**: 仅新增字段，不影响现有策略文件的解析
