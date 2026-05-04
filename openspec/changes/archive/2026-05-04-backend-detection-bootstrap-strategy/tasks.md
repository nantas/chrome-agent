# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `explore-backend-detection`: 仅修改 `runExplore()` 无策略分支，新增 `detectBackend()` 函数；不修改 `findStrategy()` 或 `runCrawl()`
  - `bootstrap-strategy-cli`: 新增 CLI 命令 `bootstrap-strategy`，新增 `runBootstrapStrategy()` 函数，修改 `printHelp()` 和 `parseArgs()`
  - `site-strategy-schema`: 仅新增可选 `backend` 字段，不修改任何必填字段或受控词汇表
- [x] 1.2 确认依赖前置条件与外部协作项
  - 依赖 `scrapling-get` 可用（由 `runScraplingPreflight()` 保障）
  - 依赖 `configs/backend-signatures.json` 存在（本 change 新建）
  - 无外部仓库依赖

## 2. 核心实现任务

### 2.1 后端指纹库

- [x] 2.1.1 新建 `configs/backend-signatures.json`
  - **Spec 覆盖**: `explore-backend-detection` — Requirement: 后端指纹检测规则
  - **实现路径**: 新建 JSON 文件，定义 `weird-gloop-mediawiki-1.45` 后端指纹
  - **验证方式**: 文件存在且 JSON 可解析；包含 `detection`、`reusable_strategies`、`cleanup_profile_options`

### 2.2 CLI explore 增强

- [x] 2.2.1 在 `scripts/chrome-agent-cli.mjs` 中新增 `detectBackend(htmlContent, targetUrl)` 函数
  - **Spec 覆盖**: `explore-backend-detection` — Requirement: 后端指纹检测规则、检测安全性与隔离
  - **实现路径**: 读取 `configs/backend-signatures.json`；按 AND 逻辑匹配 `meta_generator`、`dom_selector`、`url_patterns`
  - **验证方式**: ✅ 已通过真实站点验证（runescape.wiki → 命中 weird-gloop-mediawiki-1.45；example.com → 未命中）

- [x] 2.2.2 修改 `runExplore()` 函数 — 无策略时触发后端检测
  - **Spec 覆盖**: `explore-backend-detection` — Requirement: 后端检测触发条件
  - **实现路径**: 在 `!strategy` 分支后，调用 `runScraplingFetch(repoRoot, "get", targetUrl, htmlPath)` 抓取 raw HTML；然后调用 `detectBackend()`
  - **验证方式**: ✅ 对无策略的 MediaWiki URL（runescape.wiki）执行 explore，输出包含 "Detected backend: Weird Gloop MediaWiki 1.45.x"

- [x] 2.2.3 修改 `runExplore()` 函数 — 检测命中时生成推荐报告
  - **Spec 覆盖**: `explore-backend-detection` — Requirement: 可复用策略推荐
  - **实现路径**: 命中 backend 时，从 `reusable_strategies` 读取候选域名，构造 `next_action`: `Run chrome-agent bootstrap-strategy <url> --from <domain>`
  - **验证方式**: ✅ 报告中的 `next_action` 包含具体可执行的 bootstrap 命令

- [x] 2.2.4 修改 `runExplore()` 函数 — 检测未命中时保持现有行为
  - **Spec 覆盖**: `explore-backend-detection` — Requirement: 后端指纹检测规则（Scenario: 检测未命中）
  - **实现路径**: 未命中 backend 时，直接返回现有策略缺口报告，不修改任何文本
  - **验证方式**: ✅ 对无策略且无后端指纹的 URL（example.com）执行 explore，输出与修改前完全一致

### 2.3 CLI bootstrap-strategy 命令

- [x] 2.3.1 修改 `printHelp()` — 新增 `bootstrap-strategy` 命令帮助文本
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: 命令接口
  - **实现路径**: 在 help 文本中新增 `bootstrap-strategy <url> --from <domain> [--profile <name>]`
  - **验证方式**: ✅ `chrome-agent --help` 输出包含 bootstrap-strategy 说明

- [x] 2.3.2 修改 `parseArgs()` — 解析 `--from` 和 `--profile` 参数
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: 命令接口
  - **实现路径**: 新增 `fromDomain` 和 `profile` 字段的解析逻辑
  - **验证方式**: ✅ `--from` 和 `--profile` 参数正确解析

- [x] 2.3.3 新增 `runBootstrapStrategy()` 函数 — 参考策略验证
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: 参考策略验证
  - **实现路径**: 检查 `--from` domain 是否存在于 registry.json；检查目标 domain 是否已存在于 registry.json
  - **验证方式**: ✅ 对不存在的 `--from` 返回 failure；对已存在目标的 URL 返回 failure

- [x] 2.3.4 新增 `runBootstrapStrategy()` 函数 — 字段适配与策略生成
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: 字段适配规则、Markdown body 生成
  - **实现路径**: 读取参考策略 frontmatter → 替换 domain、description、url_example → 生成 Markdown body（含 bootstrap 标记和 review 提示）
  - **验证方式**: ✅ 生成的 `strategy.md` YAML frontmatter 完整；body 包含 bootstrap 标记和 review 提示

- [x] 2.3.5 新增 `runBootstrapStrategy()` 函数 — registry.json 更新
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: Registry 索引更新
  - **实现路径**: 将新条目追加到 `registry.json` 的 `entries` 数组；包含所有必填字段
  - **验证方式**: ✅ 执行后 `registry.json` 包含新 domain 条目；JSON 格式有效

- [x] 2.3.6 修改 `main()` switch — 新增 `bootstrap-strategy` 路由
  - **Spec 覆盖**: `bootstrap-strategy-cli` — Requirement: 命令接口
  - **实现路径**: 在 switch 中新增 `case "bootstrap-strategy"` 调用 `runBootstrapStrategy()`
  - **验证方式**: ✅ `chrome-agent bootstrap-strategy ...` 正确进入新函数

### 2.4 Schema 更新

- [x] 2.4.1 更新 `openspec/specs/site-strategy-schema/spec.md` — 新增 `backend` 字段说明
  - **Spec 覆盖**: `site-strategy-schema` — Requirement: YAML frontmatter 必填与可选字段、Registry.json 新增 backend 索引字段
  - **实现路径**: 在现有 spec 的字段表中新增 `backend` 行；新增 registry.json 字段说明
  - **验证方式**: ✅ spec 文件包含完整的 `backend` 字段定义和 scenario

## 3. 收敛与验证准备

- [x] 3.1 整理需要进入 verification 的证据与检查点
  - `explore` 后端检测端到端测试（MediaWiki 命中 vs 非 MediaWiki 未命中）✅
  - `bootstrap-strategy` 成功/失败场景测试 ✅
  - `registry.json` 一致性检查 ✅
  - 生成策略的 frontmatter 完整性验证 ✅

- [x] 3.2 标记需要进入 writeback 的摘要与状态变更
  - `sites/README.md` 新增 bootstrap-strategy 操作说明
  - `docs/patterns/mediawiki-extraction.md` 可选扩展（后端检测引用）
  - `AGENTS.md` section 7 更新（策略库操作说明）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`
  - 覆盖 spec-to-implementation 映射
  - 覆盖 task-to-evidence 映射
  - 记录端到端测试证据

- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`
  - 目标、字段映射、前置条件
  - 回写执行结果记录

- [x] 4.3 执行 `writeback.md` 中定义的回写目标
  - 更新 `sites/README.md` ✅
  - 可选更新 `docs/patterns/mediawiki-extraction.md` ✅
  - 可选更新 `AGENTS.md` ✅
