# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 5 个 capability spec 的覆盖范围与图表要求
  - `docs-strategy-schema-diagrams` — 3 个图表
  - `docs-cli-routing-diagrams` — 2 个图表
  - `docs-tech-stack-dependency-graph` — 2 个图表
  - `docs-pipeline-flow-phase-naming` — 命名更新
  - `docs-converter-path-update` — 路径更新
- [x] 1.2 确认当前 `02-pipeline-flow.md` 中所有需要更新的 Phase 命名位置
  - 执行: `grep -n "Phase 0\|Phase A\|Phase B\|Phase C\|run_phase_0\|run_phase_a\|run_phase_c" docs/architecture/02-pipeline-flow.md`
- [x] 1.3 确认当前 `05-converter-architecture.md` 中所有需要更新的路径引用
  - 执行: `grep -n "pipeline/converters/html_to_markdown\|html_to_markdown\.py" docs/architecture/05-converter-architecture.md`

## 2. 核心实现任务

### 2.1 文档 `03-strategy-schema.md` — 新增视觉元素 (spec: docs-strategy-schema-diagrams)

- [x] 2.1.1 增加系统上下文图
  - 文件: `docs/architecture/03-strategy-schema.md`
  - 插入位置: "概述"节末尾
  - 内容: ASCII 图展示 strategy.md ↔ registry.json ↔ pipeline ↔ explore ↔ extraction 的关系
  - 源注释: `<!-- Source: scripts/lib/strategy_loader.py, scripts/pipeline/pipeline/registry.py -->`
  - 验证: 非开发者能在 30 秒内理解策略文件在系统中的位置

- [x] 2.1.2 增加字段层级树
  - 文件: `docs/architecture/03-strategy-schema.md`
  - 插入位置: "字段详细说明"节开头
  - 内容: ASCII 树状图，YAML key 嵌套关系，✅ 必填 / ❌ 可选标记
  - 源注释: `<!-- Source: sites/strategies/<domain>/strategy.md frontmatter schema -->`
  - 验证: 树的深度覆盖所有嵌套层级（`domain` → `api` → `content_profile` → `discovery_strategy` 等）

- [x] 2.1.3 增加 content_profile 策略路由图
  - 文件: `docs/architecture/03-strategy-schema.md`
  - 插入位置: "content_profile 合法值"节开头
  - 内容: ASCII 图展示 5 个 content_profile 维度 → `_STRATEGY_REGISTRY` → Python 策略类
  - 源注释: `<!-- Source: scripts/pipeline/pipeline/registry.py:_STRATEGY_REGISTRY -->`
  - 验证: 每个维度显示所有已注册的策略 ID

### 2.2 文档 `04-cli-reference.md` — 新增视觉元素 (spec: docs-cli-routing-diagrams)

- [x] 2.2.1 增加命令路由决策树
  - 文件: `docs/architecture/04-cli-reference.md`
  - 插入位置: "概述"节末尾
  - 内容: ASCII 决策树展示 explore/fetch/crawl/scrape → 后端选择路径
  - 源注释: `<!-- Source: scripts/chrome-agent-cli.mjs: runExplore/runFetch/runCrawl/runScrape -->`
  - 验证: 每个分支标注对应的 CLI 函数名和行号

- [x] 2.2.2 增加管线阶段流程图
  - 文件: `docs/architecture/04-cli-reference.md`
  - 插入位置: "pipeline 子命令参数"节附近
  - 内容: ASCII 流程图展示 `--discovery` + `--phase` 参数如何决定五阶段执行
  - 源注释: `<!-- Source: scripts/pipeline/pipeline/orchestrator.py:76 run_pipeline() -->`
  - 验证: 包含默认路径、discovery-only 路径、resume 路径

### 2.3 文档 `08-tech-stack.md` — 新增视觉元素 (spec: docs-tech-stack-dependency-graph)

- [x] 2.3.1 增加组件依赖关系图
  - 文件: `docs/architecture/08-tech-stack.md`
  - 插入位置: "Runtime Dependencies"节之前（新建 "System Architecture" 节）
  - 内容: ASCII 图展示 Node.js CLI → Python pipeline/explore → 共享 lib/ → 引擎 → 输出
  - 源注释: `<!-- Source: scripts/ directory structure, package.json, configs/engine-versions.json -->`
  - 验证: 单向依赖箭头（无循环），每层标注主要文件路径

- [x] 2.3.2 增加安装脚本链流程图
  - 文件: `docs/architecture/08-tech-stack.md`
  - 插入位置: "External Engine Dependencies"节后
  - 内容: ASCII 流程图展示 install-chrome-agent-cli.sh → 各 preflight 脚本 → engine-version-check.sh 的执行顺序
  - 源注释: `<!-- Source: scripts/*.sh, scripts/engine-version-check.sh -->`
  - 验证: 每个脚本标注其管理的安装路径

### 2.4 文档 `02-pipeline-flow.md` — 命名更新 (spec: docs-pipeline-flow-phase-naming)

- [x] 2.4.1 更新 Phase 标题和引用
  - 文件: `docs/architecture/02-pipeline-flow.md`
  - 替换: "Phase 0" → "homepage discovery", "Phase A" → "allpages discovery"
  - 替换: "Phase C" → "assembly"
  - 替换: `run_phase_0()` → `run_homepage_discovery()`
  - 替换: `run_phase_a()` → `run_allpages_discovery()`
  - 替换: `run_phase_c()` → `run_assemble()`
  - 验证: `grep "Phase 0\|Phase A\|Phase B\|Phase C" docs/architecture/02-pipeline-flow.md` 零匹配（排除作为过渡说明的行）

- [x] 2.4.2 更新流程图中 Phase 节点标签
  - 验证: 流程图中无 `Phase 0`, `Phase A`, `Phase B`, `Phase C` 节点标签

### 2.5 文档 `05-converter-architecture.md` — 路径更新 (spec: docs-converter-path-update)

- [x] 2.5.1 更新模块清单
  - 文件: `docs/architecture/05-converter-architecture.md`
  - 将 `html_to_markdown.py` 从 "Pipeline Converters" 表移至 "Shared Extraction Library" 表
  - 路径更新为 `scripts/lib/extraction/converter.py`
  - 验证: Pipeline Converters 表中无 `html_to_markdown.py`

- [x] 2.5.2 更新 "Design Decision" 说明
  - 更新 §2.3 中关于文件位置的理由
  - 验证: 与当前代码实际状态一致

- [x] 2.5.3 更新数据流图中的路径引用
  - 验证: `grep "pipeline/converters/html_to_markdown" docs/architecture/05-converter-architecture.md` 零匹配

## 3. 收敛与验证准备

- [x] 3.1 全局验证：确认所有 5 篇文档无残留过时引用
  - 执行: `grep -rn "Phase [0ABC]\|run_phase_\|pipeline/converters/html_to_markdown" docs/architecture/`
  - 验证: 零匹配

- [x] 3.2 可读性验证：确认新增图表覆盖所有 spec 要求
  - `03-strategy-schema.md` 含 3 个 ASCII 图
  - `04-cli-reference.md` 含 2 个 ASCII 图
  - `08-tech-stack.md` 含 2 个 ASCII 图

- [x] 3.3 准确性验证：确认图表中的路径/函数名与代码一致
  - 抽查 3 个函数名/路径引用 vs 实际代码

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行回写
