# Specification Delta

## Capability 对齐（已确认）

- Capability: `doctor-repo-freshness`
- 来源: `proposal.md` / 已与用户在讨论中确认
- 变更类型: `modified`
- 用户确认摘要: 在 `runDoctor()` 中新增 `repo_freshness` 检查项，通过 `git fetch` 比对 HEAD 与 `origin/main`；仅当关键文件有变动时自动更新全局 runtime + skill；网络失败跳过不阻断；返回 `partial_success` 提示重载。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: repo-freshness-check
`chrome-agent doctor` SHALL 新增一个名为 `repo_freshness` 的检查项，通过在源码仓库目录执行 `git fetch origin main`（timeout 10 秒）来比对本地 HEAD commit 与 `origin/main` commit。

#### Scenario: source-repo-is-current
- **WHEN** `git fetch origin main` 成功，且本地 HEAD commit hash 等于 `origin/main` commit hash
- **THEN** `repo_freshness` 检查项标记为 `ok: true`，detail 显示当前 commit hash

#### Scenario: source-repo-behind-origin
- **WHEN** `git fetch origin main` 成功，且本地 HEAD commit hash 不等于 `origin/main` commit hash
- **THEN** `repo_freshness` 检查项标记为 `ok: false`，系统 SHALL 检查关键文件是否有实际变动

#### Scenario: network-fetch-failure
- **WHEN** `git fetch origin main` 因网络问题失败（timeout、DNS 错误、连接拒绝等）
- **THEN** `repo_freshness` 检查项标记为 `ok: true`，detail 显示 `skipped: fetch failed (<reason>)`，不阻断工作流

#### Scenario: source-repo-not-git-repo
- **WHEN** 源码仓库目录不是一个有效的 git 仓库（缺少 `.git` 目录）
- **THEN** `repo_freshness` 检查项标记为 `ok: true`，detail 显示 `skipped: not a git repo`

#### Scenario: detached-head-state
- **WHEN** 源码仓库处于 detached HEAD 状态
- **THEN** `repo_freshness` 检查项标记为 `ok: true`，detail 显示 `skipped: detached HEAD`

### Requirement: tracked-files-change-detection
当 `repo_freshness` 检查发现源码仓库落后于 `origin/main` 时，系统 SHALL 仅当以下关键文件在落后范围内有实际变动时，才触发自动更新：

- `scripts/chrome-agent-runtime.mjs`
- `scripts/chrome-agent-cli.mjs`
- `skills/chrome-agent/SKILL.md`

#### Scenario: tracked-files-changed
- **WHEN** 源码仓库落后 `origin/main`，且 `git diff --name-only HEAD..origin/main` 输出中包含至少一个关键文件
- **THEN** 系统 SHALL 执行自动更新全局文件流程

#### Scenario: tracked-files-unchanged
- **WHEN** 源码仓库落后 `origin/main`，但所有关键文件均无变动
- **THEN** 系统 SHALL NOT 执行自动更新，`repo_freshness` 检查项标记为 `ok: true`，detail 显示 `behind but no tracked files changed`

### Requirement: auto-update-global-files
当确认关键文件有变动时，系统 SHALL 自动将最新的 runtime 和 skill 复制到全局目录：

1. 复制 `<repo>/scripts/chrome-agent-runtime.mjs` → `~/.agents/scripts/chrome-agent.mjs`
2. 复制 `<repo>/skills/chrome-agent/SKILL.md` → `~/.agents/skills/chrome-agent/SKILL.md`
3. 写入当前 HEAD commit hash 到 `~/.agents/scripts/.chrome-agent-installed-hash`

复制前 SHALL 确保目标目录存在（自动创建）。

#### Scenario: auto-update-succeeds
- **WHEN** 关键文件有变动，且文件复制和 hash 写入均成功
- **THEN** doctor 返回 `partial_success`，next_action 提示用户重新加载 skill 后再重试，checks 中 `repo_freshness` 标记为 `ok: false`，新增 `global_skill_updated` 检查项标记为 `ok: true`

