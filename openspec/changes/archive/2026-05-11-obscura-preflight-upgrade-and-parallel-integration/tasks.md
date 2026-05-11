# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `obscura-preflight-v012`: preflight 脚本升级 (spec: obscura-preflight-v012/spec.md)
  - `obscura-serve-pool`: 新增引擎 serve pool 生命周期 + 并发 fetch (spec: obscura-serve-pool/spec.md)
  - `batch-command`: 新增 batch 子命令 (spec: batch-command/spec.md)
  - `crawl-strategy-router`: crawl 管线路由修改 (spec: crawl-strategy-router/spec.md)
  - `scrape-parallel-mode`: scrape --parallel 支持 (spec: scrape-parallel-mode/spec.md)
  - `engine-registry`: 引擎注册表新增 + obscura-fetch 备注更新 (spec: engine-registry/spec.md)
- [x] 1.2 确认依赖前置条件：Obscura v0.1.2 release tarball 必须包含 `obscura-worker`（已验证包含）

## 2. 核心实现任务

### Phase 1: Preflight 升级

- [x] 2.1 **更新 Obscura preflight 文档** — `docs/playbooks/obscura-cli-preflight.md`
  - 版本号: `0.1.0` → `0.1.2`
  - 下载 URL 模板不变，版本变量更新
  - 安装后验证步骤增加 `obscura-worker --help`（或执行测试）
  - 验证方式：手动执行安装脚本验证新版 CLI 输出
- [x] 2.2 **新增 worker binary 安装验证** — 同上文件
  - 在安装逻辑中确保 tarball 中的 `obscura-worker` 被解压到 `$INSTALL_DIR`
  - preflight 验证步骤增加 `obscura-worker` 可执行性检查
  - 覆盖 spec `obscura-preflight-v012` Requirement `obcura-version-update` Scenario `preflight-verify-worker`

### Phase 2: 引擎注册

- [x] 2.3 **新增 `obscura-serve-pool` 引擎注册** — `configs/engine-registry.json`
  - 新增条目：type=`cdp_lightweight_pool`, rank=3, score=68, status=`draft`
  - 字段值见 spec `engine-registry/spec.md` ADDED Requirements
  - 覆盖 spec `engine-registry` Requirement `engine-registry-new-entry`
- [x] 2.4 **更新 `obscura-fetch` 稳定性备注** — 同上文件
  - `stability.note` 中 `v0.1.0` → `v0.1.2`
  - 覆盖 spec `engine-registry` MODIFIED Requirements

### Phase 3: CLI 集成 — serve 生命周期管理

- [x] 2.5 **实现端口扫描逻辑** — `scripts/chrome-agent-cli.mjs`
  - 函数: `findAvailablePort(startPort=9200, maxAttempts=100)`
  - 轮询端口可用性，返回第一个可用端口
  - 覆盖 spec `obscura-serve-pool` Requirement `serve-pool-lifecycle` Scenario `serve-pool-port-availability`
- [x] 2.6 **实现 serve 进程启动** — 同上文件
  - 函数: `startObscuraServe(workers, port)` → `{process, port}`
  - 使用 `child_process.spawn` 以 `detached: true` 启动
  - 等待就绪：循环检查 `http://127.0.0.1:{port}/json/version`，超时 5s
  - 覆盖 spec `obscura-serve-pool` Requirement `serve-pool-lifecycle` Scenario `serve-pool-start`
- [x] 2.7 **实现 serve 进程停止** — 同上文件
  - 函数: `stopObscuraServe(handle)`
  - 使用 `process.kill(-handle.process.pid)` 终止进程组
  - 验证进程已终止，超时 5s 后强制 SIGKILL
  - 覆盖 spec `obscura-serve-pool` Requirement `serve-pool-lifecycle` Scenario `serve-pool-stop`
- [x] 2.8 **实现并发 fetch + Markdown 后处理** — 同上文件
  - 函数: `concurrentFetch(serveHandle, urls, timeout=15)` → `[{url, html, elapsed_ms, error?}]`
  - 使用 `ThreadPoolExecutor(max_workers=serveHandle.workers)`
  - 每线程执行: `spawnSync(obscuraPath, ["fetch", url, "--dump", "html", "--quiet", "--timeout", String(timeout)])`
  - 写入 HTML 文件: `{runDir}/{pageNum}.html`
  - per-URL 超时不影响其他 URL 处理
  - 覆盖 spec `obscura-serve-pool` Requirements `serve-pool-concurrent-fetch`
