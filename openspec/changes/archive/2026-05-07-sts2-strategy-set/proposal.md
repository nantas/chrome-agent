# Proposal

## 问题定义

Change 1 已将 `scripts/mediawiki-api-extract` 重构为策略组合架构，冻结了 5 个策略接口（DiscoveryStrategy、ContentAcquisitionStrategy、LinkResolver、TemplateProcessor、ListPageAssembler）和默认实现。但默认实现基于 balatro（最简单的 MediaWiki 场景），无法处理 slaythespire.wiki.gg (ns=3000) 的复杂结构，导致首次 StS2 爬取产生 13 个问题：

1. **链接断裂** (6000+)：wiki 内链使用短名（`[[Bash]]` 而非 `[[Slay the Spire 2:Bash]]`），默认 `ExactTitleLinkResolver` 无法解析
2. **括号目标断裂** (~200)：贪婪正则 `[text](path)` 无法处理 `Strike (Ironclad)` 等含括号的链接目标
3. **路径计算错误**：`ExactTitleLinkResolver` 忽略 `source_dir` 偏移，跨目录链接全部错误
4. **动态内容缺失**：`WikitextOnlyAcquisitionStrategy` 只获取 `prop=wikitext`，对 `#invoke`/`#dpl` 生成的内容和 DRUID infobox 图片完全不可见
5. **模板残留** (~690 页)：`SimpleSubstitutionTemplateProcessor` 只支持无参数模板，StS2 的多参数结构化模板无法展开
6. **发现策略局限**：`AllPagesDiscoveryStrategy` 使用 `list=allpages`，对 wiki.gg 的分类结构不如 `categorymembers` 精确
7. **列表页内容缺失**：4 个列表页（Cards/Relics/Potions/Events）的 DPL 表格数据为空
8. **无质量门控**：管线只有"提取 → 输出"单向流程，无内置验证，所有质量问题需要外部后处理脚本发现和修复

根因：默认策略实现假设了"wikitext 自包含所有内容"、"wiki 内链使用完整标题"、"单 namespace 封闭发现"，这些假设全部与 StS2 实际结构冲突。

## 范围边界

### 范围内（Change 2）

- **新增策略实现**：
  - `CategoryMembersDiscoveryStrategy`：基于 `action=query&list=categorymembers` 的发现，支持自定义 namespace，同时发现 ns=0（StS1）和 ns=3000（StS2）
  - `HybridAcquisitionStrategy`：检测 wikitext 中的 `#invoke`/`#dpl` 语法，自动补充获取 `prop=text`（渲染后 HTML）和 `prop=images`（图片信息）
  - `ShortNameLinkResolver`：短名索引（`title.split(':')[-1]`）+ 平衡括号解析器 + `os.path.relpath` 相对路径 + 跨 namespace 解析
  - `StructuredTemplateProcessor`：多参数模板展开（支持位置参数和命名参数）、Lua 模块感知
  - `HybridListPageAssembler`：优先从渲染后 HTML 提取实际表格结构，frontmatter 驱动作为 fallback
- **L6 验证质量层**（新增）：
  - `validate_links()`：扫描所有输出 `.md`，检测 `[text](path)` 中的 `path` 是否实际存在
  - `validate_content_integrity()`：检测输出文件是否为空或仅含 frontmatter
  - `validate_images()`：提取所有 `![alt](url)`，批量查询 `action=query&prop=imageinfo&titles=File:...`
- **目录结构重构**：
  - 输出按 namespace 分层：`StS2/` / `StS1/` 作为顶层目录
  - 文件名剥离 namespace 前缀：`Slay the Spire 2:Bash` → `StS2/Cards/Bash.md`
- **策略文件更新**：
  - `sites/strategies/slaythespire.wiki.gg/strategy.md`：配置 `content_profile` 使用新策略集，扩展 `template_map`
- **Spec 更新**：
  - `mediawiki-api-extraction/spec.md`：追加新策略 ID 到可用 ID 表格、新增 StS2-specific scenario
  - `mediawiki-site-strategy/spec.md`：更新 `content_profile` 可用 ID 表格

### 范围外（Change 2 不涉及）

- 不修改 Change 1 冻结的策略接口签名（Protocol 定义不变）
- 不修改 balatro 路径的默认行为（balatro 仍使用默认策略，回归验证必须 pass）
- 不新增引擎或 CLI 命令（只扩展现有 `python -m scripts.mediawiki-api-extract`）
- 不改动 Scrapling 管线或 crawl/routing 逻辑
- 不实现 Change 3 的 `ContentProfileDetector` 自动探测

## Capabilities

### New Capabilities

（无新增独立 capability——L6 验证层作为 `mediawiki-api-extraction` 的内置扩展）

### Modified Capabilities

- `mediawiki-api-extraction`: 扩展策略集——新增 5 个策略实现 ID（`category_members`, `hybrid_wikitext_plus_rendered`, `short_name_with_cross_namespace`, `structured_with_lua_fallback`, `hybrid_frontmatter_and_rendered`），新增 L6 验证层（链接完整性扫描、内容完整性检查、图片可用性验证），新增跨 namespace 发现与输出场景，新增动态内容检测场景
- `mediawiki-site-strategy`: 扩展 `content_profile` schema——更新可用策略 ID 表格，追加 StS2 策略集引用

## Capabilities 待确认项

- [x] 能力清单已确认——本次修改两个既有 capability，无新增

## Impact

| 组件 | 影响 | 风险 |
|------|------|------|
| `scripts/mediawiki-api-extract/strategies.py` | 追加 5 个新策略实现类 | 中——新增代码需充分测试，但与默认路径隔离 |
| `scripts/mediawiki-api-extract/pipeline.py` | 更新 `build_pipeline()` 支持新策略 ID，追加 L6 验证入口 | 低——默认行为不变，StS2 才触发新路径 |
| `scripts/mediawiki-api-extract/phase_a.py` | 支持跨 namespace 发现（ns=0 + ns=3000） | 中——分类发现和目录映射逻辑变化 |
| `scripts/mediawiki-api-extract/phase_c.py` | 支持 `--validate` flag，L6 验证集成 | 低——可选行为，不影响默认输出 |
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | 配置 `content_profile` + 扩展 `template_map` | 低——策略文件变更 |
| `openspec/specs/mediawiki-api-extraction/spec.md` | 追加策略 ID、scenario、L6 契约 | 低——spec 追加 |
| `openspec/specs/mediawiki-site-strategy/spec.md` | 更新 `content_profile` 可用 ID | 低——spec 追加 |
| balatro 爬取输出 | 无影响——默认策略不变 | 最低——需回归验证 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://chrome-agent/openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED
  - `repo://chrome-agent/openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED
  - `repo://chrome-agent/scripts/mediawiki-api-extract/` — MODIFIED
  - `repo://chrome-agent/sites/strategies/slaythespire.wiki.gg/strategy.md` — MODIFIED
  - `repo://chrome-agent/AGENTS.md` — MODIFIED
  - 项目页面：`repo://my-wiki/docs/design/chrome-agent-mediawiki-extraction-improvement-plan.md`
