# Tasks

> 规范真源：`specs/fetch/spec.md` · MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`（保留 C4 调用纪律 + 新增 seam surface 形状契约 + 新 scenario `seam-surface-uses-named-concern-groups`）。
> 纯机械重构（flat→grouped），crawl 产出字节不变。C10 触发（`chrome-agent-cli.mjs` tracked file 被改）。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖范围：`crawl-scrapling-orchestrator-is-a-seam-module` requirement 已写完 MODIFIED block（含 6 scenario：原 5 + 新 `seam-surface-uses-named-concern-groups`）
- [x] 1.2 确认依赖前置：`crawlApi` bundle 26 命名函数 + fs + log 已盘点并按 9 组分类（design D1 表）；shared helper 不可移动清单已确认（pagePatternMatches/selectFetcher/buildScraplingExtractionArgs/convertTraversalToMarkdown/collectMarkdownArtifacts/collectLinksFromHtml/urlToStructuredPath/scraplingSlugFromUrl）
- [x] 1.3 影响面盘点：`crawl_scrapling.mjs` ~40 调用点；`cli.mjs:2129-2141` bundle 构造；`tests/crawl_scrapling.test.mjs` stubApi + 静态纪律测试；C10 触发（cli.mjs tracked）

## 2. 核心实现任务

### Slice A — 升级静态纪律测试：声明 grouped 契约（RED → GREEN）

覆盖 scenario `seam-surface-uses-named-concern-groups`。

- [x] 2.1.A RED：升级 `tests/crawl_scrapling.test.mjs` 的静态纪律测试——`readCrawlApiKeys` 改为解析 grouped bundle（返回 `{group: [keys]}`）；新增断言：对每个声明组的 key，`crawl_scrapling.mjs` 内**不得**出现 flat `api.<key>` 调用（必须 `api.<group>.<key>`）。当前运行：**失败**——bundle 仍 flat，要么解析不到组、要么 crawl_scrapling.mjs 全是 flat `api.<key>`。
  - 完成标准：测试就绪，因 flat 结构/flat 调用而失败，信息指向需 grouped 化。
- [x] 2.2.A GREEN（本 slice 仅改测试逻辑使其能解析当前 flat 结构 = 暂时跳过 grouped 断言，**或** 标记为 expected-failure 直到 Slice B/C 完成）。**选 B**：测试就绪但 `todo/skip` 直到 Slice C 完成。本 slice 产出 = 测试代码就位。实际 GREEN 在 Slice C。
  - 完成标准：纪律测试的 grouped 断言代码就位（skip 状态），bare-call 断言（C4 保留）仍跑仍绿。

### Slice B — bundle 构造 grouped 化 + stub api 适配（行为测试保持绿）

- [x] 2.3.B `scripts/chrome-agent-cli.mjs:2129-2141`：`crawlApi` 从 flat 改 grouped（按 design D1 表：`{ fs, log, report:{...}, handoff:{...}, engine:{...}, cache:{...}, pool:{...}, traversal:{...}, convert:{...} }`）。
- [x] 2.4.B `tests/crawl_scrapling.test.mjs`：`stubApi` 从 flat 改 grouped（同 D1 结构）。跑 5 个行为测试——**预期 RED**（crawl_scrapling.mjs 还在 flat `api.<helper>` 调用，但 stub 现在 grouped，故 `api.collectMarkdownArtifacts is not a function`）。
  - 完成标准：bundle + stub 都是 grouped；行为测试因 crawl_scrapling.mjs 调用点未改而失败（过渡态）。

### Slice C — crawl_scrapling.mjs 调用点 grouped 化（RED → GREEN）

覆盖 scenario `seam-surface-uses-named-concern-groups` + 保留 C4 各 scenario。

- [x] 2.1.C GREEN：`scripts/lib/crawl_scrapling.mjs` 全部 ~40 处 `api.<helper>` → `api.<group>.<helper>`（按 D1 分组表映射）。逐组改、每组改完跑行为测试。重跑 2.4.B 的 5 个行为测试：**全绿**。
  - 完成标准：5 个行为测试绿；crawl_scrapling.mjs 无 flat `api.<helper>`（groupable 的）。
- [x] 2.2.C 取消 Slice A 的 skip：静态纪律测试 grouped 断言激活。跑全套：bare-call 断言（C4）绿 + flat-call 断言（D4）绿。
  - 完成标准：静态纪律测试双检全绿。

### Slice D — registry/无（本 change 无配置改动）；收尾核验

- [x] 2.3.D 全量 crawl suite：`node --test tests/crawl_scrapling.test.mjs tests/crawl-scrapling-pages-scope.test.mjs tests/fetch-strategy-selector.test.mjs`（19 测试全绿）
- [x] 2.4.D 确认 crawl 产出逻辑零改动：`git diff scripts/lib/crawl_scrapling.mjs` 仅 `api.X` → `api.group.X`（无控制流/产出变更）；`git diff scripts/chrome-agent-cli.mjs` 仅 bundle 构造形状（3 dispatch 点不变）

## 3. 收敛与验证准备

- [x] 3.1 全量 crawl + seam 测试绿（Slice D 已含；此为最终确认）
- [x] 3.2 确认 crawl 产出字节不变：对比改前改后一组 crawl 的 manifest/report（若难端到端跑，以「调用点仅前缀变化、无逻辑改动」+ 行为测试绿为证据）
- [x] 3.3 确认 C10 触发条件成立：`git diff --name-only` 含 `chrome-agent-cli.mjs`（tracked file）
- [x] 3.4 准备 C10 同步证据：记录 `chrome-agent-runtime.mjs` 与 `~/.agents/scripts/chrome-agent.mjs` 的 diff（应为空——runtime 未改，只 cp）+ installed-hash 刷新前后值

## 4. 验证与回写收敛

- [x] 4.1 生成 `verification.md`：spec-to-implementation（6 scenario 各证据）+ task-to-evidence（Slice A-D 测试输出）+ C10 同步证据 + 行为不变证据
- [x] 4.2 生成 `writeback.md`：回写目标 = fetch spec delta（归档提升）+ C10 全局同步（runtime cp + installed-hash 刷新，记录执行证据）
- [x] 4.3 归档前执行 C10 同步：`cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至 `git rev-parse HEAD`；`openspec status` apply-ready；归档提交提升 spec delta + C10 同步在同 commit
