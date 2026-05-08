# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界（5 个 spec 已生成）
- [x] 1.2 确认依赖前置条件：selectolax 可选、requests 必选、pyyaml 必选

## 2. 核心实现任务

### Phase 1: 基础修复（pipeline-cli-entry spec）

- [x] 2.1 **修复 `__main__.py` sys.path**
  - Spec 覆盖: `pipeline-cli-entry` → `main-runnable-as-script`
  - 实现: 在 `__main__.py` 顶部增加 `__package__` 修复块（design D6）
  - 验证: `python3 scripts/mediawiki-api-extract --help` 和 `python3 -m scripts.mediawiki_api_extract --help` 都能输出帮助信息

- [x] 2.2 **修复 `chrome-agent-cli.mjs` 调用方式**
  - Spec 覆盖: `pipeline-cli-entry` → `chrome-agent-cli-fix`
  - 实现: 将 L1146 附近的 `spawnSync` 参数从 `[extractionScript, ...]` 改为 `["-m", "scripts.mediawiki_api_extract", ...]`
  - 验证: `node scripts/chrome-agent-cli.mjs crawl <wiki-url>` 的 MediaWiki API 路径不再报 `ImportError`

### Phase 2: converters/ 子包拆分（pipeline-converters spec）

- [x] 2.3 **创建 `converters/html_to_markdown.py`**
  - Spec 覆盖: `pipeline-converters` → `converters-as-independent-package`
  - 实现: 从 `strategies.py` 搬出 `HtmlToMarkdownConverter` 类及全部私有方法，去除对 `client` 的依赖
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter; print('OK')"`

- [x] 2.4 **创建 `converters/wikitext_to_md.py`**
  - Spec 覆盖: `pipeline-converters` → `converters-as-independent-package`
  - 实现: 从 `strategies.py` 搬出 `convert_wikitext_to_markdown`、`convert_wikitable_to_markdown` 及辅助函数（`_split_templates`、`_replace_dpl_template`、`_parse_wikitable_block`、`_split_table_cells`、`_clean_table_cell`）。`LinkResolver` 和 `TemplateProcessor` 通过参数注入
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.converters.wikitext_to_md import convert_wikitext_to_markdown; print('OK')"`

- [x] 2.5 **创建 `converters/card_stats.py`**
  - Spec 覆盖: `pipeline-converters` → `converters-as-independent-package`
  - 实现: 从 `strategies.py` 搬出 `extract_card_stats`、`split_card_list_pages`
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.converters.card_stats import extract_card_stats; print('OK')"`

- [x] 2.6 **创建 `converters/__init__.py`**
  - 实现: re-export 所有公开类和函数
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.converters import HtmlToMarkdownConverter, convert_wikitext_to_markdown, extract_card_stats; print('OK')"`

### Phase 3: strategies/ 子包拆分（pipeline-converters spec）

- [x] 2.7 **创建 `strategies/discovery.py`**
  - Spec 覆盖: `pipeline-converters` → `strategies-split-by-role`
  - 实现: 搬出 `AllPagesDiscoveryStrategy`、`CategoryMembersDiscoveryStrategy`
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.strategies.discovery import AllPagesDiscoveryStrategy; print('OK')"`

- [x] 2.8 **创建 `strategies/acquisition.py`**
  - 实现: 搬出 `WikitextOnlyAcquisitionStrategy`、`HybridAcquisitionStrategy`、`HtmlRenderedAcquisitionStrategy`
  - 验证: 同上模式

- [x] 2.9 **创建 `strategies/link_resolver.py`**
  - 实现: 搬出 `ExactTitleLinkResolver`、`ShortNameLinkResolver` 及辅助函数
  - 验证: 同上模式

- [x] 2.10 **创建 `strategies/template.py`**
  - 实现: 搬出 `SimpleSubstitutionTemplateProcessor`、`StructuredTemplateProcessor`、`_split_template_args`
  - 验证: 同上模式

