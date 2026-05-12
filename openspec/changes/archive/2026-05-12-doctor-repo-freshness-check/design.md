# Design

## Context

`chrome-agent doctor` 当前在 `scripts/chrome-agent-cli.mjs` 的 `runDoctor()` 函数中实现，执行一系列 existence check（runtime script、user shim、env default、repo shape、scrapling preflight、obscura preflight、obscura worker）。所有检查项以 `{ name, ok, detail }` 结构存入 `checks` 数组，最终由 `broken.length` 决定 `result` 为 `success`/`partial_success`/`failure`。

全局安装的 runtime（`~/.agents/scripts/chrome-agent.mjs`）和 skill（`~/.agents/skills/chrome-agent/SKILL.md`）是源码仓库对应文件的静态副本，安装后不会自动更新。

## Goals / Non-Goals

**Goals:**

- 在 `runDoctor()` 中新增 `repo_freshness` 检查项，通过 `git fetch origin main` 比对源码仓库 HEAD 是否落后
- 仅当关键文件（runtime.mjs、cli.mjs、SKILL.md）有实际变动时自动更新全局文件
- 网络失败、非 git 仓库、detached HEAD 等异常场景跳过检查，不阻断
- 返回 `partial_success` + 明确的重载提示

**Non-Goals:**

- 不新增独立的 `update` 子命令
- 不修改 `install-chrome-agent-cli.sh`
- 不自动执行 `git pull`（用户自行管理源码仓库更新）
- 不处理 git merge conflict 或 stash 场景

## Decisions

### D1: git fetch 而非 git pull

选择 `git fetch origin main` + `git rev-parse HEAD` / `git rev-parse origin/main` 比对，而非 `git pull`。原因：fetch 不改变工作区状态，是只读操作，不会产生 merge conflict 或工作区脏状态。

### D2: git diff --name-only 检测关键文件变动

落后时不直接更新，而是先用 `git diff --name-only HEAD origin/main`（注意方向：从 HEAD 到 origin/main）获取变更文件列表，再与关键文件列表取交集。只有交集非空才触发更新。

关键文件列表（硬编码在 `runDoctor` 中）：
- `scripts/chrome-agent-runtime.mjs`
- `scripts/chrome-agent-cli.mjs`
- `skills/chrome-agent/SKILL.md`

### D3: hash 文件路径与格式

安装 hash 文件：`~/.agents/scripts/.chrome-agent-installed-hash`（与 runtime 同目录，隐藏文件）。
内容：单行 40 字符 commit hash + 换行符。
用途：记录最近一次安装/自动更新时的 HEAD hash，可供未来增量检查使用。当前版本的检查逻辑不依赖此文件（直接用 git fetch 比对），但写入此文件为后续优化留有余地。

### D4: 新增 `global_skill_updated` 检查项

当自动更新执行后，在 checks 数组中新增 `global_skill_updated` 检查项，标记更新是否成功。这与 `repo_freshness` 分离，使得 doctor 输出可以区分"检测到落后"和"更新成功/失败"。

### D5: checks 数组扩展策略

`repo_freshness` 和 `global_skill_updated` 都加入 `checks` 数组。`broken` 过滤逻辑不变（`ok === false` 的项）。
- 网络失败 → `repo_freshness.ok = true`（不增加 broken）
- 落后且关键文件变动 → `repo_freshness.ok = false`（增加 broken → partial_success）
- 自动更新成功 → `global_skill_updated.ok = true`（不增加 broken，但 `repo_freshness.ok = false` 已经使整体为 partial_success）
- 自动更新失败 → `global_skill_updated.ok = false`（增加 broken）

### D6: spawnSync timeout 实现

使用 `spawnSync` 的 `timeout` 选项（10 秒）和 `killSignal: "SIGTERM"` 来限制 `git fetch` 的执行时间。

### D7: doctor 输出扩展字段

在 doctor 返回的 `extra` 对象中增加：
- `checks` 数组已包含所有检查项（现有行为不变）
- `next_action` 在需要重载时包含明确的提示文本

## Risks / Migration

### 网络延迟风险
每次 `doctor` 调用增加一次 `git fetch`（最多 10s timeout）。在 skill preflight 路径中，每次 `fetch`/`explore`/`crawl` 命令都会先调 doctor。缓解：网络失败时跳过，不阻断。

### 自动写入全局文件的风险
自动更新会覆盖 `~/.agents/scripts/chrome-agent.mjs` 和 `~/.agents/skills/chrome-agent/SKILL.md`。如果用户手动修改过这些文件，更新会丢失。缓解：这些文件本就是源码仓库的副本，手动修改不属于支持的用法。

### 向后兼容
`checks` 数组新增 `repo_freshness` 和 `global_skill_updated` 检查项，现有读取 doctor 输出的代码如果只检查特定 `name` 的项则不受影响；如果遍历所有项计算 `broken`，需注意新检查项的语义。
