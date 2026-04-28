# Design

## Context

Phase 1-4 已经把仓库内部的治理骨架搭起来了：

- `agents-governance` 定义了仓库身份、工作流路由和治理边界
- `engine-contracts` / `engine-registry` 定义了引擎与 fallback 基础
- `site-strategy-schema` / `anti-crawl-schema` 定义了策略层
- `scrapling-cli-environment` 定义了 Scrapling preflight 与安装保障

但 Phase 5 之前，仓库对外仍然缺少一个正式的、全局可调用、又不篡改仓库内执行权威的入口。历史上的 `skills/chrome-agent` 只是 thin dispatcher skill，适合作为过渡方案，不适合作为长期 capability contract。与此同时，`crawl` 在能力图里仍是 future-facing，虽然其底层要素已经散落在 site-strategy 和现有引擎能力中。

本 change 的目标是把这些已有内核拼装成一个正式的 repo-backed global CLI，而不是再造一层新的抓取运行时。

## Goals / Non-Goals

**Goals:**

- 定义 `chrome-agent` 作为唯一正式全局入口
- 使用 `repo-registry` 作为 `repo://chrome-agent` 的主解析机制，保留 `CHROME_AGENT_REPO` fallback
- 将 `explore`、`fetch`、`crawl`、`doctor`、`clean` 固化为一级命令
- 保证 `explore` / `fetch` / `crawl` 的真实执行仍在仓库内部完成，并遵循仓库 `AGENTS.md`
- 将 `crawl` 正式化为 strategy-guided traversal
- 将 `install-chain` 与 `output-lifecycle` 纳入 CLI 支撑面
- 移除旧 `skills/chrome-agent` 的正式入口地位

**Non-Goals:**

- 不把仓库工作流重写成一个大型 deterministic runtime
- 不实现开放式 spider / recursive crawl
- 不修改现有引擎实现
- 不在本 change 中实现远程调度、监控或多节点执行
- 不把 AGENTS.md 变成 launcher 安装手册

## Decisions

### Decision 1: CLI is the external contract, repository remains the execution authority

采用双层模型：

```text
global callers
  -> chrome-agent CLI
       -> repo resolution
       -> result normalization
       -> dispatch into repo-local workflow
            -> AGENTS.md / specs / strategies / engines
```

这样做的核心原因是：当前仓库已经有成熟的治理与选择规则，但还没有足够厚的 deterministic runtime 去覆盖复杂异常、登录态、挑战页和策略演化。把 CLI 定位为稳定外壳，而不是完整执行内核，可以避免把 agent judgement 硬编码进脚本。

### Decision 2: repo-registry first, environment second

仓库定位采用以下优先级：

1. explicit override
2. `repo://chrome-agent` via global repo-registry
3. `CHROME_AGENT_REPO`
4. fail with remediation

这与 OrbitOS 已有的 `repo://` 语义保持一致，也避免继续把历史环境变量作为唯一定位真源。`CHROME_AGENT_REPO` 保留只是为了兼容历史入口和局部环境，而不是继续作为长期主协议。

### Decision 3: strategy-guided crawl instead of open spider

`crawl` 在 Phase 5 正式化，但其范围明确收窄为 strategy-guided traversal：

- 必须匹配已有 `site-strategy`
- 入口来自 `entry_points`
- 扩展边来自 `links_to`
- 列表推进来自 `pagination`
- 不做开放式递归发现

这让 `crawl` 成为“正式能力”而不是“无限能力”。如果缺少 strategy，就强制走 `explore`。这也把 `explore -> strategy -> crawl` 变成仓库内部一致的能力链。

### Decision 4: doctor and clean are first-class commands

原规划中的 install-chain 与清理闭环不再是 Phase 5 的主轴，但保留为 CLI 支撑面：

- `doctor` 负责 launcher / repo resolution / runtime prerequisites
- `clean` 负责 lifecycle-aware artifact cleanup

这样 Phase 5 仍然兑现了原规划里的“安装链”和“清理闭环”，但它们围绕全局入口服务，而不是孤立存在。

### Decision 5: JSON-first result contract

CLI 默认要有稳定的结构化返回，因为它既面向人，也面向其他 agent / automation。文本输出只是这个结构化结果的渲染层。

这比沿用旧 global skill 的 `result/summary/artifacts/next_action` 纯文本约定更稳，也更容易做后续自动化集成和验证。

### Decision 6: thin launcher distribution

分发形态选择全局薄启动器，而不是完整打包一个独立运行时。实现上沿用现有 OrbitOS 风格：

- runtime script under `~/.agents/scripts/`
- user-facing shim under a PATH-visible user bin directory

这样可以复用现有全局脚本分发方式，也能把真实逻辑持续留在仓库内部，不制造第二份漂移中的实现副本。

## Risks / Migration

### Risk 1: CLI and repository rules drift

如果 CLI 自己复制一份路由或引擎决策规则，就会与仓库 AGENTS/specs 漂移。

**Mitigation:** CLI 只做 repo resolution、doctor、clean、result normalization；真实工作流交回仓库内部。

### Risk 2: repo-registry and env fallback ambiguity

同时保留 repo-registry 与 `CHROME_AGENT_REPO` 可能让调用者误解哪个才是主协议。

**Mitigation:** 在 spec、doctor 和 install guidance 中明确 registry-first；env 只在 registry 缺失时启用，并在结果中暴露 fallback usage。

### Risk 3: crawl scope expands accidentally

一旦实现者把 crawl 理解成通用 spider，复杂度会失控。

**Mitigation:** 在 `strategy-guided-crawl` spec 中把边界写死为 strategy-gated、entry-point-based、pagination-aware traversal。

### Risk 4: artifact cleanup deletes useful reports

如果 `clean` 默认清掉 `reports/`，会直接破坏仓库的证据积累。

**Mitigation:** lifecycle spec 强制 durable/disposable 区分，默认只清 `outputs/`，删除 `reports/` 必须显式升级 scope。

### Risk 5: global skill removal leaves undocumented migration gap

历史 `skills/chrome-agent` 已存在，如果直接移除而没有迁移说明，调用方会断裂。

**Mitigation:** 本 change 只定义新入口与旧入口退场规则；实现阶段需要在任务中补 install/migration guidance，并由 `doctor` 产出明确 remediation。
