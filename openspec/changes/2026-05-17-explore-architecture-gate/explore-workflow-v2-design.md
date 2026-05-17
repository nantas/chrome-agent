# Explore 工作流完整设计（v2）

> 基于 2026-05-17 session 复盘，融合 Architecture Gate 和 KI Lifecycle 两个新 Phase。

## 阶段总览

```
Phase 0: EXPLORE & DISCOVERY          Phase 1: SAMPLE CONVERSION
┌────────────────────────────┐        ┌──────────────────────────────┐
│ ┌─ doctor preflight        │        │ ┌─ select 2-6 samples        │
│ ├─ engine chain probe      │   ──→  │ ├─ fetch via engine/api     │
│ ├─ API discovery           │        │ ├─ convert (extraction_rules)│
│ ├─ structure mapping       │        │ ├─ run S1-S12 self-checks   │
│ ├─ protection identify     │        │ ├─ auto-remediation (≤2)    │
│ └─ scaffold generate       │        │ └─ present self-check report│
└────────────────────────────┘        └──────────────────────────────┘
                                                       │
                                                       ▼
Phase 2: ARCHITECTURE GATE [NEW]       Phase 3: KI LIFECYCLE [NEW]
┌──────────────────────────────┐       ┌──────────────────────────────┐
│ Check 1: Strategy→Pipeline   │       │ ┌─ classify by owner domain  │
│  - dead config detection     │       │ ├─ assign priority (P0-P3)  │
│  - every field has consumer  │  ──→  │ ├─ fix P0 batch             │
│                              │       │ │   → full retest (iter 1)   │
│ Check 2: Pipeline→Strategy   │       │ ├─ fix P1 batch             │
│  - agent audit checklist     │       │ │   → full retest (iter 2)   │
│  - zero hardcoded selectors  │       │ ├─ fix P2 batch             │
│  - zero unconditional ops    │       │ │   → full retest (iter 3)   │
│                              │       │ └─ document in strategy.md   │
└──────────────────────────────┘       └──────────────────────────────┘
         │ FAIL: fix + retest                       │
         └────────────────────┐                     ▼
                              │       Phase 4: USER CONFIRMATION
                              │       ┌──────────────────────────────┐
                              └──────→│ ┌─ present final samples     │
                                      │ ├─ self-check summary        │
                                      │ ├─ architecture gate result  │
                                      │ ├─ KI resolution status      │
                                      │ └─ user confirms quality      │
                                      └──────────────────────────────┘
                                                       │
                                                       ▼
                                              Phase 5: FREEZE
                                              ┌──────────────────────┐
                                              │ ├─ freeze strategy    │
                                              │ ├─ update registry    │
                                              │ └─ generate report    │
                                              └──────────────────────┘
```

## Phase 2: Architecture Gate 详细

### 目标

防止 commit 55ac8d4 型违规：策略和管线各自独立演化，缺乏双向对齐校验。

### Gate 的两个检查

| # | 检查方向 | 方法 | 失败示例 |
|---|---------|------|---------|
| 1 | **策略→管线** | 程序化 schema 校验 | strategy 有 `wiki_gg_specific` block，pipeline 无消费者 |
| 2 | **管线→策略** | Agent 审计清单 (5 项) | pipeline 硬编码 `"aside.portable-infobox"`，strategy 无配置源 |

### Gate 输出

```json
{
    "architecture_gate": {
        "status": "pass",
        "strategy_to_pipeline": { "status": "pass", "dead_config": [] },
        "pipeline_to_strategy": { "status": "pass", "violations": [] }
    }
}
```

### Agent 行为规则

- Gate **必须** pass 才能进入 Phase 4
- Gate 违规修复**不计入** 3-iteration 限制
- Gate 违规修复后**必须**全量重测

---

## Phase 3: KI Lifecycle 详细

### 目标

系统性管理自检失败产生的已知问题，按归属、优先级分类，有序修复和追踪。

### 分类体系

```
self-check failure
├── pipeline bug?    → Owner: pipeline, fix in sample_converter.py
├── check false pos? → Owner: self_check, fix in self_check.py
├── config missing?  → Owner: strategy, fix in strategy.md
└── engine limit?    → Status: open_systemic, document limitation
```

### 优先级

| P | 条件 | 案例 |
|---|------|------|
| P0 | 数据损坏、链接/图片不可用 | KI-6: Collectible ID "None 1" |
| P1 | 可读性降低、轻微污染、检查误报 | KI-5: 图片链接粘连；KI-2: S5 误报 |
| P2 | 检查方法论问题 | KI-1: S1 计数范围 |
| P3 | skip/装饰性 | KI-3/4: S6/S8 已 skip/pass |

### 修复顺序

```
P0 batch → full retest (iteration 1)
  ↓ pass
P1 batch → full retest (iteration 2)
  ↓ pass
P2 batch → full retest (iteration 3)
  ↓
KI table updated in strategy.md → Phase 4
```

### KI 状态机

```
open → in_progress → resolved
                  → wontfix (user accepts)
open → open_systemic (engine limitation)
```

---

## Agent Gate 规则汇总

| # | Gate | 来源 | 描述 |
|---|------|------|------|
| 1 | Self-check first | explore-skill-gates | 自检报告先于样本内容展示 |
| 2 | File paths | explore-skill-gates | 样本写入 `outputs/<run>/` 并列出路径 |
| 3 | Self-audit | explore-skill-gates | Agent 自行对比审查后再请用户 review |
| 4 | Full retest | explore-skill-gates | 修改 converter 后全量重测所有样本 |
| 5 | Iteration limit | explore-skill-gates | fix→retest→present 最多 3 次 |
| **6** | **Architecture Gate** | **NEW** | **策略↔管线双向对齐校验，pass 才能确认** |
| **7** | **KI Lifecycle** | **NEW** | **KI 按归属/优先级有序修复，状态文档化** |

---

## 本 Session 工作流对照

| 阶段 | 本 session 实际操作 | 设计后应如何 |
|------|-------------------|------------|
| 探索 | `explore` 命中已有策略 → 跳过 scaffold | 同 |
| 样本转换 | 20 个样本 V1→V4 迭代 | 同，但自检报告应先展示 |
| **架构校验** | ❌ **缺失** → 导致 commit 55ac8d4 revert | ✅ Gate 检查策略↔管线对齐 |
| KI 管理 | 手动在 agent 内存中追踪，最后才写表 | ✅ Phase 3: 分类→优先级→顺序修复→document |
| 用户确认 | V4 接受（但架构违规未发现） | ✅ Gate + KI 都通过后才确认 |
| Freeze | commit 55ac8d4（违规）→ d301cd0（revert）→ 4c1a589（修复） | ✅ 一次正确 commit |
