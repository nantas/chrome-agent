# Tasks

## 1. 基线建立与准备

- [x] 1.1 运行当前（未修改）脚本生成 balatro 基线
      ```bash
      python scripts/mediawiki-api-extract https://balatrowiki.org/w/Jokers \
        --strategy sites/strategies/balatrowiki.org/strategy.md \
        --output /tmp/mw-baseline
      ```
- [x] 1.2 确认基线输出完整性（~467 页面，~15 个目录）
- [x] 1.3 将基线保存为回归参考（`/tmp/mw-baseline/`）

## 2. 模块拆分与文件创建

- [x] 2.1 创建 `scripts/mediawiki-api-extract/` 目录结构
      - `__init__.py` — 包标记
      - `__main__.py` — CLI 入口（`main()` + `run_pipeline()`）
      - `client.py` — `ApiClient` + `probe_api_endpoint`
      - `strategies.py` — 策略 Protocols + 默认实现 + 辅助函数
      - `phase_a.py` — Phase A 编排
      - `phase_b.py` — Phase B 编排
      - `phase_c.py` — Phase C 编排
      - `pipeline.py` — 策略组装 + 验证 + 编排

- [x] 2.2 删除原单体文件 `scripts/mediawiki-api-extract`

**验证**：`python -m scripts.mediawiki-api-extract --help` 输出正确

### 2.1 `client.py` — ApiClient 提取

- [x] 2.1.1 迁移 `ApiClient` 类（`_request`, `query`, `parse` 方法，完全不变）
- [x] 2.1.2 迁移 `probe_api_endpoint` 函数（完全不变）

### 2.2 `strategies.py` — 策略接口与默认实现

- [x] 2.2.1 定义 `DiscoveryStrategy` Protocol 和 `AllPagesDiscoveryStrategy` 实现
      - 方法：`discover_pages()`, `discover_categories()`, `classify_page()`, `fetch_list_pages()`, `required_capabilities`
      - 行为与当前 `discover_all_pages()`, `discover_categories()`, `classify_page_to_directory()`, `fetch_list_page_content()` 一致
      - **spec 覆盖**：DiscoveryStrategy interface (spec:mediawiki-api-extraction)、AllPagesDiscoveryStrategy (default)

- [x] 2.2.2 定义 `ContentAcquisitionStrategy` Protocol 和 `WikitextOnlyAcquisitionStrategy` 实现
      - 方法：`fetch_page_content()`, `required_capabilities`
      - 行为与当前 `process_single_page()` 的前半段（client.parse → 返回 wikitext）一致
      - **spec 覆盖**：ContentAcquisitionStrategy interface (spec:mediawiki-api-extraction)

- [x] 2.2.3 定义 `LinkResolver` Protocol 和 `ExactTitleLinkResolver` 实现
      - 方法：`convert_links()`, `resolve()`
      - 行为与当前 `convert_wiki_links()` 一致（含短名/括号/路径缺陷——Change 1 不修复）
      - **spec 覆盖**：LinkResolver interface (spec:mediawiki-api-extraction)

- [x] 2.2.4 定义 `TemplateProcessor` Protocol 和 `SimpleSubstitutionTemplateProcessor` 实现
      - 方法：`extract_frontmatter()`, `expand_templates()`, `remove_infobox()`, `clean_remaining_templates()`
      - 行为与当前 `extract_frontmatter()`, `expand_templates()`, `remove_infobox_templates()` + 清理逻辑一致
      - 迁移辅助函数：`_split_templates()`, `_replace_dpl_template()`
      - **spec 覆盖**：TemplateProcessor interface (spec:mediawiki-api-extraction)

- [x] 2.2.5 定义 `ListPageAssembler` Protocol 和 `FrontmatterDrivenListPageAssembler` 实现
      - 方法：`assemble_index()`
      - 行为与当前 `run_phase_c()` 中 index.md 生成逻辑一致（DPL 表格组装 + 目录索引）
      - **spec 覆盖**：ListPageAssembler interface (spec:mediawiki-api-extraction)

- [x] 2.2.6 迁移 `convert_wikitable_to_markdown` + 辅助函数到 `strategies.py`
      - `_parse_wikitable_block()`, `_split_table_cells()`, `_clean_table_cell()`
      - 保持为模块级函数（非策略）

- [x] 2.2.7 迁移 `convert_wikitext_to_markdown` 函数到 `strategies.py`
      - 改为通过函数参数接受 `link_resolver` 和 `template_processor` 对象
      - 函数签名：
        ```python
        def convert_wikitext_to_markdown(wikitext, title, source_url,
                                          manifest_pages, source_dir,
                                          frontmatter_fields, template_map,
                                          link_resolver, template_processor) -> tuple[str, list[str], dict]:
        ```

### 2.3 `phase_a.py` — Phase A 编排

