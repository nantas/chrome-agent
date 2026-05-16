# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `explore`: 移除 `runExplore()` 静默 try/catch + legacy fallback，增加 preflight 错误返回
  - `explore-workflow`: `main.py` 启动依赖自检 + CLI preflight 检查
  - `doctor-repo-freshness`: doctor 新增 `explore_deps` 检查条目
  - `pipeline-converters`: `HtmlToMarkdownConverter` 参数化 domain + 配置化 cleanup/image filter
  - `agents-governance`: AGENTS.md 新增 explore→crawl 确认门规则段
  - `explore-skill-gates`: SKILL.md 新增 Gate 1-4 + Result Interpretation 章节

- [x] 1.2 确认依赖前置条件
  - `beautifulsoup4>=4.12` 和 `pyyaml>=6.0` 需安装到 `scripts/explore/` 的 Python 环境
  - `scripts/explore/main.py` 自身不引入新的外部模块依赖（仅 stdlib + bs4 + yaml）
  - `HtmlToMarkdownConverter` 重构不影响 `phase_b.py` / `phase_c.py` / `standalone.py` 的外部接口（仅 `__init__` 签名变化）

## 2. 核心实现任务

### A 系列：管线依赖与 preflight（spec: explore, explore-workflow）

- [x] 2.A1 新建 `scripts/explore/requirements.txt`
  - 内容：`beautifulsoup4>=4.12` + `pyyaml>=6.0`
  - 验证：文件存在于正确路径，内容与 spec `pipeline-dependency-preflight` 的 `deps-file-declaration` scenario 一致

- [x] 2.A2 在 `scripts/explore/main.py` 增加启动依赖自检
  - `main()` 函数开头尝试 `import bs4, yaml`
  - 缺失时打印 `FATAL: Missing dependencies: ...` 到 stderr 并 `sys.exit(1)`
  - 覆盖 spec:`main-py-dependency-self-check`, `main-py-dependencies-present`

- [x] 2.A3 在 `scripts/chrome-agent-cli.mjs` 中新建 `runExplorePythonDepsCheck()`
  - 执行 `python3 -c "import bs4, yaml; print('ok')"`
  - 返回 `{ ok: boolean, detail: string }`
  - 覆盖 spec:`cli-preflight-before-spawn`

- [x] 2.A4 在 `runExplore()` 中增加 preflight 调用，在 `spawnSync` 之前
  - 调用 `runExplorePythonDepsCheck(repoRoot)`
  - 失败时返回 `makeResult(..., "failure", ...)`，含安装指令
  - 成功时继续现有 deep discovery 路径
  - 覆盖 spec:`explore-preflight-failure` (python-deps-missing)

- [x] 2.A5 移除 `runExplore()` 中的静默 try/catch（lines 1210-1224）
  - 改为非静默的 `spawnSync` 调用 + exit code 检查
  - 非零退出码时返回 `makeResult(..., "failure", ...)` 含前 500 字符 stderr
  - 覆盖 spec:`explore-preflight-failure` (deep-discovery-execution-failure)

- [x] 2.A6 移除 `runExplore()` 中的 legacy fallback 代码
  - 删除 `if (!discoveryResult)` 分支（HTML fetch + `detectBackend` + bootstrap 建议）
  - 删除 `buildExploreReport` 的 `backend` / `htmlFetchResult` 参数传递
  - 覆盖 spec:`explore-legacy-fallback-removal`

### B 系列：Doctor preflight 扩展（spec: doctor-repo-freshness）

- [x] 2.B1 在 `runDoctor()` 中新增 `explore_deps` 检查条目
  - 复用 `runExplorePythonDepsCheck()` 函数
  - 检查条目 push 到 `checks` 数组
  - 覆盖 spec:`explore-python-deps-available`, `explore-python-deps-missing`

### C 系列：Converter 通用化（spec: pipeline-converters）

- [x] 2.C1 修改 `HtmlToMarkdownConverter.__init__`
  - `wiki_domain` 从默认参数改为必传参数（无默认值）
  - 增加 `extraction_config: dict | None = None` 参数
  - `self.config = extraction_config or {}`
  - `self._REMOVAL_SELECTORS` 从 `self.config.get("cleanup_selectors", [...defaults...])` 读取
  - 覆盖 spec:`domain-required`, `domain-explicit`, `cleanup-from-extraction-config`

- [x] 2.C2 修改 `clean_html()` 中的 image 过滤
  - 移除所有硬编码的 StS2 pattern（`StS2_Bg`, `StS2_Frame`, `StS2_Banner`, `StS2_Type`, `StS2_Card*Orb`, `Art.png`）
  - 改为从 `self.config.get("image_filtering", {}).get("skip_patterns", [])` 读取 patterns
  - 循环执行 `parser.css(f'img[src*="{pattern}"]')` 并 `decompose()`
  - 覆盖 spec:`image-filter-from-extraction-config`