#### Scenario: auto-update-write-fails
- **WHEN** 文件复制失败（权限不足、磁盘满等）
- **THEN** doctor 返回 `partial_success`，next_action 提示手动更新失败原因和修复步骤，`global_skill_updated` 检查项标记为 `ok: false`

### Requirement: installed-hash-file
系统 SHALL 在 `~/.agents/scripts/.chrome-agent-installed-hash` 文件中记录最近一次安装或自动更新时的源码仓库 HEAD commit hash。

#### Scenario: hash-file-created-on-update
- **WHEN** 自动更新全局文件成功
- **THEN** `.chrome-agent-installed-hash` 文件内容为当前 HEAD commit hash（40 字符 hex），文件末尾有换行符

#### Scenario: hash-file-absent-on-first-run
- **WHEN** `doctor` 首次运行且 `.chrome-agent-installed-hash` 不存在
- **THEN** 系统 SHALL 视为"未记录安装版本"，不因 hash 缺失而阻断工作流；若检测到落后且有关键文件变动，正常执行自动更新并创建 hash 文件

### Requirement: doctor-result-semantics
`repo_freshness` 检查项的结果 SHALL 遵循以下语义：

- `ok: true` + detail 不含 `skipped` → 源码仓库是最新的
- `ok: true` + detail 含 `skipped` → 跳过检查（网络失败 / 非 git 仓库 / detached HEAD / 落后但无关键文件变动）
- `ok: false` → 源码仓库落后且有关键文件变动，全局文件已自动更新，需要用户重新加载 skill

#### Scenario: partial-success-with-reload-hint
- **WHEN** `repo_freshness` 为 `ok: false`（自动更新成功）
- **THEN** doctor 整体结果为 `partial_success`，`next_action` 包含明确的 skill 重载提示文本

### Requirement: skill-contract-update
`skills/chrome-agent/SKILL.md` 的 Backend Contract 部分 SHALL 更新，说明 doctor 输出中新增的 `repo_freshness` 检查项和 `skill_reload_required` 语义。

#### Scenario: skill-docs-updated
- **WHEN** 用户阅读更新后的 SKILL.md
- **THEN** 可以了解到：当 doctor 返回 `partial_success` 且 next_action 包含 skill 重载提示时，应告知用户重载 skill 后重试当前命令

### Requirement: explore-python-deps-check

`chrome-agent doctor` SHALL include an `explore_deps` check item that verifies the Python packages required by `scripts/explore/main.py` are importable.

The check SHALL execute `python3 -c "import bs4, yaml; print('ok')"` and evaluate the exit code.

#### Scenario: explore-deps-available
- **WHEN** both `bs4` and `yaml` are importable (exit code 0)
- **THEN** the `explore_deps` check item SHALL be marked `ok: true`
- **THEN** `detail` SHALL read `"bs4, yaml available"`

#### Scenario: explore-deps-missing
- **WHEN** either `bs4` or `yaml` is not importable (non-zero exit code)
- **THEN** the `explore_deps` check item SHALL be marked `ok: false`
- **THEN** `detail` SHALL read `"missing: bs4 or yaml. Install: pip3 install beautifulsoup4 pyyaml"`

#### Scenario: doctor-result-with-explore-deps-failure
- **WHEN** `explore_deps` is `ok: false` and no other checks are broken
- **THEN** doctor's overall `result` SHALL be `"partial_success"`
- **THEN** `summary` SHALL include `explore_deps` in the list of failed checks
- **THEN** `next_action` SHALL include the installation command for the missing packages

#### Scenario: python3-not-found
- **WHEN** the `python3` binary is not available or the spawn fails for any reason other than import error
- **THEN** the `explore_deps` check item SHALL be marked `ok: false`
- **THEN** `detail` SHALL include the spawn error reason