# Proposal

## 问题定义

用户通过 chrome-agent 对 `bindingofisaacrebirth.wiki.gg` 执行首页驱动的全站爬取时，遭遇管线阻塞（exit code 11, EXIT_PHASE_A_FAILURE）。根因分析揭示三层问题：

1. **P-line 异常处理不统一**：`client.py` 按 `api-error-semantics` spec 定义了 `PageNotFoundError(Exception)`（不继承 `RuntimeError`），但 discovery 策略层（`discovery.py`、`acquisition.py`、`_strategies_legacy.py`）的 `fetch_list_pages()` 和 `fetch_page_content()` 使用 `except RuntimeError`，无法捕获 `PageNotFoundError`，导致本应降级为 warning 的 missingtitle 错误直接向上传播，终止 pipeline。

2. **S-line 策略数据错误**：`taxonomy.list_pages` 包含 "Modes" 和 "Objects"，但它们在 wiki 上不存在为 ns=0 普通页面（返回 missingtitle）。策略的 `category_page_types` 已正确声明它们为 category_page，但 `list_pages` 未同步修正，且 Phase A 的 `fetch_list_pages()` 不检查 `category_page_types`。

3. **S-line + W-line 分类排除缺口**：策略 `api.homepage.categories` 罗列了首页全部 19 个分类，但无机制让用户指定排除特定分类（如 Music、Modding、Version History）。用户 prompt 中的 "排除首页链接里的 xx" 无法通过策略字段或 CLI 参数表达。

## 范围边界

**范围内：**
- 统一 discovery 和 acquisition 策略层的异常处理（`except RuntimeError` → `except Exception`），覆盖 `discovery.py`、`acquisition.py`、`_strategies_legacy.py` 共 12 处
- Phase A 的 `fetch_list_pages()` 增加防御性 try/except
- 策略 schema 新增 `api.homepage.exclude_categories` 字段
- Phase 0 集成 exclude_categories 过滤逻辑
- CLI 新增 `--exclude-category` 参数（repeatable），与策略字段合并取并集
- 策略文件修正：`taxonomy.list_pages` 移除 Modes/Objects

**范围外：**
- `PageNotFoundError` 的类层次重构（保持 `Exception` 基类不变）
- Phase A 的全量发现逻辑变更（仅修复异常处理和防御性保护）
- Phase B/C 的修改（已有正确的异常处理）
- 新的 discovery 策略类型

## Capabilities

### Modified Capabilities

- `api-error-semantics`: 扩展异常处理范围，要求 discovery/acquisition 策略层的 `fetch_list_pages()` 和 `fetch_page_content()` 使用 `except Exception` 捕获 `PageNotFoundError`，Phase A 的 `fetch_list_pages()` 调用点增加防御性 try/except。

- `homepage-driven-discovery`: 新增分类排除过滤能力——Phase 0 的 `run_phase_0()` 在 `parse_homepage()` 完成后、`_discover_category_pages()` 调用前，按 `exclude_categories` 列表过滤分类。

- `pipeline-strategy-schema`: `api.homepage` 下新增可选字段 `exclude_categories: list[str]`，定义需排除的分类名称列表。

- `pipeline-cli-entry`: 新增 `--exclude-category` 参数（`action=append`，repeatable），与策略 `exclude_categories` 合并取并集，CLI 覆盖策略文件的单方面偏好，两者互补不互斥。

- `page-assignment`: 排除的分类不进入发现流程，因此不参与页面分配（assigner 无需内部修改，排除在源头完成）。

## Capabilities 待确认项

- [x] 能力清单已与用户确认：5 个 modified capabilities，按 P-line→S-line→CLI 顺序推进

## Impact

- **代码变更**: 6 文件修改（`discovery.py`、`acquisition.py`、`_strategies_legacy.py`、`phase_a.py`、`phase_0.py`、`orchestrate.py`），1 文件新增参数（`cli.py`），1 策略文件数据修正
- **向后兼容**: `api.homepage.exclude_categories` 为可选字段，缺失时行为不变（不过滤任何分类）。`--exclude-category` 为可选参数。异常处理变更仅影响 missingtitle/nosuchpage 场景，原 `RuntimeError` 路径行为保持不变。
- **破坏性变更**: 无

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`api-error-semantics`、`homepage-driven-discovery`、`pipeline-strategy-schema`、`pipeline-cli-entry`、`page-assignment`
  - 项目页：`repo://my-wiki:docs/workflow-experience/binding-of-isaac-wiki-crawl.md`
  - 回写目标：上述项目页 + `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