- [x] 2.11 **创建 `strategies/list_assembler.py`**
  - 实现: 搬出 `FrontmatterDrivenListPageAssembler`、`HybridListPageAssembler`
  - 验证: 同上模式

- [x] 2.12 **创建 `strategies/__init__.py` + 兼容 shim**
  - Spec 覆盖: `pipeline-converters` → `backward-compatible-reexports`
  - 实现: Protocol 定义 + re-export 所有策略类 + 从 converters re-export `HtmlToMarkdownConverter` 等转换器
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter, AllPagesDiscoveryStrategy, ExactTitleLinkResolver; print('OK')"`

- [x] 2.13 **将旧 `strategies.py` 重命名为 `_strategies_legacy.py`（兼容 shim）**
  - 实现: 文件内容改为从新子包 re-export，保留过渡期兼容性
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.strategies import HtmlToMarkdownConverter; print('OK')"`

### Phase 4: pipeline/ 子包拆分（pipeline-converters spec）

- [x] 2.14 **创建 `pipeline/rate_limit.py`**
  - 实现: 搬出 `RateLimitConfig`、`resolve_rate_limit_config`、`_load_anti_crawl_strategy`
  - 验证: import 成功

- [x] 2.15 **创建 `pipeline/orchestrate.py`**
  - Spec 覆盖: `pipeline-converters` → `pipeline-orchestration-extracted`
  - 实现: 搬出 `run_pipeline`、`build_pipeline`、`parse_strategy`、`validate_api_config`、exit codes、`DEFAULT_STRATEGIES`、`_STRATEGY_REGISTRY`、`_PROFILE_KEY_MAP`、`PipelineStrategies`
  - 验证: import 成功

- [x] 2.16 **移动 `phase_a.py` → `pipeline/phase_a.py`**
  - 实现: 移动文件，更新内部 import（`from .client` → `from ..client`）
  - 验证: `from scripts.mediawiki_api_extract.pipeline.phase_a import run_phase_a` 成功

- [x] 2.17 **移动 `phase_b.py` → `pipeline/phase_b.py`**
  - 实现: 移动文件，更新内部 import
  - 验证: import 成功

- [x] 2.18 **移动 `phase_c.py` → `pipeline/phase_c.py`**
  - 实现: 移动文件，更新内部 import
  - 验证: import 成功

- [x] 2.19 **创建 `pipeline/__init__.py`**
  - 实现: re-export `run_pipeline` 等公开函数
  - 验证: `from scripts.mediawiki_api_extract.pipeline import run_pipeline` 成功

### Phase 5: 兼容性验证（pipeline-converters spec → no-behavior-change）

- [x] 2.20 **全量管线 smoke test**
  - Spec 覆盖: `pipeline-converters` → `no-behavior-change` / `full-pipeline-output-unchanged`
  - 实现: 对 slaythespire.wiki.gg 执行 `python3 -m scripts.mediawiki_api_extract <url> --strategy <path> --output /tmp/smoke-test --phase A B C --no-api-probe`（受限 5 个页面）
  - 验证: 管线正常完成，输出 .md 文件格式与预期一致

- [x] 2.21 **全量管线有限页面回归**
  - 实现: 使用已有策略对 slaythespire.wiki.gg 抓取 `Ironclad` 分类下的 5 个已知页面（如 Strike、Defend、Bash、Anger、Body Slam）
  - 验证: 输出 .md 文件与重构前已有文件对比（frontmatter 字段一致、card stats 存在、链接格式正确）

### Phase 6: 独立操作入口（standalone-extraction + incremental-reprocess）

- [x] 2.22 **创建 `standalone.py`**
  - Spec 覆盖: `standalone-extraction` → `single-page-fetch-and-convert`、`reconvert-existing-file`；`incremental-reprocess` → `reprocess-specified-pages`、`reprocess-preserves-successful`
  - 实现: 实现 `fetch_and_convert`、`reconvert_file`、`reprocess_pages` 三个函数
  - 验证: `python3 -c "from scripts.mediawiki_api_extract.standalone import fetch_and_convert, reconvert_file, reprocess_pages; print('OK')"`

