# Design

## Context

Phase 5 把 `chrome-agent` CLI 固化成了唯一正式外部入口，并把历史 `skills/chrome-agent` 降级为兼容遗留物。但真实使用表明，这个模型没有消除高层包装需求，反而迫使外部 agent 自己决定 `fetch` / `explore` / `crawl`，使仓库宣称的 `workflow-driven` 原则落空。

这次 change 不回退到旧的 prompt-forwarding skill，也不推翻 repo-backed CLI。目标是把两层入口重新对齐：
- 全局 skill 负责 agent-facing 的意图路由、backend preflight 和结果包装
- 全局 CLI 负责显式命令执行、repo 解析和 JSON-first backend contract
- 仓库内 workflow 继续负责实际引擎选择、fallback 和证据规则

## Goals / Non-Goals

**Goals:**

- 恢复一个官方支持的 agent-first `chrome-agent` skill
- 明确 skill 只包装 CLI，而不是调用 `repo-agent` 或 `codex-agent`
- 将 `explore` 扩展为 Platform/Page Analysis 的 CLI backend
- 统一 skill、CLI、AGENTS、README、install guidance 的入口叙事
- 用新的 change 明确 supersede Phase 5 中“retire skill”这一失效假设

**Non-Goals:**

- 不把 skill 变成新的抓取运行时
- 不新增 `auto` 或 `run` 之类的高层 CLI 命令
- 不改写现有 Scrapling / DevTools / CDP engine 的内部行为
- 不让 CLI 复制仓库内 workflow 的站点规则或 fallback 判断
- 不恢复任何基于 prompt transport 的旧 dispatcher 依赖链

## Decisions

### Decision 1: Skill-first, CLI-backed layering

采用明确的两层入口模型：

```text
agent caller
  -> global workflow skill
       -> chrome-agent doctor
       -> intent routing
       -> chrome-agent fetch|explore|crawl
            -> repo-local workflow
                 -> engines / strategies / reports
```

skill 的价值是意图层，而不是执行层。这样可以保留 CLI 的可组合性，同时把工作流判断从上游 caller 手里收回来。

### Decision 2: No legacy dispatcher runtime

恢复 skill，但不恢复旧 global skill 的 runtime 方式。新的 skill 不能再依赖 `repo-agent` 或 `codex-agent` 去“转发一段 prompt 到仓里执行”，因为那会让结果格式和执行语义重新变得不稳定。

统一 backend 只保留 repo-backed CLI，所有 agent-facing 输出都以 CLI JSON 为真源。

### Decision 3: `explore` becomes the analysis backend

不新增 `analyze` 命令，也不把深度分析继续留在 skill 外侧。Platform/Page Analysis 统一落到扩展后的 `explore`：
- strategy gap 仍由 `explore` 覆盖
- DOM / network / screenshot / structure evidence 也由 `explore` 承接
- skill 遇到“分析、调试、证据、规则、复现”等意图时统一路由到 `explore`

这样 CLI 仍保持紧凑，不引入新的高层命令分叉。

### Decision 4: CLI remains explicit, not primary-for-agents

CLI 继续保留 `fetch` / `explore` / `crawl` / `doctor` / `clean`。

其中：
- `fetch` / `explore` / `crawl` 是低层显式 workflow backend
- `doctor` / `clean` 是运行支撑命令

帮助文本和 README 需要明确这个角色边界，避免继续把 CLI 叙述成“唯一正式入口”，但 shell/backend 使用场景仍直接面向 CLI。

### Decision 5: Result contract grows around orchestration needs

为了让 skill 能稳定包装 CLI 结果，CLI JSON contract 需要补足更高层的可消费字段，至少包括：
- `workflow`
- `engine_path`

这样 skill 不必从自由文本猜测当前走的是 Content Retrieval 还是 Platform/Page Analysis，也不用自行归纳 fallback 路径。

## Risks / Migration

### Risk 1: Skill and CLI documentation drift

如果 skill 文案、README、CLI `--help`、specs 各说各话，入口模型会再次混乱。

**Mitigation:** 以 `global-workflow-skill`、`global-capability-cli`、`agents-governance` 三份 delta specs 作为唯一契约，并在任务里要求同步更新所有入口文档。

### Risk 2: `explore` 语义扩张后仍保留旧实现

如果只改文档、不改 `explore` 输出和 artifact 语义，skill 路由到 `explore` 后仍拿不到稳定的分析后端结果。

**Mitigation:** 任务中明确要求扩展 `explore` 的结果字段、artifact disclosure 和 analysis evidence 路径。

### Risk 3: Legacy guidance remains reachable

仓内还保留着历史 skill 文件和 Phase 5 归档结论，若 README 或 install playbook 没完全更新，用户会继续看到相互矛盾的入口指引。

**Mitigation:** 将迁移工作纳入核心实现任务，而不是只在收尾文档阶段顺手调整。

### Risk 4: Skill starts re-implementing workflow logic

如果实现时把 engine 选择、strategy 判断、fallback 细节重新写进 skill，会复制仓库内执行规则。

**Mitigation:** 强制 skill 只做 doctor preflight、intent routing 和 CLI invocation；所有执行细节仍以仓库内 workflow 和 CLI 结果为准。
