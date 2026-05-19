# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 6 个 capability spec 均已完成且覆盖本次 change 全部范围
  - `pipeline-registry`: registry + factory + derive_capabilities → `specs/pipeline-registry/spec.md`
  - `pipeline-discovery-summary`: build_discovery_summary + 5 辅助函数 → `specs/pipeline-discovery-summary/spec.md`
  - `pipeline-phases-fetch`: run_phase_fetch → `specs/pipeline-phases-fetch/spec.md`
  - `pipeline-phases-convert`: run_phase_convert → `specs/pipeline-phases-convert/spec.md`
  - `pipeline-orchestration`: 精简后的 orchestrator → `specs/pipeline-orchestration/spec.md`
  - `pipeline-package-identity`: 包重命名 + 路径更新 → `specs/pipeline-package-identity/spec.md`

- [x] 1.2 确认前置条件：Change 1（`lib/`）和 Change 2（`lib/extraction/`）已完成且验证通过
  - `grep -n "from.*lib\." scripts/mediawiki-api-extract/pipeline/orchestrate.py` 确认已使用 `lib/`
  - `grep "def _extract_infobox" scripts/explore/sample_converter.py` 返回空确认 Change 2 完成

## 2. 核心实现任务

### Phase A: 模块拆分（在现有包结构内）

- [x] 2.1 创建 `pipeline/registry.py` — 从 `orchestrate.py` 提取策略注册表
  - 移入: `PipelineStrategies`, `DEFAULT_STRATEGIES`, `_STRATEGY_REGISTRY`, `_PROFILE_KEY_MAP`, `STRATEGY_REGISTRY`, `PROFILE_KEY_MAP`, `derive_capabilities()`, `build_pipeline()`
  - import: `..strategies` 中的策略类
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.pipeline.registry import STRATEGY_REGISTRY, build_pipeline; print('OK')"`
  - Spec 覆盖: `pipeline-registry` 全部 requirements

- [x] 2.2 创建 `pipeline/discovery_summary.py` — 从 `orchestrate.py` 提取发现摘要
  - 移入: `build_discovery_summary()`, `_build_homepage_categories()`, `_build_allpages_categories()`, `_build_excluded_list()`, `_build_unclassified()`, `_estimate_time()`
  - import: `os`, `math`, `...lib.config_resolver.RateLimitConfig`
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.pipeline.discovery_summary import build_discovery_summary; print('OK')"`
  - Spec 覆盖: `pipeline-discovery-summary` 全部 requirements

- [x] 2.3 创建 `pipeline/phases/` 目录和 `__init__.py`

- [x] 2.4 创建 `pipeline/phases/fetch.py` — 从 `orchestrate.py` 提取 Phase Fetch
  - 移入: `run_phase_fetch()` 及其内部 `_fetch_one()`
  - import: `time`, `concurrent.futures`, `..client.ApiClient/PageNotFoundError`, `..phase_b.fetch_single_page`, `..cache as cache_mod`
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.pipeline.phases.fetch import run_phase_fetch; print('OK')"`
  - Spec 覆盖: `pipeline-phases-fetch` 全部 requirements

- [x] 2.5 创建 `pipeline/phases/convert.py` — 从 `orchestrate.py` 提取 Phase Convert
  - 移入: `run_phase_convert()`
  - import: `..phase_b.convert_single_page`, `..registry.build_pipeline`, `..cache as cache_mod`, `..strategies` 策略类
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.pipeline.phases.convert import run_phase_convert; print('OK')"`
  - Spec 覆盖: `pipeline-phases-convert` 全部 requirements

- [x] 2.6 精简 `pipeline/orchestrate.py` — 删除已移出的代码，改为 import
  - 保留: exit 常量 (L37-54) + `validate_api_config()` + `run_pipeline()` 主编排
  - 替换内联调用: `build_pipeline` → `registry.build_pipeline`, `build_discovery_summary` → `discovery_summary.build_discovery_summary`, `run_phase_fetch` → `phases.fetch.run_phase_fetch`, `run_phase_convert` → `phases.convert.run_phase_convert`
  - 删除已移出的函数定义和注册表数据
  - 验证: `wc -l scripts/mediawiki-api-extract/pipeline/orchestrate.py` ≤ 350 行
  - Spec 覆盖: `pipeline-orchestration` 全部 requirements

- [x] 2.7 更新 `pipeline/__init__.py` 导出 — 确保公共 API 不变
  - 从 `orchestrator.py` 导出: `run_pipeline`, exit codes, `validate_api_config`
  - 从 `registry.py` 导出: `build_pipeline`, `STRATEGY_REGISTRY`, `PROFILE_KEY_MAP`, `derive_capabilities`, `PipelineStrategies`
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.pipeline import run_pipeline, EXIT_SUCCESS, STRATEGY_REGISTRY; print('OK')"`

- [x] 2.8 端到端验证（拆分后、重命名前）
  - `python3 -m scripts.mediawiki-api-extract --help` 正常
  - `python3 scripts/mediawiki-api-extract/tests/test_discovery_summary.py` 通过
  - 确认无循环 import: `python3 -c "import scripts.mediawiki_api_extract.pipeline.orchestrate; print('OK')"`

### Phase B: 包重命名

- [x] 2.9 执行目录重命名
  - `mv scripts/mediawiki-api-extract scripts/pipeline`
  - 验证: `ls scripts/pipeline/` 确认目录存在

