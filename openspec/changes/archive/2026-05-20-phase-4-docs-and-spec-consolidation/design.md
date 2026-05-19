# Design

## Context

Phase 1~3 重构（`scripts/lib/` 共享库、统一提取引擎、orchestrator 拆分与包重命名、Phase 文件重命名、CLI 大函数拆分）已全部完成。当前仓库处于"代码已重构，文档未跟进"的状态：

- 无 `docs/architecture/` 目录
- 74 个 spec 文件散落，含大量过期路径引用
- AGENTS.md 同时承载治理规则和架构设计（~10KB），且有 6 处过时代码路径申明

本次 change 为纯文档与 spec 变更，零代码修改。

## Goals / Non-Goals

**Goals:**

1. 创建 `docs/architecture/` 下 8 篇架构文档，以 LSP 验证的代码实际行为为唯一真源
2. 冻结 2 个已完成 change 的 9 个 spec delta 至 `openspec/specs/`
3. 将 74 个 spec 合并为 ~22 个能力域 spec，同步修复过期路径引用
4. LSP 核查 AGENTS.md 并修复 6 处过时申明
5. AGENTS.md 瘦身为纯治理文档（~10KB→~3KB），架构内容迁移至 `docs/architecture/`

**Non-Goals:**

- 代码变更
- 新增引擎或修改引擎选择逻辑
- 修改 `html_to_markdown.py` 文件位置（推迟到下次包重构）
- 修改策略文件内容
- 创建新的 playbook 或操作手册

## Decisions

### D1: 架构文档以 LSP 验证为准，不以 Spec 为准

**决策**：每篇架构文档的关键函数签名、模块路径、import 关系、调用链均通过 `lsp symbols` / `lsp definition` / `lsp references` 验证后写入。不依赖 spec 中的过期路径引用或提案阶段的假设。

**理由**：spec 中存在大量过期引用（如 `mediawiki-api-extract`），以代码实际行为为真源可确保文档长期准确性。

### D2: 执行顺序 — Step 0(修复) → Step 1(冻结) → Step 2(合并) → Step 3(文档) → Step 4(瘦身)

**决策**：先修复 AGENTS.md 中的过时内容（Step 0），再冻结 change spec（Step 1），再合并 spec（Step 2），然后以此为真源写架构文档（Step 3），最后瘦身 AGENTS.md（Step 4）。

**理由**：
- Step 0 先行可避免瘦身时产生过时内容冲突
- Step 1→Step 2 依赖链：需先冻结新 spec 再合并（新 spec 也是合并源）
- Step 3 依赖 Step 2：架构文档需引用合并后的 spec 路径
- Step 4 依赖 Step 3：瘦身需要 `docs/architecture/` 文档已就位

### D3: Spec 合并策略 — 逐 Requirement 迁移，双重 grep 验证

**决策**：每个目标 spec 的合并过程分三步：
1. 创建目标 spec 文件，逐个 Requirement 从源 spec 迁移
2. `grep -r "specs/<old-name>" openspec/` 确认无活跃引用
3. 删除源 spec 目录

**理由**：74→22 的合并规模下，自动化脚本风险高（语义丢失）。逐 Requirement 人工迁移 + 双重 grep 验证可确保不丢失有效约束。

### D4: 过期路径批量替换

**决策**：Spec 合并时集中执行路径替换（`mediawiki-api-extract`→`pipeline` 等），使用 `grep` 验证零残留引用。

**理由**：集中替换比分散修复更可控，且 `grep` 零匹配标准是可自动化验证的硬性约束。

### D5: AGENTS.md 瘦身 — 每段替换为显式链接

**决策**：AGENTS.md 中每个被迁移的段落在原位置保留一句上下文摘要 + `→ <摘要> 详见 docs/architecture/<file>.md` 链接（如 `→ 引擎选择 & fallback 详见 docs/architecture/06-engine-selection.md`）。不静默删除。

**理由**：确保瘦身后的 AGENTS.md 仍然是可导航的入口文档，读者能从治理规则快速跳转到对应的架构文档。

### D6: 引擎表格真源 — `engine-registry.json` 为唯一来源

**决策**：`06-engine-selection.md` 和修复后的 AGENTS.md 中的引擎清单均以 `configs/engine-registry.json` 为唯一权威来源。不手动维护引擎表格。

**理由**：AGENTS.md 当前引擎表格缺 2 个引擎且有 rank 偏差，根本原因是没有单一真源。文档应引用 registry JSON 而非手动维护副本。

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| Spec 合并时 Requirement 遗漏 | 逐条 grep 源 spec 确认所有 `### Requirement:` 已出现在目标 spec |
| 过期路径引用残留 | 合并完成后 `grep -r "mediawiki-api-extract" openspec/specs/` 必须返回 0 |
| 架构文档与代码不一致 | 每篇文档配 LSP hover 验证关键函数签名和调用链 |
| AGENTS.md 瘦身后 agent 找不到信息 | 每个删除段保留链接；Reference Index 增加 `docs/architecture/` 条目 |
| 合并后 spec 文件名变化导致 change 引用断裂 | 更新 `openspec/changes/` 中所有活跃 change 的 spec 引用路径 |
| `agents-governance` spec 自身在合并目标中 | `governance/governance.md` 合并 `agents-governance` + `master-plan` + `capability-contracts` 时，保留 `agents-governance` 的所有 Requirement 作为 MODIFIED delta 的基础 |
