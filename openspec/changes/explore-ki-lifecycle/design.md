# Design: Explore KI Lifecycle

## Overview

Known Issues (KI) 在 explore 工作流中产生于 Phase 1 的 self-check 失败。KI Lifecycle 定义了这些问题的分类、优先级、修复顺序和状态追踪规范。

## 工作流位置

KI Lifecycle 是 Architecture Gate 通过后的独立 Phase：

```
Phase 1: Self-Check → failures identified
         ↓
Phase 2: Architecture Gate → pass
         ↓
Phase 3: KI Lifecycle [NEW] ← from self-check failures
  ├── 3.1 Classify each failure as KI
  ├── 3.2 Assign Owner Domain (strategy/pipeline/self_check)
  ├── 3.3 Assign Priority (P0-P3)
  ├── 3.4 Fix in priority order (max 3 iterations total)
  ├── 3.5 Full retest after each fix
  └── 3.6 Document resolved/open KIs in strategy.md
         ↓
Phase 4: User Confirmation
```

## 3.1 KI 分类 (Owner Domain)

每个 KI 按**修复所在领域**分类，而非症状发生领域：

| Owner Domain | 定义 | 修复范围 | 示例 |
|-------------|------|---------|------|
| `strategy` | 问题应由更新 strategy.md 配置解决 | 仅修改 `sites/strategies/<domain>/strategy.md` | 添加 `cleanup_selectors`、调整 `infobox.selector` |
| `pipeline` | 问题应由更新管线代码解决（必须保持通用性，通过配置消费） | 修改 `scripts/explore/sample_converter.py` 或 `_extract_infobox` 等通用函数 | infobox nav 结构处理、链接空格修复 |
| `self_check` | 问题应由更新自检方法论解决（检查工具误报、范围失误） | 修改 `scripts/explore/self_check.py` | S5 版本号误报、S1 计数范围 |

### 分类决策树

```
self-check failure
├── 是管线转换的 bug？          → pipeline
│   (图片丢失、值拼接错误、nav 泄漏)
├── 是自检的方法论问题？         → self_check
│   (检查范围错误、正则误匹配、预期偏差)
├── 是策略配置不完整/不正确？    → strategy
│   (缺少 selector、skip_pattern 不完整)
└── 是转换引擎的系统性限制？     → open_systemic
    (markdownify 不渲染折叠模板)
```

## 3.2 优先级定义

| 优先级 | 条件 | 本 session 案例 |
|--------|------|---------------|
| **P0** | 阻断用户接受。导致关键数据损坏、丢失或严重错误 | KI-6: ID 显示 "None 1" 而非 "1" |
| **P1** | 影响内容质量但不阻断。可读性降低、轻微数据污染 | KI-5: 图片链接粘连无空格；KI-2: S5 误报 |
| **P2** | 检查工具问题。self_check 的误报或范围误差 | KI-1: S1 计数偏差 |
| **P3** | 装饰性/不触发。已在 skip 状态，或仅在特定条件下触发 | KI-3: S6 skip；KI-4: S8 已 pass |

### 优先级决策规则

1. **数据正确性 > 格式美观 > 检查精度**
2. 任何导致 infobox 字段值错误 → P0
3. 任何导致 markdown 链接/图片不可用 → P0
4. self_check 的误报 → 最高 P1（不阻断接受但浪费调试时间）
5. 已在 skip 状态的检查 → P3（自动降级）

## 3.3 KI 状态机

```
┌──────┐    classified    ┌──────────┐    fixed & verified    ┌──────────┐
│ open │ ───────────────> │ in_progress│ ──────────────────> │ resolved │
└──────┘                  └──────────┘                        └──────────┘
    │                           │                                   │
    │  (determined            │  (3 iterations                 │
    │   not fixable)           │   exhausted)                    │
    ▼                           ▼                                   │
┌───────────────┐     ┌─────────┐                          ┌──────────────┐
│ open_systemic │     │ wontfix │                          │ See strategy │
│ (engine limit)│     │(accepted)│                          │ KI table     │
└───────────────┘     └─────────┘                          └──────────────┘
```

状态转换条件：

- `open` → `in_progress`: 分类和优先级已确定，开始修复
- `in_progress` → `resolved`: 修复提交 + full retest 通过
- `open` → `open_systemic`: 确认为引擎/转换工具系统性限制，不可在当前层级修复
- `open` → `wontfix`: 用户明确接受（成本 > 收益）
- `in_progress` → `wontfix`: 3 次迭代后仍未修复，用户选择接受

## 3.4 修复顺序与迭代

### 修复顺序

1. **P0 问题优先** — 批量修复所有 P0 KI（可并行）
2. 全量重测 → 验证 P0 修复
3. **P1 问题** — 批量修复所有 P1 KI
4. 全量重测 → 验证 P1 修复
5. **P2/P3 问题** — 视时间修复

### 迭代计数

- 每完成一个优先级批次的修复 + 全量重测 = 1 次迭代
- 总计最多 3 次迭代（覆盖 P0 + P1 + P2 三个批次）
- Architecture Gate 违规修复 **不计入** 迭代计数

## 3.5 Known Issues Table Schema

strategy.md 的 Known Issues 表扩展为：

```markdown
## Known Issues (Post-Validation)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | S1 image count mismatch | open_systemic | P2 | self_check | Template-internal images not rendered | markdownify limitation — not fixable |
| KI-2 | S5 version regex false positive | resolved | P1 | self_check | Image URL hashes matched as version | Self-Check: strip `![](...)` from scan |
```

### 列定义

| Column | Values | Description |
|--------|--------|-------------|
| ID | `KI-N` | 自增序号，每个站点独立编号 |
| Issue | 描述 | 问题一句话摘要 |
| Status | `open` / `in_progress` / `resolved` / `wontfix` / `open_systemic` | 当前状态 |
| Priority | `P0` / `P1` / `P2` / `P3` | 修复优先级 |
| Owner | `strategy` / `pipeline` / `self_check` | 修复归属域 |
| Impact | 描述 | 对输出质量的实质影响 |
| Resolution | 描述 | 如何修复（或为何不修复） |

## Agent 行为规则

1. KI 分类和优先级判定 **MUST** 在 Architecture Gate 通过后进行
2. KI 修复**必须**按 P0 → P1 → P2 → P3 顺序，不可跳级
3. 每批修复后**必须**全量重测 ALL 样本
4. KI 表**必须**在 strategy.md 中更新，不可仅在 agent 内存中跟踪
5. `open_systemic` KI **必须**标注根因（引擎/工具/方法论的哪个限制）
6. 3 次迭代后仍有未修复 KI → 提交用户决策（continue/accept/adjust）
