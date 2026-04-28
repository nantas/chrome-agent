# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `output-lifecycle-git-governance`、`output-lifecycle`、`report-emission-gating` 的 requirement 都有对应实现动作
- [x] 1.2 确认仓库现有 `.gitignore` 与治理文档存在不一致并记录修复目标

## 2. 核心实现任务

- [x] 2.1 修改 `.gitignore`：移除 `reports/` 目录级忽略，新增 `outputs/` 目录级忽略
- [x] 2.2 更新 `openspec/specs/output-lifecycle/spec.md`：新增 git ignore 对齐 requirement（`outputs/` ignored、`reports/` non-ignored by default）
- [x] 2.3 为 CLI 工作流增加报告产出门控：`explore` 默认产出，`fetch/crawl` 默认不产出，显式 report 参数可强制产出
- [x] 2.4 校验变更后 `git status` 与目录策略符合 durable/disposable 定义

## 3. 收敛与验证准备

- [x] 3.1 准备验证证据：`.gitignore` 关键行、spec 新增 requirement 与 scenario
- [x] 3.2 准备门控验证证据：`explore` 默认产出报告、`fetch` 默认不产出报告、`fetch --report` 可产出报告
- [x] 3.3 记录对既有本地 `reports/` 文件可见性的迁移影响说明

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