- [x] 2.23 **单页面 fetch smoke test**
  - Spec 覆盖: `standalone-extraction` → `single-page-fetch-and-convert`
  - 实现: 对 `https://slaythespire.wiki.gg/wiki/Strike_(Ironclad)` 执行 `fetch_and_convert`（HTML 模式）
  - 验证: 输出 .md 包含 Card Stats、frontmatter、内容完整

- [x] 2.24 **增量 reprocess smoke test**
  - Spec 覆盖: `incremental-reprocess` → `reprocess-specified-pages`
  - 实现: 使用已有 manifest 对 3 个指定页面执行 `reprocess_pages`
  - 验证: 只重新处理指定页面，其他文件不变

### Phase 7: CLI 子命令路由（pipeline-cli-entry spec）

- [x] 2.25 **创建 `cli.py`**
  - Spec 覆盖: `pipeline-cli-entry` → `cli-subcommand-routing`
  - 实现: argparse 子命令（pipeline/fetch/reprocess/fix-links/reconvert），路由到对应函数
  - 验证: `python3 -m scripts.mediawiki_api_extract --help` 显示子命令列表

- [x] 2.26 **更新 `__main__.py`**
  - 实现: 替换为调用 `cli.main()`
  - 验证: `python3 -m scripts.mediawiki_api_extract fetch --help` 显示 fetch 子命令帮助

### Phase 8: 链接修复（unified-link-fixer spec）

- [x] 2.27 **创建 `converters/link_fixer.py`**
  - Spec 覆盖: `unified-link-fixer` → `fix-links-in-directory`
  - 实现: 实现 `fix_links_in_dir(output_dir, domain, manifest_pages)` 函数，统一处理 /wiki/ 链接、双重后缀、fragment、query 参数
  - 验证: 对 smoke test 输出目录执行修复，统计修复数

- [x] 2.28 **链接修复 smoke test**
  - Spec 覆盖: `unified-link-fixer` 所有场景
  - 实现: 构造包含各种问题链接的测试 .md 文件，执行 `fix_links_in_dir`
  - 验证: `/wiki/Title` → `.md` 链接、`.md.md` → `.md`、fragment 保留、query 剥离、无法解析时保留原样

### Phase 9: 端到端回归验证

- [x] 2.29 **CLI fetch 子命令端到端**
  - 执行: `python3 -m scripts.mediawiki_api_extract fetch "https://slaythespire.wiki.gg/wiki/Strike_(Ironclad)" --domain slaythespire.wiki.gg --mode html --output /tmp/strike-test.md`
  - 验证: 输出文件存在且内容有效

- [x] 2.30 **CLI reprocess 子命令端到端**
  - 执行: `python3 -m scripts.mediawiki_api_extract reprocess "https://slaythespire.wiki.gg" --pages "Strike_(Ironclad),Defend_(Ironclad)" --manifest <path> --output /tmp/reprocess-test`
  - 验证: 仅 2 个页面被处理

- [x] 2.31 **CLI fix-links 子命令端到端**
  - 执行: `python3 -m scripts.mediawiki_api_extract fix-links /tmp/smoke-test --domain slaythespire.wiki.gg --manifest <path>`
  - 验证: 输出修复统计

- [x] 2.32 **chrome-agent-cli.mjs 端到端**
  - 执行: 通过 `chrome-agent crawl <wiki-url>` 触发 MediaWiki API 路径
  - 验证: 不再出现 `ImportError`，管线成功运行

## 3. 收敛与验证准备

- [x] 3.1 整理需要进入 verification 的证据与检查点：smoke test 输出文件、diff 对比结果、CLI 退出码
- [x] 3.2 标记需要进入 writeback 的摘要与状态变更：AGENTS.md 引擎概览表（如目录结构描述需更新）、README.md 能力描述（新增独立操作能力）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标
