# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/doctor-repo-freshness/spec.md` 中所有 requirement 的实现范围：`repo-freshness-check`、`tracked-files-change-detection`、`auto-update-global-files`、`installed-hash-file`、`doctor-result-semantics`、`skill-contract-update`
- [x] 1.2 确认 `runDoctor()` 函数当前结构：checks 数组、broken 过滤、result 计算、renderResult 输出格式

## 2. 核心实现任务

- [x] 2.1 在 `scripts/chrome-agent-cli.mjs` 顶部新增 `runGitFetchCheck(repoRoot)` 辅助函数
  - 检测 `.git` 目录是否存在 → 不存在返回 `{ ok: true, detail: "skipped: not a git repo" }`
  - 执行 `git fetch origin main`（timeout 10s）→ 失败返回 `{ ok: true, detail: "skipped: fetch failed (<reason>)" }`
  - 检查是否 detached HEAD → 是则返回 `{ ok: true, detail: "skipped: detached HEAD" }`
  - 比对 HEAD 与 origin/main → 相等返回 `{ ok: true, detail: "<hash>" }`；不等返回 `{ ok: false, detail: "behind: HEAD <hash> vs origin/main <hash>" }`
  - Spec 覆盖：`repo-freshness-check`（4 个 scenario）

- [x] 2.2 在 `runGitFetchCheck` 基础上新增 `runTrackedFilesCheck(repoRoot)` 逻辑
  - 落后时执行 `git diff --name-only HEAD origin/main`
  - 与关键文件列表取交集：`scripts/chrome-agent-runtime.mjs`、`scripts/chrome-agent-cli.mjs`、`skills/chrome-agent/SKILL.md`
  - 交集为空 → 覆写结果为 `{ ok: true, detail: "behind but no tracked files changed" }`
  - 交集非空 → 返回 `{ ok: false, detail: "tracked files changed: <file list>", changedFiles: [...] }`
  - Spec 覆盖：`tracked-files-change-detection`（2 个 scenario）

- [x] 2.3 新增 `runAutoUpdateGlobalFiles(repoRoot, changedFiles)` 辅助函数
  - 确保目标目录存在：`~/.agents/scripts/` 和 `~/.agents/skills/chrome-agent/`
  - 如果 `changedFiles` 包含 `scripts/chrome-agent-runtime.mjs` → 复制到 `~/.agents/scripts/chrome-agent.mjs`
  - 如果 `changedFiles` 包含 `skills/chrome-agent/SKILL.md` → 复制到 `~/.agents/skills/chrome-agent/SKILL.md`
  - 复制成功后写入 HEAD commit hash 到 `~/.agents/scripts/.chrome-agent-installed-hash`
  - 返回 `{ ok: true/false, detail: "..." }`
  - Spec 覆盖：`auto-update-global-files`（2 个 scenario）、`installed-hash-file`（2 个 scenario）

- [x] 2.4 修改 `runDoctor()` 函数，在现有 checks 数组末尾插入新检查逻辑
  - 调用 `runGitFetchCheck(repoRoot)` → 添加 `repo_freshness` 检查项
  - 若 `repo_freshness.ok === false` → 调用 `runTrackedFilesCheck(repoRoot)` 获取 `changedFiles`
  - 若 `changedFiles` 非空 → 调用 `runAutoUpdateGlobalFiles(repoRoot, changedFiles)` → 添加 `global_skill_updated` 检查项
  - 更新 `next_action`：当 `repo_freshness.ok === false` 且更新成功时，设为 "Global skill and runtime files have been updated. Please reload the skill (restart the session or re-read the skill file), then retry your command."
  - Spec 覆盖：`doctor-result-semantics`（1 个 scenario）

- [x] 2.5 更新 `skills/chrome-agent/SKILL.md` 的 Backend Contract 部分
  - 在 "Required result fields to preserve from doctor" 段落说明新增的 `repo_freshness` 和 `global_skill_updated` 检查项语义
  - 新增一段说明：当 doctor 返回 `partial_success` 且 next_action 包含 skill 重载提示时，应告知用户重载 skill 后重试
  - Spec 覆盖：`skill-contract-update`（1 个 scenario）

## 3. 收敛与验证准备

- [x] 3.1 在源码仓库 HEAD 落后 origin/main 的场景下运行 `chrome-agent doctor --format json`，验证 `repo_freshness` 检查项输出和自动更新行为
- [x] 3.2 在源码仓库 HEAD 等于 origin/main 的场景下运行 `chrome-agent doctor --format json`，验证 `repo_freshness` 为 ok
- [x] 3.3 在无网络环境下运行 `chrome-agent doctor --format json`，验证跳过检查不阻断
- [x] 3.4 标记需要进入 writeback 的摘要：`docs/playbooks/chrome-agent-global-install.md`、`skills/chrome-agent/SKILL.md`

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
