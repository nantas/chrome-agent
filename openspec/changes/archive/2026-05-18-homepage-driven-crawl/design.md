# Design

## Context

用户通过 chrome-agent 爬取 wiki.gg 站点（Binding of Isaac Rebirth Wiki）时，面临管线缺陷和策略缺口。当前 pipeline（Phase A 全量发现 → Phase B 提取 → Phase C 组装）无法支持"按首页分类体系有界爬取"的用户需求。用户不得不编写 ~600 行后处理脚本来填补页面分配、链接修复和索引生成等缺口。

本 change 通过三层推进解决：底层 bugfix + 管线扩展 + CLI 命令集成。

## Goals / Non-Goals

**Goals:**
- 修复 `standalone.py` 和 `explore/main.py` 的 MediaWiki 重定向处理（P-1）
- 修复 `HtmlToMarkdownConverter._to_markdown_link` 的 URL 编码解码（P-3）
- 新增策略 schema 字段 `api.homepage`，支持首页分类结构定义
- 新增管线 Phase 0：首页解析 → 分类发现 → 页面分配
- 集成 `--phase homepage` CLI 选项，跳过 Phase A 走首页入口
- 新增 `--resume` 断点续传支持
- Pipeline 结束时自动调用 `fix_links_in_dir`
- 回填 BOI 站点策略的 `api.homepage` 配置

**Non-Goals:**
- 包名重构（`mediawiki-api-extract` → `mediawiki_api_extract`）
- 通用 wiki.gg 首页选择器泛化（先 BOI 验证，后续 change 处理模板）
- `link_fixer.py` 修改（已正确使用 `unquote()`）
- Phase A（allpages）功能修改

## Decisions

### D1: Phase 0 作为独立模块，不嵌入 Phase A

**Decision**: 新增 `pipeline/phase_0.py`（编排）、`pipeline/homepage_parser.py`（首页解析）、`pipeline/page_assigner.py`（页面分配），通过 `orchestrate.py` 的 phase dispatch 集成。

**Rationale**: Phase 0 的发现逻辑（首页选择器 → 分类链接 → 分类型发现 → 页面分配）与 Phase A 的 allpages 全量发现正交。保持独立模块避免 Phase A 膨胀，也便于后续独立测试和复用。

**Alternatives considered**: 将 homepage 逻辑嵌入 Phase A 作为 `discovery_strategy` 的新实现。拒绝原因：Phase A 的 discovery 接口是 `discover_pages(client, strategy)`，而 homepage 需要额外的 homepage 解析和选择器匹配步骤，接口不兼容。

### D2: 页面分配使用优先级链而非加权评分

**Decision**: 优先级链（manual override > category_page_member > MW category tag match by priority order）而非加权评分。

**Rationale**: 用户报告中的实际需求是确定性归属（"Bosses 优先级高于 Basement bosses"），而非模糊匹配。优先级链简单、可预测、可调试。策略文件中的 `assignment_priority` 列表即为优先级声明。

### D3: `--resume` 默认开启

**Decision**: `--resume` 默认启用，`--no-resume` 显式关闭。

**Rationale**: 100 分钟的爬取中因中断而全量重来是用户报告中的核心痛点（P-5）。default-on 降低意外中断的代价。`--no-resume` 提供干净的退出路径。

### D4: `fix_links_in_dir` 在 pipeline 结束时自动触发

**Decision**: Phase C 完成后（或仅 Phase B 完成后）自动调用 `fix_links_in_dir`，无需 CLI 额外步骤。

**Rationale**: 用户报告中的步骤 4（链接修复 pass）是 pipeline 输出质量的必要步骤。自动集成消除了"忘记运行 fix-links"的人为错误。link fix 失败不阻断 pipeline（logged as warning）。

### D5: 新模块位置与命名

**Decision**: 
- `pipeline/phase_0.py`: Phase 0 编排逻辑
- `pipeline/homepage_parser.py`: 首页 HTML 解析 + 分类链接提取
- `pipeline/page_assigner.py`: 页面→目录分配算法

**Rationale**: 放在 `pipeline/` 子包下与现有 Phase A/B/C 保持一致。文件名使用 `snake_case` 与 Python 项目规范一致。

## Risks / Migration

### Risk 1: 首页选择器跨站点不稳定

**Mitigation**: 选择器通过策略文件配置（`api.homepage.category_sections[].selector`），而非硬编码。不同站点可以配置不同选择器。先在 BOI 站点验证 `.gallerytext a` 选择器，后续 change 泛化到模板。

### Risk 2: Phase 0 的 API 调用量

**Mitigation**: 18 个分类（BOI 案例）约 20 次 API 调用。`assignment_priority` 配置支持限制实际处理的分类数量。最坏情况（100+ 分类）用户可仍使用 Phase A 全量发现。

### Risk 3: `--resume` 状态文件与数据一致性

**Mitigation**: 状态文件写入 `completed_pages` 使用原子写入（write to temp → rename）。Phase B 在写输出文件后才标记页面为 completed。输出文件存在性作为 completed 状态的辅助验证。

### Risk 4: `api.homepage` 策略向后兼容

**Mitigation**: `api.homepage` 为可选字段。无此块的策略行为完全不变。`--phase homepage` 仅在此块存在时可用。

### Migration Path

1. 现有策略文件无需修改（`api.homepage` 可选）
2. 需要首页驱动爬取的站点添加 `api.homepage` 配置
3. `--phase homepage` 是新 option，不影响默认 `all` 行为
4. Bugfix（P-1, P-3）对所有站点透明生效