- [x] 2.3.1 迁移 `run_phase_a()`，签名增加 `discovery_strategy: DiscoveryStrategy` 参数
- [x] 2.3.2 委托 `discovery_strategy.discover_pages()`, `discover_categories()`, `classify_page()`, `fetch_list_pages()` 完成核心工作
- [x] 2.3.3 保留 manifest 结构完全不变（`{pages[], list_page_content{}, ...}`）

### 2.4 `phase_b.py` — Phase B 编排

- [x] 2.4.1 迁移 `run_phase_b()`，签名增加策略对象参数
- [x] 2.4.2 迁移 `process_single_page()`，使用策略对象进行转换
      - 调用 `content_strategy.fetch_page_content()` 获取原始内容
      - 调用 `convert_wikitext_to_markdown()`（传入 `link_resolver`, `template_processor`）
- [x] 2.4.3 消除全局变量 `SOURCE_DOMAIN`，改为 `run_phase_b` 的参数传递

### 2.5 `phase_c.py` — Phase C 编排

- [x] 2.5.1 迁移 `run_phase_c()`，签名增加 `list_page_assembler` 和 `link_resolver` 参数
- [x] 2.5.2 委托 `list_page_assembler.assemble_index()` 生成 index.md
- [x] 2.5.3 保留 _index.md 生成逻辑（目前不抽象为策略）

### 2.6 `pipeline.py` — 管线编排

- [x] 2.6.1 定义 `PipelineStrategies` dataclass
      ```python
      @dataclass
      class PipelineStrategies:
          discovery: DiscoveryStrategy
          content_acquisition: ContentAcquisitionStrategy
          link_resolver: LinkResolver
          template_processor: TemplateProcessor
          list_page_assembler: ListPageAssembler
      ```
- [x] 2.6.2 实现 `build_pipeline(strategy: dict) -> PipelineStrategies`
      - 解析 `api.content_profile`（可选）
      - 根据 ID 选择策略实现（未知 ID 回退默认 + 警告日志）
      - 无 content_profile 时全部使用默认实现
      - **spec 覆盖**：Pipeline 策略注入 (spec:mediawiki-api-extraction)

- [x] 2.6.3 重构 `validate_api_config(api_config, strategies: PipelineStrategies) -> str | None`
      - 改为计算 `strategies` 中各策略 `required_capabilities` 的并集
      - 对比策略声明的 `api.capabilities`
      - 不硬编码 required 集合
      - **spec 覆盖**：Capabilities 受控词汇表验证场景 (spec:mediawiki-api-extraction)

- [x] 2.6.4 更新 `run_pipeline()` 调用序列
      ```
      strategies = build_pipeline(strategy)
      error = validate_api_config(api_config, strategies)
      manifest = run_phase_a(client, strategy, origin, strategies.discovery)
      results, stats = run_phase_b(client, manifest, strategy, concurrency, domain,
                                    strategies.content_acquisition, strategies.link_resolver, strategies.template_processor)
      phase_c_stats = run_phase_c(output_dir, manifest, results, strategy, domain,
                                   strategies.list_page_assembler, strategies.link_resolver)
      ```

### 2.7 `__main__.py` — CLI 入口

- [x] 2.7.1 迁移 `main()` 函数（argparse 配置完全不变）
- [x] 2.7.2 在 `main()` 函数内保留 `import yaml`（lazy import）
- [x] 2.7.3 调用 `run_pipeline()`（位于 `pipeline.py`）
- [x] 2.7.4 迁移所有 exit code 常量

### 2.8 `__init__.py` — 空包标记

- [x] 2.8.1 创建空文件

## 3. 策略文件更新

- [x] 3.1 可选：为 `sites/strategies/balatrowiki.org/strategy.md` 追加 `api.content_profile`（全部使用默认实现）
      ```yaml
      api:
        content_profile:
          discovery_strategy: "allpages"
          content_acquisition: "wikitext_only"
          link_resolver: "exact_title_match"
          template_processor: "simple_substitution"
          list_page_assembler: "frontmatter_driven"
      ```

## 4. 回归验证

- [x] 4.1 运行重构后脚本，输出到临时目录
      ```bash
      python -m scripts.mediawiki-api-extract https://balatrowiki.org/w/Jokers \
        --strategy sites/strategies/balatrowiki.org/strategy.md \
        --output /tmp/mw-refactored
      ```
- [x] 4.2 执行目录 diff，确认无差异
      ```bash
      diff -r /tmp/mw-baseline /tmp/mw-refactored
      ```
- [x] 4.3 如有差异，排查原因并修复

## 5. 清理与收尾

- [x] 5.1 验证 `python -m scripts.mediawiki-api-extract --help` 输出完整且正确
- [x] 5.2 清理临时基线目录 `/tmp/mw-baseline/`
- [x] 5.3 确认 `scripts/mediawiki-api-extract` 原文件已删除