- [x] 2.10 更新 Python 绝对 import 路径
  - 全局替换 `scripts.mediawiki_api_extract` → `scripts.pipeline`（约 5 处 `.py` 文件中的 docstring/注释 import 示例）
  - 验证: `grep -rn "mediawiki_api_extract" scripts/pipeline/ --include='*.py' | grep -v __pycache__` 返回 0 匹配
  - Spec 覆盖: `pipeline-package-identity` → package-rename

- [x] 2.11 简化 `__main__.py`
  - 删除 re-invoke workaround，改为直接 `from .cli import main` + `sys.exit(main())`
  - 验证: `python3 -m scripts.pipeline --help` 正常，无 subprocess re-invoke
  - Spec 覆盖: `pipeline-package-identity` → main-simplification

- [x] 2.12 更新 `chrome-agent-cli.mjs` 硬编码路径
  - L2073: `path.join(repoRoot, "scripts", "mediawiki-api-extract")` → `path.join(repoRoot, "scripts", "pipeline")`
  - L2077: `"-m", "scripts.mediawiki-api-extract"` → `"-m", "scripts.pipeline"`
  - L2201: `"mediawiki-api-extract script not found"` → `"pipeline script not found"`
  - 验证: `grep -n "mediawiki-api-extract" scripts/chrome-agent-cli.mjs` 返回 0 匹配
  - Spec 覆盖: `pipeline-package-identity` → cli-spawn-path-update

- [x] 2.13 更新 logger 名称
  - 全局替换 `getLogger("mediawiki-api-extract")` → `getLogger("pipeline")`
  - 子模块 `getLogger("mediawiki-api-extract.converters")` → `getLogger("pipeline.converters")`
  - `lib/config_resolver.py` 的 logger 也同步更新
  - 验证: `grep -rn 'getLogger("mediawiki-api-extract' scripts/ --include='*.py' | grep -v __pycache__` 返回 0 匹配
  - Spec 覆盖: `pipeline-package-identity` → logger-name-update

- [x] 2.14 更新 `scripts/explore/` 中的路径引用
  - `architecture_gate.py` L16: `scripts/mediawiki-api-extract/converters/html_to_markdown.py` → `scripts/pipeline/converters/html_to_markdown.py`
  - `sample_converter.py` L144: `scripts.mediawiki-api-extract.converters.html_to_markdown` → `scripts.pipeline.converters.html_to_markdown`
  - `strategy_scaffold_generator.py` L174: `scripts/mediawiki-api-extract/pipeline/orchestrate.py` → `scripts/pipeline/pipeline/orchestrator.py`
  - `strategy_scaffold_generator.py` L178: `mediawiki_api_extract.pipeline.orchestrate` → `pipeline.pipeline.orchestrate`
  - 验证: `grep -rn "mediawiki-api-extract\|mediawiki_api_extract" scripts/explore/ --include='*.py'` 返回 0 匹配
  - Spec 覆盖: `pipeline-package-identity` → external-reference-update

- [x] 2.15 更新测试文件路径引用
  - `scripts/pipeline/tests/test_discovery_summary.py` L12: `scripts/mediawiki-api-extract/pipeline/orchestrate.py` → `scripts/pipeline/pipeline/orchestrator.py`
  - 验证: `grep -rn "mediawiki-api-extract" scripts/pipeline/tests/` 返回 0 匹配
  - Spec 覆盖: `pipeline-package-identity` → test-reference-update

- [x] 2.16 更新 `client.py` 中的 User-Agent 字符串
  - L40: `"chrome-agent/mediawiki-api-extract"` → `"chrome-agent/pipeline"`
  - L124: 同上
  - 验证: `grep -n "mediawiki-api-extract" scripts/pipeline/client.py` 返回 0 匹配

- [x] 2.17 更新 `strategies.py` 代理文件 docstring
  - L3: `from scripts.mediawiki_api_extract.strategies import X` → `from scripts.pipeline.strategies import X`
  - 验证: `grep "mediawiki_api_extract" scripts/pipeline/strategies.py` 仅在注释中存在（如有保留历史说明）

- [x] 2.18 更新 `converters/` 内的 docstring import 示例
  - `html_to_markdown.py` L6: `from scripts.mediawiki_api_extract.converters.html_to_markdown import ...` → `from scripts.pipeline.converters.html_to_markdown import ...`
  - `card_stats.py` L4: 同理更新
  - `wikitext_to_md.py` L4: 同理更新
  - `fandom_html_to_markdown.py`: 检查是否有类似引用
  - 验证: `grep -rn "mediawiki_api_extract" scripts/pipeline/converters/ --include='*.py'` 返回 0 匹配

## 3. 收敛与验证准备

- [x] 3.1 整理验证证据清单
  - 拆分后 `orchestrator.py` 行数 ≤ 350
  - `python3 -m scripts.pipeline --help` 成功
  - `python3 scripts/pipeline/tests/test_discovery_summary.py` 全部通过
  - `node --test tests/` 全部通过
  - `grep -rn "mediawiki-api-extract\|mediawiki_api_extract" scripts/ --include='*.py' --include='*.mjs' | grep -v __pycache__` 返回 0 匹配（或仅注释保留）

- [x] 3.2 标记需要回写 `AGENTS.md` 的变更
  - §7 Pipeline Strategy Schema 治理: `_STRATEGY_REGISTRY` 权威来源从 `scripts/mediawiki-api-extract/pipeline/orchestrate.py` 更新为 `scripts/pipeline/pipeline/registry.py`
  - §9 Python 脚本约定: 包名、调用方式、`__main__.py` 说明更新
  - §9 常见陷阱: 更新 `__main__.py` 陷阱说明（不再需要 `-m` workaround）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
