# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `global-capability-cli` spec 覆盖 CLI 一级命令面、repo-backed dispatch、repo 解析优先级、JSON-first 返回契约和旧 global skill 退场规则
- [x] 1.2 确认 `install-chain` spec 覆盖薄启动器安装模型、全局脚本位置、repo-registry 主解析、`CHROME_AGENT_REPO` fallback 和 `doctor` 检查面
- [x] 1.3 确认 `output-lifecycle` spec 覆盖 durable/disposable artifact 分类、默认落盘位置、clean 默认安全语义和 artifact disclosure
- [x] 1.4 确认 `strategy-guided-crawl` spec 覆盖 strategy-gated crawl、entry_points / links_to / pagination 边界、partial_success 语义和 explore-first remediation
- [x] 1.5 确认 `agents-governance` MODIFIED spec 覆盖“全局 CLI 为入口、仓库内治理为执行权威”的关系
- [x] 1.6 确认 `master-plan` MODIFIED spec 覆盖 Phase 5 重定义、交付物与排他边界改写

## 2. 全局入口与安装链实现

- [x] 2.1 设计并实现全局 `chrome-agent` 薄启动器：明确 runtime script 位于 `~/.agents/scripts/`，并提供 PATH 可调用的 user-facing shim
- [x] 2.2 实现 repo 解析优先级：explicit override → `repo://chrome-agent` via repo-registry → `CHROME_AGENT_REPO` fallback → fail with remediation
- [x] 2.3 实现统一 dispatch 入口：`explore`、`fetch`、`crawl` 都进入目标仓库内部执行，并显式要求读取仓库 `AGENTS.md`
- [x] 2.4 移除或退役 `skills/chrome-agent` 作为正式入口的安装/文档路径，完成标准是主文档只保留 CLI 路径
- [x] 2.5 实现 `doctor` 命令，至少覆盖 launcher availability、repo resolution、仓库形态校验和运行前依赖检查

## 3. Crawl 与产物生命周期实现

- [x] 3.1 实现 `crawl` 的 strategy gate：只有存在匹配 `site-strategy` 时才允许执行
- [x] 3.2 实现 `crawl` 的 explore-first failure path：缺少 strategy 时返回明确失败并引导先执行 `explore`
- [x] 3.3 将 crawl 遍历边界约束到 `entry_points`、`links_to`、`pagination`，完成标准是不出现开放式递归 spider 默认行为
- [x] 3.4 建立 `outputs/` 与 `reports/` 的 lifecycle 区分和 artifact metadata 输出，完成标准是 CLI 结果能区分 durable/disposable artifacts
- [x] 3.5 实现 `clean` 默认只清 disposable outputs，完成标准是不带提升 scope 时不会删除 `reports/`

## 4. 治理与文档收敛

- [x] 4.1 更新 `openspec/specs/agents-governance/spec.md` 和对应治理文档，使其声明 global CLI 的角色边界而不把 AGENTS.md 变成安装手册
- [x] 4.2 更新 `openspec/specs/master-plan/spec.md` 与 `docs/governance-and-capability-plan.md`，将 Phase 5 明确改写为 “Global Capability CLI”
- [x] 4.3 补充安装与迁移说明，覆盖 repo-registry 主路径、env fallback、旧 skill 移除和 `doctor` 的常见 remediation

## 5. 收敛与验证准备

- [x] 5.1 验证 fresh install 场景：repo-registry 已注册时，全局 CLI 可以完成 repo 解析与命令分发
- [x] 5.2 验证 fallback 场景：repo-registry 缺失时，`CHROME_AGENT_REPO` 能作为兼容 fallback 生效，并在结果中明确标记
- [x] 5.3 验证 fetch / explore 场景：CLI 返回 JSON-first 结果且 artifact paths 正确
- [x] 5.4 验证 crawl 场景：有 strategy 时可执行，无 strategy 时会拒绝并提示 explore-first
- [x] 5.5 验证 clean 场景：默认只删除 disposable outputs，并保留 durable reports

## 6. 验证与回写收敛

- [x] 6.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 6.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 6.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
