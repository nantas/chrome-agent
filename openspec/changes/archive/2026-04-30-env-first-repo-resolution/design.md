# Design

## Context

`chrome-agent` 已经完成了 skill-first / CLI-backed 的入口分层，但 runtime 默认仓库解析仍是 repo-registry-first。这与高频、本机、agent-first 的实际使用方式不一致：使用者通常已经配置了 `CHROME_AGENT_REPO`，却仍然让默认热路径先经过 registry 读取。

本次 change 不改变 workflow skill 的基本定位，也不改变抓取 backend 本身；目标只是把“默认运行时仓库来源”收敛到更短、更明确的 env-first 契约。

## Goals / Non-Goals

**Goals:**

- 把默认解析顺序改成 `--repo` override → `CHROME_AGENT_REPO` → failure
- 保留显式 `--repo repo://...` 路径，避免破坏显式 repo-ref 使用场景
- 把 `doctor`、README、安装手册和相关 specs 的默认叙事统一到 env-first
- 明确 env 缺失或无效时的停止语义与 remediation

**Non-Goals:**

- 不修改 `fetch` / `explore` / `crawl` 的抓取实现
- 不删除 repo-registry 支持能力本身
- 不自动写入或覆盖用户 shell 配置
- 不引入新的高层命令或新的安装器

## Decisions

### Decision 1: Env-first applies at the runtime layer

直接修改 `scripts/chrome-agent-runtime.mjs` 的默认 `resolveRepository()` 逻辑，而不是只在 skill 层做条件分支。这样 skill 路径和直接 CLI 路径保持同一套默认契约，不会出现两种默认解析顺序。

### Decision 2: Repo-registry becomes explicit-only

repo-registry 不再参与默认热路径，但保留显式 `--repo repo://chrome-agent` 的能力。这样既能缩短高频路径，又不需要删除既有 repo-ref 生态。

### Decision 3: Missing or invalid env is a hard stop

当没有显式 `--repo` override 且 `CHROME_AGENT_REPO` 缺失或无效时，直接失败并给出 remediation。默认路径不再透明 fallback 到 registry，否则“env-first”只会退化成“env-check-first but registry-still-default-enough”。

### Decision 4: Resolution semantics must be visible

当前实现和 JSON contract 已经暴露了 `repo_ref`、`workflow`、`engine_path`，并保留 `resolution_mode`。本次 change 应同步更新这些语义，至少让默认 env 路径不再被命名为 `env_fallback`。

### Decision 5: Install contract must match runtime truth

安装/迁移文档不能继续把 repo-registry-first 写成默认前提，否则用户会在文档层看到与真实高频路径相反的建议。文档需要明确：
- `CHROME_AGENT_REPO` 是默认运行前提
- `--repo` 是显式 override
- `repo://...` 仅在显式 override 路径中出现

## Risks / Migration

### Risk 1: Existing zero-config registry users lose the old default path

如果有调用者只配了 repo-registry、没配 `CHROME_AGENT_REPO`，默认调用会从 success 变成 failure。

**Mitigation:** 明确保留 `--repo repo://chrome-agent` 路径，并在 remediation 中直接指向“设置 env 或显式传 `--repo`”。

### Risk 2: `resolution_mode` / `repo_ref` naming drifts

如果代码行为改了，但 JSON contract 继续沿用 `env_fallback` 等旧术语，上层 skill 或文档会产生误导。

**Mitigation:** 把 resolution naming 作为核心实现任务，而不是仅改解析顺序。

### Risk 3: Install docs stay split-brain

如果 README、playbook、项目页、specs 各自保留一部分 registry-first 叙事，用户会继续混淆默认路径与显式 override 路径。

**Mitigation:** 将文档收敛列为核心任务，而不是实现后的附带修补。
