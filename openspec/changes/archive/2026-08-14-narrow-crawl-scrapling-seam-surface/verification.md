# Verification

## 验证结论

**PASS** — 6 个 spec scenario 全有可执行证据；seam surface 从 flat 29-key 重塑为 9 个 named concern objects；crawl 产出字节不变（diff 纯 `api.X` → `api.<group>.X` 前缀）；静态纪律测试升级为双检（C4 bare-call 保留 + 新 flat-call 检测），且经 mutation 证明非恒真；20/20 crawl suite + 84/84 全量 node 测试绿。C10 触发（`chrome-agent-cli.mjs` tracked file 被改），归档时执行同步。

## Spec-to-Implementation Coverage

规范真源：`specs/fetch/spec.md` → MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`（6 scenario）。

| Scenario | 实现位置 | 证据 |
| --- | --- | --- |
| `orchestrator-extractable-and-importable`（保留） | `crawl_scrapling.mjs:15` | 5 个行为测试（stub api grouped）全绿 |
| `crawl-output-byte-identical`（保留） | 纯前缀重构 | `git diff crawl_scrapling.mjs` 仅 `api.X`→`api.<group>.X`，无控制流/产出改动（见 task 3.2 证据） |
| `api-bundle-built-once-in-cli`（保留+强化） | `cli.mjs:2129-2148` grouped bundle | `readCrawlApiGroups()` 测试解析出 7 组（report/handoff/engine/cache/pool/traversal/convert）+ fs/log 顶层 |
| `all-bundled-helpers-called-via-api-prefix`（C4 保留） | 全调用点 `api.<group>.<helper>` | 纪律测试 `all bundled helpers...no bare-identifier calls` 绿；mutation 验证：改一个为 bare → 失败 |
| `markdown-true-branch-produces-artifacts-not-reference-error`（C4 保留） | `crawl_scrapling.mjs` convert 组 | `markdown:true` 行为测试绿（stub `convert.collectMarkdownArtifacts` 返回 sentinel） |
| `seam-surface-uses-named-concern-groups`（新增） | bundle grouped + 调用点 grouped | 纪律测试 `seam surface uses named concern groups` 绿；**mutation 验证**：把 `api.report.writeTextFile` 改回 `api.writeTextFile` → 该测试 + 3 个行为测试都失败（flat 调用 + stub 不匹配） |

## Task-to-Evidence Coverage

| Task | 证据 |
| --- | --- |
| Slice A（纪律测试升级） | `readCrawlApiGroups`/`readCrawlApiHelperToGroup` 解析 grouped bundle；2 个纪律测试（bare-call + flat-call） |
| Slice B（bundle + stub grouped） | `cli.mjs:2129` crawlApi 重塑为 7 组 + fs/log；`stubApi` 重塑为同构 + `groupOverrides` 参数 |
| Slice C（调用点 grouped） | `crawl_scrapling.mjs` ~52 处 `api.<helper>` → `api.<group>.<helper>`（Python word-boundary 替换，验证 0 flat 残留） |
| Slice D（收尾） | 20/20 crawl suite + 84/84 全量 node 测试；`fetch-strategy-selector.test.mjs:160` 同步订正（flat 断言 → grouped） |
| 3.1 全量测试 | `node --test tests/*.test.mjs` → 84/84 pass |
| 3.2 产出不变 | `git diff crawl_scrapling.mjs` 的 +/- 行全为 `api.X`↔`api.group.X`（grep 非 api 改动 = 0） |
| 3.3 C10 触发 | `git diff --name-only` 含 `chrome-agent-cli.mjs`（tracked file） |
| 3.4 C10 证据 | `chrome-agent-runtime.mjs` 不在 diff（未改，只 cp 目标）；当前 global hash `9cd9a3a`（归档时刷新至 HEAD） |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| grouped bundle 构造 | `scripts/chrome-agent-cli.mjs:2129-2148` | scenario `api-bundle-built-once-in-cli` / `seam-surface-uses-named-concern-groups` |
| 调用点 grouped 化 | `scripts/lib/crawl_scrapling.mjs`（全 `api.<group>.<helper>`） | scenario `seam-surface-uses-named-concern-groups` |
| 双检纪律测试 | `tests/crawl_scrapling.test.mjs`（bare-call + flat-call） | C4 保留 + 新 scenario |
| stub api grouped | `tests/crawl_scrapling.test.mjs::stubApi` + `groupOverrides` | 行为测试 5 个 |
| 产线测试订正 | `tests/fetch-strategy-selector.test.mjs:160`（flat→grouped 断言） | task 2.4.D |
| 产出不变证据 | `git diff scripts/lib/crawl_scrapling.mjs`（纯前缀） | task 3.2 |
| C10 触发证据 | `git diff --name-only`（含 cli.mjs） | task 3.3 |

## 缺口与阻塞项

**无缺口，无阻塞。**

- 6 个 spec scenario 全有可执行证据，2 个纪律测试经 mutation 证明非恒真。
- J3 测试完备：改动的 `crawl_scrapling.mjs` + `cli.mjs`（bundle 构造）均有对应测试（`crawl_scrapling.test.mjs` + `fetch-strategy-selector.test.mjs`）。
- **C10 同步是归档前置**（task 4.3）：`chrome-agent-cli.mjs` 是 tracked file 且被改 → 归档前 SHALL `cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至 HEAD。runtime.mjs 本身未改（只 cp）。
- **诚实披露（D2 决策）**：`nextPaginationUrl` 未移入 seam 模块（虽 cli 零调用者）——保持 `api.traversal` 组内一致性，收益（少 1 bundle entry）< 成本（组内分裂 + 移动逻辑的回归面）。design.md D2 记录。
- **再审查报告「缩到 ~4」的修正**：proposal/design 已诚实记录该目标天真（shared helper 跨 cli 共享不可移动）；本 change 真实成果 = 重塑 bundle 形状为 named concern objects，不是物理移动 helper。