- [x] 2.8b **实现 Scrapling file:// Markdown 转换** — 同上文件
  - 修改 `convertTraversalToMarkdown` 的 `prefetchedHtml` 路径：
    a. 将 Obscura 获取的 HTML 写入临时文件（如 `_tmp_{i}.html`）
    b. 调用 `scrapling extract get file://<TEMP>.html <OUTPUT>.md --ai-targeted`
    c. 转换完成后清理临时文件
  - 保留 `htmlToMarkdown()` 作为 Scrapling CLI 不可用时的降级路径
  - Scrapling `file://` 经验证可直接工作（接受 file:// 作为 URL 参数）
  - 覆盖 spec `obscura-serve-pool` Requirements `serve-pool-content-compatibility`
    - Scenario `markdown-via-scrapling-ai-targeted`
    - Scenario `html-to-markdown-fallback`
    - Scenario `temp-file-cleanup`

### Phase 4: CLI 集成 — Crawl/Scrape 并行化

- [x] 2.9 **crawl 命令增加管线路由逻辑** — `scripts/chrome-agent-cli.mjs`
  - `runCrawl()` 入口: 读取 strategy frontmatter 后检查 `api.platform`
  - API 模式 (`api.platform === "mediawiki"`): 路由到现有 `scripts/mediawiki-api-extract`（不变）
  - Browser 模式: 检查 `--parallel` 标志，选择 Obscura serve pool 或 Scrapling 串行
  - 覆盖 spec `crawl-strategy-router` Requirements `crawl-strategy-routing`
- [x] 2.10 **crawl 并行三阶段工作流** — 同上文件
  - Phase 1: 复用现有 Scrapling get 遍历逻辑，收集 visited URLs（与串行一致）
  - Phase 2: 调用 `startObscuraServe` + `concurrentFetch` 批量获取内容
  - Phase 3: 调用 `convertTraversalToMarkdown`（与串行一致，零改动）
  - 覆盖 spec `crawl-strategy-router` Requirement `crawl-parallel-three-phase`
- [x] 2.11 **scrape 命令增加 --parallel/--workers 参数** — 同上文件
  - 新增 `--parallel` flag: 布尔值，默认 false
  - 新增 `--workers` flag: 数字，默认 5，上限 30
  - 参数解析: 在 `parseArgs / opts` 中传递
  - 覆盖 spec `scrape-parallel-mode` Requirements `scrape-parallel-flag`, `scrape-parallel-workers-flag`

### Phase 5: 新增 batch 命令

- [x] 2.12 **新增 batch 命令入口** — `scripts/chrome-agent-cli.mjs`
  - CLI 参数: `chrome-agent batch <urls...> [--workers 5] [--timeout 15] [--markdown] [--output <dir>]`
  - 流程: Obscura preflight → startObscuraServe → concurrentFetch → stopObscuraServe → (可选) Markdown 转换
  - 降级: Obscura 不可用时 → 串行 Scrapling get fetch
  - 覆盖 spec `batch-command` Requirements `batch-command-syntax`, `batch-command-fallback`

### Phase 6: 依赖文档更新

- [x] 2.13 **更新 fallback escalation 文档** — `docs/playbooks/fallback-escalation.md`
  - 在 escalation chain 中 `obscura-fetch` 之后、`scrapling-fetch` 之前插入 `obscura-serve-pool` 的推荐路径
  - 注明: 仅在批量/并行场景使用，单 URL fetch 仍走原来的 obscura-fetch
- [x] 2.14 **更新 scrapling fetchers 文档** — `docs/playbooks/scrapling-fetchers.md`
  - 新增 `obscura-serve-pool` 章节，包含:
    - 使用场景: 批量动态页抓取
    - 命令格式: `chrome-agent batch <urls...> --workers N`
    - 与 `scrapling-bulk-fetch` 的对比与选择建议
- [x] 2.15 **更新 doctor 命令** — `scripts/chrome-agent-cli.mjs`
  - doctor 输出增加 Obscura CLI 状态报告
  - 检查并显示: `obscura` 版本、`obscura-worker` 可用性、serve 子命令兼容性

## 3. 收敛与验证准备

- [x] 3.1 整理进入 verification 的证据与检查点
  - Phase 1 完成后: `obscura --help` 输出确认 v0.1.2，`obscura-worker` 可用
  - Phase 3 完成后: serve 生命周期测试 (启动/停止/超时/端口冲突)
  - Phase 4 完成后: crawl --parallel 对 8 页动态站的加速比回归 (≥2.4x vs Scrapling)
  - Phase 5 完成后: batch 命令端到端测试 (10 URL, 5 workers, 完整 HTML + Markdown)
- [x] 3.2 标记进入 writeback 的摘要与状态变更
  - 配置变更: preflight 版本号、engine-registry 新增条目
  - 能力变更: 新增 serve-pool 引擎、batch 命令、crawl/scrape --parallel
  - 行为变更: crawl 管线路由逻辑

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
  - 状态: `pending_confirmation`，原因见 `writeback.md`
