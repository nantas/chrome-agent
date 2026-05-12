# Proposal

## 问题定义

当前 `chrome-agent doctor` 只检查 runtime/shim/repo_shape/scrapling/obscura 等组件的存在性，不检查源码仓库是否落后于 `origin/main`。用户在 `git pull` 更新源码仓库后，全局安装的 skill 和 runtime 仍然是旧版本，导致行为不一致。需要一种自动检测机制：当源码仓库落后时，自动将最新的 runtime 和 skill 同步到全局目录，并提示用户重新加载 skill。

## 范围边界

**范围内：**

- 在 `runDoctor()` 中新增 `repo_freshness` 检查项
- 通过 `git fetch origin main`（timeout 10s）比对 HEAD 与 `origin/main`
- 仅当 runtime.mjs 或 SKILL.md 相关文件在源码仓库中有实际变动时，才触发自动更新全局文件
- 自动复制 runtime + skill 到全局目录，更新安装 hash 文件
- 网络失败时跳过检查（skipped/warning），不阻断工作流
- 更新 SKILL.md 文档，说明 `repo_freshness` 和 `skill_reload_required` 字段

**范围外：**

- 不新增独立的 `update` 子命令
- 不修改 `install-chrome-agent-cli.sh` 安装器
- 不改变 doctor 的整体 result 语义（仍然基于 checks 数组计算）
- 不处理源码仓库的 `git pull`（用户自行管理）

## Capabilities

### New Capabilities

（无新增独立能力）

### Modified Capabilities

- `doctor-repo-freshness`: 在 `chrome-agent doctor` 中新增源码仓库版本新鲜度检查，包含自动更新全局 runtime 和 skill 的逻辑，以及安装 hash 文件管理

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

- **`scripts/chrome-agent-cli.mjs`** — `runDoctor()` 函数增加 repo_freshness 检查项和自动更新逻辑
- **`skills/chrome-agent/SKILL.md`** — Backend Contract 部分增加 doctor 输出字段说明
- **`docs/playbooks/chrome-agent-global-install.md`** — 更新安装手册，增加版本检查与自动更新流程说明
- **`~/.agents/scripts/.chrome-agent-installed-hash`** — 新增文件，记录安装时的 commit hash（运行时产物）
- **性能影响** — 每次 doctor 执行 `git fetch`（timeout 10s），增加 1-3s 延迟；网络失败时跳过，无额外开销

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/agents-governance/spec.md`
  - 项目页：`docs/playbooks/chrome-agent-global-install.md`
  - 回写目标：`docs/playbooks/chrome-agent-global-install.md`、`skills/chrome-agent/SKILL.md`、`AGENTS.md`
