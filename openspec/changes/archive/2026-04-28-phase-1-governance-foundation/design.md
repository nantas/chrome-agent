# Design

## Context

本 change 是总体规划中 Phase 1 的实现。前置 `governance-and-capability-rebuild` 产出了总体规划文档和 README 重写，但将治理层的具体建设工作留给了 Phase 1。

当前 AGENTS.md 是 245 行的操作手册，需要转为纯治理文档。操作流程需要提取到 playbooks。契约元模型需要在引擎契约冻结（Phase 2）之前建立。`scrapling-first-browser-workflow` spec 的规范内容将被 `agents-governance` 吸收后标记为 superseded。

## Goals / Non-Goals

**Goals:**
1. 重写 AGENTS.md 为纯治理文档，包含 7 个强制章节
2. 将现有 AGENTS.md 中的操作流程提取到 `docs/playbooks/` 作为独立操作手册
3. 创建 `agents-governance` spec 作为仓库治理层的行为规范真源
4. 创建 `capability-contracts` spec 作为引擎契约的通用元模型
5. 标记 `scrapling-first-browser-workflow` spec 为 superseded

**Non-Goals:**
- 不修改任何引擎实现
- 不创建具体引擎的契约文件（Phase 2）
- 不涉及策略库标准化（Phase 3）
- 不涉及引擎注册机制（Phase 4）
- 不涉及输出生命周期管理（Phase 5）

## Decisions

### Decision 1: AGENTS.md 内容拆分策略

AGENTS.md 的现有操作内容（Scrapling 使用步骤、fallback 切换逻辑、证据收集流程、认证会话处理）全部提取到以下 playbook 文件：

```
docs/playbooks/
├── scrapling-fetchers.md        # get / fetch / stealthy-fetch 的使用指南
├── fallback-escalation.md       # chrome-devtools-mcp / chrome-cdp 的切换条件
├── evidence-collection.md       # 截图、DOM snapshot、网络请求等证据收集方法
├── authenticated-sessions.md    # 已登录会话的只读边界与安全规则
└── article-extraction.md        # 文章式正文提取（DOM 顺序 + 内联图片）
```

AGENTS.md 在相关治理章节中使用 `docs/playbooks/` 的相对路径引用这些文件，但不嵌入操作细节。

**Rationale**: 每个 playbook 聚焦单一操作主题，便于独立维护和扩展。AGENTS.md 保持轻量治理入口。

### Decision 2: AGENTS.md 治理章节结构

按 `agents-governance` spec 的 7 个 Requirements 组织：

1. Service Identity（服务身份 + 核心原则）
2. Capability Framework（能力全景引用）
3. Governance Rules（引擎选择 + 路由 + 报告 + 认证边界）
4. Directory Governance（顶级目录用途与约束）
5. Decision Record Governance（决策记录格式与索引）
6. Spec and Change Governance（openspec 管理规则）
7. Reference Index（仓库关键文档索引）

不使用子标题编号，直接使用 Markdown heading 层级。

### Decision 3: scrapling-first-browser-workflow spec 处理方式

在原 spec 文件顶部追加一行：

```
> **Status**: Superseded by [`agents-governance`](../agents-governance/spec.md) as of 2026-04-28.
```

文件其余内容保持不变，作为历史记录保留。`openspec/specs/scrapling-first-browser-workflow/` 目录不移动、不删除。后续 design、tasks、verification 引用治理相关的路由规则时，引用 `agents-governance` 而非 `scrapling-first-browser-workflow`。

### Decision 4: 契约元模型存放位置

`capability-contracts` spec 作为通用元模型放在 `openspec/specs/capability-contracts/spec.md`，定义 input/output/error 三维结构和命名规范。Phase 2 的具体引擎契约按 `openspec/specs/<engine-id>-contract/spec.md` 模式存放。

元模型本身不包含任何引擎特定的参数值或行为描述——那些是 Phase 2 的职责。

### Decision 5: 总体规划文档的 Phase 1 描述更新

`docs/governance-and-capability-plan.md` 中 Phase 1 的当前描述：
- 范围: "项目治理与能力契约建立"
- 交付物: "AGENTS.md 治理重写、能力契约创建与冻结"

对本 change 完成后的状态，更新为更精确的描述：
- 范围: "项目治理层与契约元模型建立"
- 交付物: "AGENTS.md 纯治理重写、agents-governance spec、capability-contracts 元模型 spec、操作流程下沉到 playbooks"

### Decision 6: README.md 的 AGENTS.md 角色描述更新

`README.md` 中当前描述 AGENTS.md 为"操作指南与工作流定义"。更新为"治理文档——服务身份、能力契约框架、治理规则"。同时更新 README 中的目录结构注释。

## Risks / Migration

- **风险 1**: 现有自动化或 skill 可能硬编码了对 AGENTS.md 中特定操作句子的引用。迁移对策：本 change 完成后检查 skill 文件（特别是 `chrome-cdp` skill）是否引用了被移走的操作内容，如有则更新引用指向对应的 playbook。
- **风险 2**: 操作流程从 AGENTS.md 移除后，直接打开 AGENTS.md 的读者可能找不到"怎么用"的信息。缓解措施：AGENTS.md 的 Reference Index 章节明确列出每个 playbook 的路径和用途；README.md 也添加 playbooks 的说明。
- **风险 3**: 契约元模型如果定义得过于宽泛可能对 Phase 2 的指导价值弱。缓解措施：本 change 的 spec 已为每个维度定义了具体的必填字段，避免抽象的"应有尽有"模板。
