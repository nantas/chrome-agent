# Writeback

## 回写目标

### 1. `docs/playbooks/chrome-agent-global-install.md`

**字段映射：**

| 回写位置 | 内容 |
|----------|------|
| Install Workflow 之后 | 新增 "Version Freshness Check" 段落：说明 doctor 现在会自动检测源码仓库是否落后 origin/main，落后且关键文件有变动时自动更新全局 runtime 和 skill |
| Validation 段落 | 更新验证步骤：doctor 输出新增 `repo_freshness` 和可选的 `global_skill_updated` 检查项 |
| Operator Notes | 新增说明：doctor 的 git fetch timeout 为 10s；网络失败时跳过不阻断；hash 文件路径 |

### 2. `skills/chrome-agent/SKILL.md`

**字段映射：**

| 回写位置 | 内容 |
|----------|------|
| Backend Contract / Required result fields | 已在 Task 2.5 中直接更新：新增 `repo_freshness` 和 `global_skill_updated` 检查项说明 |
| Backend Contract / Doctor Freshness Checks | 已新增完整段落 |

### 3. `AGENTS.md`

**字段映射：**

| 回写位置 | 内容 |
|----------|------|
| 参考 索引表 | 无需新增条目（doctor 修改属于内部实现变更，不新增独立文档） |

## 回写状态

- [x] `skills/chrome-agent/SKILL.md` — 已在 Task 2.5 中直接修改，无需额外回写
- [x] `docs/playbooks/chrome-agent-global-install.md` — 已回写版本新鲜度检查段落

## 前置条件

- verification.md 已确认所有 spec requirement 有对应实现和证据
- 代码变更在 `scripts/chrome-agent-cli.mjs`（`runGitFetchCheck`、`runTrackedFilesCheck`、`runAutoUpdateGlobalFiles`、`runDoctor` 修改）

## Capability 增量摘要

**Modified Capability: `doctor-repo-freshness`**

- `chrome-agent doctor` 新增 `repo_freshness` 检查项，通过 `git fetch origin main` 比对 HEAD 与 `origin/main`
- 落后时仅当关键文件（runtime.mjs、cli.mjs、SKILL.md）有变动才触发自动更新全局文件
- 自动更新成功后写入 `~/.agents/scripts/.chrome-agent-installed-hash`
- 返回 `partial_success` + skill 重载提示
- 网络失败、非 git 仓库、detached HEAD 场景跳过不阻断

**Spec 文件变更：**
- `openspec/changes/doctor-repo-freshness-check/specs/doctor-repo-freshness/spec.md` — 新增，6 个 requirement、11 个 scenario

**证据入口：**
- verification.md 中 spec-to-implementation 和 task-to-evidence 完整映射