- [x] 2.C3 修改 `_regex_clean()` 方法
  - 移除正则中的 StS2 硬编码 pattern
  - 如果 selectolax 不可用，仅执行 selector-based removal（使用简单正则），不保留 StS2 特定 pattern
  - 覆盖 spec:`config-driven-cleanup`

- [x] 2.C4 在 `phase_b.py` / `phase_c.py` / `standalone.py` 更新 converter 实例化
  - 传递 `wiki_domain`（从 strategy 的 `domain` 或 `api.base_url` 提取 hostname）
  - 传递 `extraction_config`（从 strategy 的 `extraction` 段读取）
  - 覆盖 spec:`domain-from-strategy`, `strategy-passes-extraction-config`

- [x] 2.C5 更新 `sites/strategies/slaythespire.wiki.gg/strategy.md`
  - 在 `extraction` 段增加 `cleanup_selectors`（显式列出之前硬编码的 selector）
  - 在 `extraction` 段增加 `image_filtering.skip_patterns`（显式列出 StS2_Bg 等 pattern）
  - 覆盖 spec:`sts-backward-compatibility`
  - 验证：对 StS 站点运行 Phase B 单页提取，输出与变更前逐字节一致

### D 系列：治理文档更新（spec: agents-governance, explore-skill-gates）

- [x] 2.D1 在 `AGENTS.md` 的 Governance Rules 区域新增「Explore→Crawl Confirmation Gate」章节
  - 内容与 spec `explore-crawl-confirmation-gate` 一致
  - 位置：在「Intent Routing」大段之后
  - 覆盖 spec:`agent-reads-confirmation-gate`, `explore-failure-prohibition`, `section-placement`

- [x] 2.D2 在 `~/.agents/skills/chrome-agent/SKILL.md` 新增「Explore Workflow Gates」章节
  - Gate 1: Structure Analysis Confirmation（结构分析确认）
  - Gate 2: Sample Conversion（采样转换）
  - Gate 3: LLM Self-Check（LLM 自检）
  - Gate 4: User Confirmation（用户确认）
  - 覆盖 spec: `skill-gate-structure-analysis`, `skill-gate-sample-conversion`, `skill-gate-llm-self-check`, `skill-gate-user-confirmation`

- [x] 2.D3 在 SKILL.md 新增「Explore Result Interpretation」章节
  - 字段映射表（discovery fields → purpose → gate）
  - failure 结果处理指令
  - 覆盖 spec:`field-mapping-table`, `failure-result-handling`

### E 系列：Isaac wiki 策略配置补全（spec: pipeline-converters）

- [x] 2.E1 更新 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 在 `extraction` 段增加 `cleanup_selectors`（基于 Isaac wiki 的 DOM 特征）
  - 在 `extraction` 段增加 `image_filtering.skip_patterns`（移除 logo 等非内容图片）
  - 验证：对 Isaac wiki 2-3 个样本页面运行单页提取，检查 Markdown 无 HTML artifact

## 3. 收敛与验证准备

- [x] 3.1 整理 verification 证据清单
  - `chrome-agent doctor --format json` 输出含 `explore_deps` 检查项
  - `chrome-agent explore <wiki-url>` 在策略缺口时返回 deep discovery 结果（非 "strategy gap"）
  - `chrome-agent explore <wiki-url>` 在管线依赖缺失时返回 failure + 安装指令
  - `HtmlToMarkdownConverter` 实例化不传 `wiki_domain` 时抛出 TypeError
  - `HtmlToMarkdownConverter` 对 StS 页面的输出与变更前一致
  - AGENTS.md 包含「Explore→Crawl Confirmation Gate」章节
  - SKILL.md 包含 Gate 1-4 和 Result Interpretation 章节

- [x] 3.2 标记 writeback 目标
  - 六个 spec 文件：`explore`, `explore-workflow`, `doctor-repo-freshness`, `pipeline-converters`, `agents-governance`, `explore-skill-gates`
  - 回写内容：implementation_status 更新

## 4. 依赖与执行顺序

```
2.A1 (requirements.txt)
  → 2.A2 (main.py 自检)
  → 2.A3 (explorePythonDepsCheck)
    → 2.A4 (runExplore preflight)
    → 2.A5 (移除 try/catch)
    → 2.A6 (移除 legacy)
    → 2.B1 (doctor explore_deps)

2.C1 (converter __init__)
  → 2.C2 (clean_html image filter)
  → 2.C3 (regex_clean)
    → 2.C4 (phase_b/c 更新)
    → 2.C5 (StS 策略)
    → 2.E1 (Isaac 策略)

2.D1 (AGENTS.md)
2.D2 (SKILL.md gates)
2.D3 (SKILL.md interpretation)
  # D 系列可并行执行，与其他系列无依赖
```
