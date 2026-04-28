# Tasks

## 1. AGENTS.md 重写（5 个子任务）

- [x] 1.1 重写 AGENTS.md 为纯治理文档，按 `specs/agents-governance/spec.md` Requirement "AGENTS.md 结构与强制内容" 的 7 个章节排列，移除所有操作步骤
- [x] 1.2 在 AGENTS.md 中声明服务身份与核心设计原则（spec: agents-governance, Service Identity requirement）
- [x] 1.3 在 AGENTS.md 中定义工作流路由规则和引擎选择策略（spec: agents-governance, 工作流路由规则 + 引擎选择策略 requirements）
- [x] 1.4 在 AGENTS.md 中定义目录结构治理规则（spec: agents-governance, 目录结构治理 requirement）
- [x] 1.5 在 AGENTS.md 中定义决策记录治理规则（spec: agents-governance, 决策记录治理 requirement）

## 2. Playbooks 提取（5 个子任务）

- [x] 2.1 创建 `docs/playbooks/` 目录（如不存在）
- [x] 2.2 提取 Scrapling 各 fetcher 使用指南到 `docs/playbooks/scrapling-fetchers.md`（从 AGENTS.md "Scrapling-First Path" 节提取并在准确性与连贯性无损的前提下进行必要改写）
- [x] 2.3 提取 fallback 切换逻辑到 `docs/playbooks/fallback-escalation.md`（从 AGENTS.md "Fallback Boundaries" 和 "Selection Rules" 节提取）
- [x] 2.4 提取证据收集方法到 `docs/playbooks/evidence-collection.md`（从 AGENTS.md "Minimum Verification Baseline" 和 "Reporting Requirements" 节提取）
- [x] 2.5 提取认证会话规则到 `docs/playbooks/authenticated-sessions.md`（从 AGENTS.md "Authenticated Read-Only Boundary" 节提取）

## 3. Spec 迁移（2 个子任务）

- [x] 3.1 在 `openspec/specs/scrapling-first-browser-workflow/spec.md` 顶部追加 superseded 声明，指向 `agents-governance`（spec: agents-governance, Scrapling-first spec 迁移 requirement）
- [x] 3.2 在 `openspec/specs/capability-contracts/spec.md` 创建最终的规范文件（基于 delta spec 的 ADDED Requirements）

## 4. 文档更新（2 个子任务）

- [x] 4.1 更新 `docs/governance-and-capability-plan.md` 中 Phase 1 的描述，反映实际交付物（design: Decision 5）
- [x] 4.2 更新 `README.md` 中 AGENTS.md 的角色描述和目录结构注释（design: Decision 6）

## 5. 验证与回写收敛（6 个子任务）

- [x] 5.1 验证 AGENTS.md 包含全部 7 个强制章节且不含操作步骤（spec: agents-governance, AGENTS.md 结构与强制内容 requirement）
- [x] 5.2 验证所有提取的 playbook 文件存在且内容与原始 AGENTS.md 一致
- [x] 5.3 验证 scrapling-first-browser-workflow spec 已正确标记 superseded
- [x] 5.4 验证 governance-plan 和 README 的更新正确反映 Phase 1 交付状态
- [x] 5.5 生成 writeback.md（基于 verification 结论）
- [x] 5.6 执行 writeback：更新 Obsidian 项目页状态（ref: binding.md writeback_targets）
