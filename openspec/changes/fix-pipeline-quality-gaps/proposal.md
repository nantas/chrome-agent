# Proposal

## 问题定义

对 `bindingofisaacrebirth.wiki.gg` 的全站爬取暴露了 MediaWiki API 提取管线的系统性质量缺口。handoff 文档记录了 4 类 Issue，且用户在 chrome-agent 仓库与外部仓库之间反复调试三个来回仍未解决。

根因分析发现以下结构性缺陷：

1. **Phase 命名混乱与调度失效**：Phase A（allpages 发现）与 Phase 0（homepage 发现）本质是同一 Discovery 阶段的两种互斥策略，却被命名为不同 phase。`orchestrate.py` 的自动检测逻辑因 CLI 默认值 `["all"]` 为 truthy 而永远不触发，导致定义了 `api.homepage` 的策略仍然走 Phase A 全量发现。

2. **Phase 0 功能缺口**：首页驱动发现不将分类页面（Items、Bosses 等）本身加入 manifest，导致这些页面不被提取。`list_page_content` 缺失使 Phase C 只能生成裸链接列表而非有内容的分类索引页。

3. **HTML→Markdown 转换器双路径分裂**：explore 样本验证使用 `sample_converter.py`（BeautifulSoup + markdownify），实际爬取使用 `html_to_markdown.py`（selectolax + 自定义渲染器）。两个转换器零代码共享，前者正确组装 Markdown infobox 表格，后者输出破碎的孤立表格行。Architecture Gate 只校验前者，后者处于盲区。

4. **策略 schema 歧义**：`api.homepage.exclude_categories` 仅在 Phase 0 生效，`api.content_profile.discovery_strategy: "allpages"` 实际控制行为，两者并存产生矛盾。`page_categories` 映射不完整导致 337 页落入根目录。

## 范围边界

**范围内：**
- 统一 Phase A/0 为 Discovery 阶段的两种策略实现，通过 `--discovery` CLI 参数选择
- 修复 Phase 0：分类页面入 manifest、填充 list_page_content
- 修复 `html_to_markdown.py`：infobox 表格正确组装、读取 `extraction.infox.*` 配置
- 修复 orchestrator 自动检测：策略有 `api.homepage` 时默认走 homepage 策略
- 扩展 Architecture Gate 校验范围到 `html_to_markdown.py`
- 清理死代码 `_pipeline_legacy.py`、`_strategies_legacy.py`
- 策略 schema 修正：`exclude_categories` 提升层级
- 补全 BOI 策略的 `page_categories` 映射

**范围外：**
- 不统一 `sample_converter.py` 与 `html_to_markdown.py` 为单一转换器（评估为后续 change）
- 不修改 Phase B/C 的核心逻辑
- 不新增 discovery 策略类型
- 不修改 `link_fixer.py` 或 `page_assigner.py` 的核心逻辑

## Capabilities

### New Capabilities

- `discovery-phase-unification`: 将 Phase A 与 Phase 0 统一为 Discovery 阶段的两种可切换策略实现（allpages / homepage），通过 `--discovery` CLI 参数和 orchestrator 自动检测选择
- `homepage-discovery-category-extraction`: Phase 0（homepage 发现）将分类页面本身纳入 manifest，填充 list_page_content，确保分类页被 Phase B 提取且 Phase C 能生成有内容的 index.md

### Modified Capabilities

- `homepage-driven-discovery`: Phase 0 补充分类页面 manifest 入列逻辑、list_page_content 获取；新增 `include_category_pages` manifest 字段
- `mediawiki-api-extraction-pipeline`: orchestrator 统一 discovery phase dispatch，修复 `api.homepage` 自动检测逻辑；Phase 内部命名统一（不再使用 Phase 0 作为对外名称）
- `pipeline-converters`: `html_to_markdown.py` 修复 infobox 表格渲染（组装完整 Markdown 表格含分隔行）、读取 `extraction.infox.*` 配置、增加空值防御
- `explore-architecture-gate`: 校验范围从仅 `sample_converter.py` 扩展到同时校验 `html_to_markdown.py`
- `pipeline-strategy-schema`: `exclude_categories` 从 `api.homepage` 提升到 `api` 顶层（同时保留 `api.homepage` 中的同名字段为别名）；明确 `discovery_strategy` 与 `api.homepage` 的关系
- `pipeline-cli-entry`: `--phase` 参数重构，新增 `--discovery` 参数（`auto`|`allpages`|`homepage`），`--phase` 仅保留 `extract`|`assemble`|`all`（与 discovery 正交）

## Capabilities 待确认项

- [x] 能力清单已与用户确认：explore 阶段已详细讨论所有缺口与修正方向，用户确认推进

## Impact

| 影响维度 | 详情 |
|---------|------|
| CLI 接口 | `--phase homepage` 废弃（改为 `--discovery homepage`），`--phase` 保留 `extract`/`assemble`/`all` |
| 策略 schema | `api.homepage.exclude_categories` 提升到 `api.exclude_categories`（`api.homepage.exclude_categories` 保留为别名向后兼容） |
| 行为变更 | 策略含 `api.homepage` 时默认走 homepage 发现（原默认走 allpages） |
| 文件变更 | 删除 `_pipeline_legacy.py`、`_strategies_legacy.py`；修改 6 个 pipeline 文件 + 1 个 explore 文件 + 1 个策略文件 |
| 向后兼容 | `--phase all` 继续可用（等价于 `--discovery auto`）；`--phase homepage` 废弃但有 warning 降级 |
| 验证目标 | `bindingofisaacrebirth.wiki.gg` 全站爬取：infobox 表格有效、分类页有内容 index.md、exclude_categories 生效、无页面落根目录 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：
  - `openspec/specs/homepage-driven-discovery/spec.md`
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md`
  - `openspec/specs/pipeline-converters/spec.md`
  - `openspec/specs/explore-architecture-gate/spec.md`
  - `openspec/specs/pipeline-strategy-schema/spec.md`
  - `openspec/specs/page-assignment/spec.md`
  - `openspec/specs/pipeline-cli-entry/spec.md`
- 已确认项目页：
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
