# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认所有 5 个 spec delta 的实现范围：`api-error-semantics`（3 requirements modified/added）、`homepage-driven-discovery`（4 added）、`pipeline-strategy-schema`（3 added）、`pipeline-cli-entry`（2 added）、`page-assignment`（1 added）
- [x] 1.2 确认依赖前置条件：无外部依赖，所有修改限于 `scripts/mediawiki-api-extract/` 和策略文件

## 2. 核心实现任务

### 2.1 P-line：统一异常处理

- [x] 2.1.1 `strategies/discovery.py:128,257` — `except RuntimeError` → `except Exception`（`AllPagesDiscoveryStrategy.fetch_list_pages` + `CategoryMembersDiscoveryStrategy.fetch_list_pages`）
  - **Spec**: `api-error-semantics` → Requirement "策略层对 PageNotFoundError 的优雅处理"
  - **验证**: 模拟 missingtitle 场景，确认 log.warning 输出，流程继续
- [x] 2.1.2 `strategies/acquisition.py:45,51,74,81` — `except RuntimeError` → `except Exception`（`HtmlRenderedAcquisitionStrategy` + `HybridAcquisitionStrategy` 的各处异常捕获）
  - **Spec**: `api-error-semantics` → Requirement "策略层对 PageNotFoundError 的优雅处理"
  - **验证**: 模拟 missingtitle 页面，确认返回含 `wikitext: None` 的结果而非异常传播
- [x] 2.1.3 `_strategies_legacy.py:216,847,878,885,1429,1437` — `except RuntimeError` → `except Exception`（6 处）
  - **Spec**: `api-error-semantics` → Requirement "策略层对 PageNotFoundError 的优雅处理"
  - **验证**: 与 discovery.py 相同模式，确认无语法错误

### 2.2 P-line：Phase A 防御性保护

- [x] 2.2.1 `pipeline/phase_a.py:65` — 包裹 `discovery_strategy.fetch_list_pages()` 于 `try/except Exception`，失败时 `list_page_content = {}`
  - **Spec**: `api-error-semantics` → Requirement "Phase A 对 fetch_list_pages 的防御性保护"
  - **验证**: 提供含 Modes/Objects 的 `list_pages`，确认 Phase A 完成不返回 EXIT_PHASE_A_FAILURE

### 2.3 S-line：策略 Schema 扩展（代码侧）

- [x] 2.3.1 `pipeline/phase_0.py` — `run_phase_0()` 在 `parse_homepage()` 后、`_discover_category_pages()` 前，新增排除过滤逻辑
  - 读取合并后的 `exclude_categories` 列表（由 orchestrator 传入）
  - 过滤 `categories` 列表，排除匹配的分类
  - 未匹配的排除名输出 `log.info("Exclude category 'X' not found ...")`
  - **Spec**: `homepage-driven-discovery` → Requirement "category-exclusion-filtering"
  - **验证**: 用 BOI 策略 + `exclude_categories=["Music"]`，确认 Music 分类不出现在 manifest

### 2.4 P-line：CLI 参数新增

- [x] 2.4.1 `cli.py:_add_pipeline_args()` — 新增 `--exclude-category` 参数（`action="append", default=None`）
  - **Spec**: `pipeline-cli-entry` → Requirement "exclude-category-cli-parameter"
  - **验证**: 多次传参，确认 `args.exclude_category` 为列表

### 2.5 P-line：Orchestrator 合并逻辑

- [x] 2.5.1 `pipeline/orchestrate.py:run_pipeline()` — 在 Phase 0 执行前，合并策略 `exclude_categories` 和 CLI `exclude_category` 为并集
  - 日志输出 `"Excluded categories: <list> (source: strategy=<n>, cli=<m>)"`
  - 合并后的列表传递给 `run_phase_0()`
  - **Spec**: `pipeline-cli-entry` → Requirement "exclude-category-merge-logic"
  - **验证**: 策略排除 2 项 + CLI 排除 3 项（含重复），确认合并后去重

### 2.6 S-line：策略文件数据修正

- [x] 2.6.1 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — `taxonomy.list_pages` 移除 `"Modes": "Modes"` 和 `"Objects": "Objects"`
  - **验证**: `grep` 确认这两个条目不再存在于策略文件
- [x] 2.6.2 同一策略文件 — `api.homepage` 下新增 `exclude_categories: ["Music", "Modding", "Version History"]`
  - **Spec**: `pipeline-strategy-schema` → Requirement "homepage-exclude-categories-field"
  - **验证**: `yq` 解析策略 frontmatter 确认新字段存在

## 3. 收敛与验证准备

- [x] 3.1 集成验证：BOI 站点全流程爬取
  - `chrome-agent crawl https://bindingofisaacrebirth.wiki.gg --strategy ... --output ...`
  - 验证 exit code 非 11（非 EXIT_PHASE_A_FAILURE）
  - 验证 Music、Modding、Version History 目录不存在
  - 验证日志含排除分类信息
- [x] 3.2 边界测试：无排除配置时行为不变（向后兼容）
- [x] 3.3 边界测试：排除不存在的分类名不阻断流程

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
