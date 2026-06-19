# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖：6 个 ADDED Requirements 与 `docs/playbooks/chrome-agent-global-install.md` + `AGENTS.md` 落点一一对应（见 design.md 表格）
- [x] 1.2 确认前置条件：读取 `docs/playbooks/chrome-agent-global-install.md` 全文（确认 Case 编号体系与 Version Freshness 现状）、`AGENTS.md` §3 与 §11 现状

## 2. 核心实现任务（纯文档，不涉及代码，无需 TDD slice）

> 本 change 是文档型 change：核心实现 = 编辑项目页使其满足 spec requirement。每个任务的验证方式 = 该 requirement 对应 scenario 可在文档中核对。

- [x] 2.1 **playbook 新增 Case 6**（覆盖 `manual-sync-procedure-documented`）：在 `docs/playbooks/chrome-agent-global-install.md` 的 Case 5 之后新增「Case 6: Manually sync global copies (ahead of origin, or immediate-effect needed)」，含四步：cp runtime + chmod、cp skill、`git rev-parse HEAD > installed-hash`、`chrome-agent doctor --format json` + reload skill。
  - 验证：Case 6 存在且四步齐全；scenario `operator-syncs-ahead-of-origin` 可逐句核对。
- [x] 2.2 **playbook Version Freshness 补 ahead 行**（覆盖 `ahead-of-origin-sync-gap-documented`）：在该段 behind 两条之后补「Source repo AHEAD of `origin/main`」一条，说明 `repo_freshness` 报 `ahead` 且为 ok、不触发 auto-update、全局副本相对本地 HEAD 已过时、须手动同步（指向 Case 6）或先 `git push`。
  - 验证：ahead 行存在；scenario `ahead-of-origin-detected` 可核对。
- [x] 2.3 **playbook 规范 behind 两条措辞**（覆盖 `auto-update-behind-origin-documented`）：确认现有 behind-with-tracked / behind-without-tracked 两条措辞与 spec 一致（含「refreshes the installed-hash to the current HEAD」与「reload the skill」），缺则补齐。
  - 验证：两条 scenario `behind-origin-with-tracked-changes` / `behind-origin-without-tracked-changes` 可核对。
- [x] 2.4 **playbook 新增 Installed Hash Semantics 小节**（覆盖 `installed-hash-semantics-documented`）：在 Version Freshness 之后新增小节，说明 hash 记录的是 `git rev-parse HEAD`（非文件内容 hash）、作为 doctor 增量判断种子、手动同步后必须刷新。
  - 验证：小节存在；scenario `operator-misreads-hash-file` 可核对。
- [x] 2.5 **playbook tracked files 清单补 cli 说明**（覆盖 `tracked-files-registry-documented`）：确认现有「Tracked files for auto-update」清单为三文件，并补一句说明 `chrome-agent-cli.mjs` 是 trigger（触发重拷 runtime）而非 copy 目标。
  - 验证：清单为三文件 + cli 触发说明；scenario `operator-locates-tracked-files` 可核对。
- [x] 2.6 **AGENTS.md §0.5 新增 C10 治理条目**（覆盖 `agents-md-governance-anchor` §3 部分）：在 C4（引擎版本同步）之后新增「Skill/Runtime 全局同步」条目，措辞：修改 tracked files（`scripts/chrome-agent-runtime.mjs`、`scripts/chrome-agent-cli.mjs`、`skills/chrome-agent/SKILL.md`）后须同步到全局副本并刷新 `~/.agents/scripts/.chrome-agent-installed-hash`，附 `docs/playbooks/chrome-agent-global-install.md` 链接。
  - 验证：§3 条目存在且含三文件 + installed-hash + playbook 链接。
- [x] 2.7 **AGENTS.md §11 必读表新增一行**（覆盖 `agents-md-governance-anchor` §11 部分）：在「按任务类型必读」表新增任务类型「改 runtime/cli/SKILL.md」→ 必读 `docs/playbooks/chrome-agent-global-install.md`，关注点：tracked files、ahead / 手动同步、installed-hash 刷新。
  - 验证：§11 表新增行存在且关注点齐全。

## 3. 收敛与验证准备

- [x] 3.1 整理进入 verification 的证据：6 个 requirement 的 spec→doc 覆盖核对（grep 关键句）、`chrome-agent doctor --format json` 在 ahead 场景的 `repo_freshness` 实测输出。
- [x] 3.2 标记进入 writeback 的摘要：playbook Case 6 / ahead 行 / hash 小节、AGENTS.md §3 条目 + §11 行。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification 结论生成 `writeback.md`（目标、字段映射、前置条件；本 change 回写目标即核心实现已编辑的项目页，writeback 记录审计证据）
- [x] 4.3 执行 writeback.md 中定义的回写核对，记录可审计证据（文件路径、关键句位置、doctor 实测结果）
