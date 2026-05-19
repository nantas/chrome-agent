# Proposal

## 问题定义

Phase 1~3 重构（`scripts/lib/` 共享库提取、统一提取引擎、orchestrator 拆分与包重命名、Phase 文件重命名、CLI 大函数拆分）已全部完成，但以下 4 个系统性缺口仍然存在：

1. **架构文档真空**：`docs/architecture/` 目录不存在。新人理解系统的唯一入口是 10KB 的 `AGENTS.md`（其中约 60% 是架构/开发内容，非纯治理规则），缺少人类可读的真源架构文档。

2. **Spec 碎片化**：`openspec/specs/` 中存在 74 个 spec 文件，许多为单变更产生的孤立 spec（如 `tooltip-icon-link-merge` 仅 51 行），且大量引用 Phase 1~3 重构前的过期路径（`scripts/mediawiki-api-extract/`、`orchestrate.py`、`infox_renderer.py`、`phase_0/phase_a/phase_b/phase_c`）。

3. **Change spec 未冻结**：`extract-shared-lib` 和 `split-orchestrator-rename-package` 两个已完成 change 创建的 9 个 spec delta 仍在 `openspec/changes/` 中，未合并到 `openspec/specs/`。

4. **AGENTS.md 过时**：LSP 真源核查发现 6 处过时/错误申明：引擎表格缺 2 个引擎（`mediawiki-api`, `obscura-serve-pool`），`scrapling-fetch` rank 从 3→4，Python 3.9 兼容性声明已过期，测试路径指向旧模块，目录结构图缺 `scripts/lib/`，Phase 命名仍使用旧名。

## 范围边界

**范围内：**
- 创建 `docs/architecture/` 下 8 篇真源架构文档（以 LSP 验证的代码实际行为为准）
- 冻结 `extract-shared-lib` 和 `split-orchestrator-rename-package` 的 9 个 spec delta 至 `openspec/specs/`
- 将 74 个 spec 合并为 ~22 个能力域 spec，同步修复过期路径引用
- LSP 真源核查 AGENTS.md，修复 6 处过时申明
- 将 AGENTS.md 中架构/开发内容迁移至 `docs/architecture/`，瘦身为纯治理文档

**范围内但推迟到 Change 3（已有设计决定）：**
- `html_to_markdown.py` 不移动至 `lib/extraction/`（4 个 import 方保护，推迟到下次包重构）

**范围外：**
- 代码变更（本次为纯文档与 spec 变更）
- 新增引擎或修改引擎选择逻辑
- 修改策略文件内容
- `html_to_markdown.py` 文件移动

## Capabilities

### New Capabilities

- `docs-architecture`: 创建 `docs/architecture/` 下 8 篇真源架构文档（01-overview 至 08-tech-stack），以 LSP 验证的代码实际行为为唯一真源，覆盖系统全景、管线数据流、策略 Schema 权威参考、CLI 命令参考、转换器架构、引擎选择决策、Explore 工作流、技术栈与开发约定。

### Modified Capabilities

- `agents-governance`: (a) LSP 真源核查修复 6 处过时申明（引擎表格补全为 10 引擎、Python 3.9 兼容声明更新、测试路径修正、目录结构补 lib/、Phase 命名更新）；(b) 架构/开发内容迁移至 `docs/architecture/`，替换为索引链接；(c) AGENTS.md 文档瘦身 ~10KB→~3KB，保留纯治理规则。

- `spec-consolidation`: (a) 冻结 `extract-shared-lib` 和 `split-orchestrator-rename-package` 两个已完成 change 的 9 个 spec delta 至 `openspec/specs/`；(b) 将 74 个 spec 合并为 ~22 个能力域 spec；(c) 同步修复所有过期路径引用：`mediawiki-api-extract`→`pipeline`、`orchestrate.py`→`orchestrator.py`/`registry.py`、`infox_renderer.py`→`lib/extraction/infobox.py`、`phase_0`/`phase_a`/`phase_b`/`phase_c`→新命名。

## Capabilities 待确认项

- [x] 8 篇架构文档清单已与用户确认（基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change D1，扩展为含 AGENTS.md 内容注入版）
- [x] Spec 合并映射（~22 能力域）已与用户确认（基于规划文档附录 C Change D2 合并映射，调整为含新增 9 个 change spec）
- [x] AGENTS.md 瘦身方向已与用户确认（保留纯治理规则，架构内容迁移至 docs/architecture/）

## Impact

**受影响的文件 (~110+ 个)：**
- 新建：`docs/architecture/` 下 8 个文档文件
- 新建：`openspec/specs/` 下 ~22 个合并后 spec 文件
- 新建：`openspec/specs/` 下 9 个冻结 change spec 文件
- 修改：`AGENTS.md`（瘦身 + 修复）
- 修改：`docs/plans/2026-05-19-structure-refactor-and-docs.md`（标注 Phase 4 完成）
- 删除/归档：~50 个旧 spec 文件
- 归档：2 个已完成 change（`extract-shared-lib`, `split-orchestrator-rename-package`）

**风险：**
- Spec 合并可能丢失有效约束 → 逐条 grep 验证 Requirement 迁移完整性
- 过期路径引用遗漏 → LSP references + grep 双重验证
- 架构文档与代码不一致 → 每篇文档配 LSP symbols/hover 验证关键函数签名

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：`openspec/specs/agents-governance/spec.md`
- 已确认项目页：`AGENTS.md`（瘦身目标）、`docs/plans/2026-05-19-structure-refactor-and-docs.md`（状态更新）、`README.md`（补充 docs/architecture/ 引用）
- 已确认回写目标：Step 4 完成后一次性回写三个项目页面
