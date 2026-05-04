# Design

## Context

chrome-agent 当前所有引擎都基于"渲染页面→提取内容"范式。在对 MediaWiki 游戏 wiki 进行批量结构化爬取时，Scrapling 输出包含大量视觉噪音和模板噪音，需要多轮不确定的后处理清洗。

MediaWiki 的 `action=parse&prop=wikitext` API 可以直接获取模板展开后的 wikitext（平均 5KB vs Scrapling MD 的 54KB），无视觉噪音，wiki 链接已结构化。这为确定性转换提供了可能性。

本设计定义如何在不破坏现有引擎体系的前提下，将 API 路径集成到 chrome-agent 的 `crawl` 命令中。

## Goals / Non-Goals

**Goals:**
- 为声明了 `api.platform: mediawiki` 的策略文件启用 API-first 的 crawl 路径
- 输出 Markdown 质量达到 Scrapling 路径经过 3-4 轮后处理后的水平，且为一次性确定性转换
- API 路径失败时自动 fallback 到 Scrapling，不阻断 crawl 执行
- 现有策略文件向后兼容（不声明 `api` 字段的策略行为不变）

**Non-Goals:**
- 不创建新的引擎类型或修改 `engine-registry.json`
- 不支持 `action=parse&prop=text`（API HTML）路径——该路径仍有 DOM 解析复杂性
- 不支持 MediaWiki 以外的 CMS 平台（但 `api.platform` 字段预留扩展点）
- 不修改 `fetch` 和 `scrape` 命令的行为
- 不替换 `clean-mediawiki.sh`——继续作为 Scrapling fallback 路径的清洗工具

## Decisions

### Decision 1: 集成点为 `crawl` 命令，而非新命令

**选择**：在 `crawl` 命令的路由逻辑中增加 API 检查分支。

**理由**：
- `crawl` 已是策略引导的有界遍历命令，策略文件是其天然锚点
- `fetch` 是单页轻量获取，不需要完整管线
- `scrape` 是策略无关的自发现遍历，没有策略文件就无从判断 API 可用性
- 新增独立命令（如 `extract-mediawiki`）会增加命令面复杂度，且与 `crawl` 的遍历+组织能力重复

**替代方案已排除**：新增 `chrome-agent extract` 命令。原因：与 `crawl` 的 Phase C（目录组织+链接修正）大面积重叠，且增加用户认知负担（"我该用 crawl 还是 extract？"）。

### Decision 2: 仅使用 wikitext 路径，放弃 API HTML 路径

**选择**：Phase B 使用 `action=parse&prop=wikitext`，不使用 `action=parse&prop=text`（HTML）。

**理由**（基于实际样本证据）：
- Wikitext 大小：5KB（模板展开后）
- API HTML 大小：157KB（含深层嵌套 DOM、HTML 实体编码 `&#95;&#95;`）
- Wikitext 无视觉噪音（无 `<div class="tilt-box-wrap">` 重复图片、无 `[edit]` 链接）
- Wiki 链接 `[[Page|text]]` 可直接转换，无需 `<a href>` 正则匹配
- Infobox 模板参数 `{{Joker info|effect=...|rarity=...}}` 可直接提取为 YAML frontmatter

**替代方案已排除**：wikitext + HTML 双路径。原因：HTML 路径引入 DOM 解析器依赖（html.parser 状态机），增加了与 wikitext 路径不共享的复杂性，而 balatro 爬取经验表明 HTML 路径的价值被 wikitext 完全覆盖。

### Decision 3: 管线实现为独立 Python CLI 工具

**选择**：实现为 `scripts/mediawiki-api-extract`（Python CLI），而非嵌入 chrome-agent 主进程。

**理由**：
- 管线有独立的依赖需求（`requests`、并发控制、JSON 解析），不适合嵌入 shell 脚本
- 与现有 `scripts/` 目录的定位一致（`clean-mediawiki.sh`、`extract-links.py` 等辅助工具）
- 可被 `crawl` 命令以子进程方式调用，保持 CLI 面的简洁
- balatro-wiki-converter 的 Python 工具链（`fetch_pages.py`、`organize.py`、`html2md.py`）提供了可提炼的实现参考

**命令接口**：
```
mediawiki-api-extract <url> --strategy <path> --output <dir> [--concurrency N] [--phase A|B|C|all]
```

### Decision 4: Fallback 策略为 phase-granular

**选择**：每个 phase 失败时可独立触发 fallback，而非全量失败后才 fallback。

- Phase A 失败（API unreachable）→ 整体 fallback 到 Scrapling crawl
- Phase B 失败率 > 50% → 整体 fallback
- Phase B 个别页面失败 → 继续处理剩余页面，标记 partial_success
- Phase C 失败（本地文件操作）→ 报告错误，不丢失已提取内容

**理由**：API 的典型故障模式是端点不可用或限流，而非间歇性失败。如果 API 可达，大部分页面应该成功。Phase B 个别失败通常是页面本身问题（已删除、受保护），不应阻断整体流程。

### Decision 5: 链接修正使用 manifest-based 全量映射

**选择**：Phase A 生成完整的 `page_manifest.json`（page_title → target_directory → target_filename），Phase C 使用该 manifest 做全量链接重写。

**理由**：
- 正向映射（已知所有页面的位置）比反向正则（在每个文件中猜测链接目标位置）更可靠
- balatro 爬取的链接路径断裂问题正是因为 organize.py 没有使用全量 manifest 做链接修正
- 全量映射避免了跨目录链接的边界情况（同名文件在不同目录、index.md 的目标目录等）

**算法概要**：
```
for each .md file:
    for each [text](target.md) link:
        lookup target in manifest
        if target_dir != source_dir:
            rewrite to [text](<relative_path_to_target_dir>/target.md)
```

### Decision 6: 策略 schema 扩展为 add-only，向后兼容

**选择**：在 `site-strategy-schema` 中新增可选的 `api` 字段，不修改任何现有字段。

**理由**：
- 现有策略文件不声明 `api` 字段 → 行为完全不变
- 新增 `api` 字段的策略文件 → 仅在 `crawl` 时触发新路径
- registry.json 的 schema 同步扩展 `api` 相关字段，但不强制现有条目更新

### Decision 7: DPL 表格用数据驱动还原，不解析 DPL 语法

**选择**：`<dpl>...</dpl>` 块不被解析为 DPL 查询语义，而是被替换为从 Phase B frontmatter 数据组装的 Markdown 汇总表格。

**理由**：
- DPL 是 MediaWiki 扩展的声明式查询语言，完整解析成本高且不同版本语法差异大
- 管线已在 Phase B 提取了每个页面的 `frontmatter_fields`，这些正是 DPL 表格的列数据
- Phase A manifest 已记录了每个页面的分类归属，可以精确匹配 "哪些页面属于这个列表页的分类"
- 数据驱动方式（manifest + frontmatter → table）比解析 DPL 语法更可靠、更通用
- DPL 查询语义可从 strategy 的 `taxonomy` + `output.frontmatter_fields` 推导，无需解析原始 DPL 代码

**算法概要**：
```
for each list page containing <dpl>:
    target_dir = taxonomy.list_pages[page_title]
    pages_in_dir = [p for p in manifest if p.target_directory == target_dir]
    columns = ["Joker"] + frontmatter_fields  # title link + data columns
    for page in pages_in_dir:
        row = [link_to(page)] + [phase_b_frontmatter[page.title].get(f) for f in frontmatter_fields]
    replace <dpl>...</dpl> with assembled Markdown table
```

### Decision 8: HTML 注释作为噪音过滤，不保留

**选择**：`<!-- ... -->` HTML 注释在 Phase B wikitext 转换时整块移除。

**理由**：
- MediaWiki 的 HTML 注释是编辑者之间的协作备注（如 DPL 配置说明、编辑提示），不是面向读者的内容
- 在 Scrapling 路径中，HTML 注释不会出现在渲染后的 DOM 中
- 保留注释会在 Markdown 输出中暴露编辑噪音，违反「无 wikitext artifacts」的输出格式契约

## Risks / Migration

### Risk 1: API 端点探测开销

**风险**：对每个未知的 MediaWiki 站点，Phase A 前的端点探测需要 3 次 HTTP 请求（api.php, w/api.php, strategy-specified base_url）。

**缓解**：
- 探测结果缓存在 crawl run 期间（每个 run 只探测一次）
- 如果策略文件已指定 `api.base_url` 且验证通过，跳过其他候选
- 如果策略文件已验证过（在之前的 run 中成功），默认跳过探测（通过 `--no-api-probe` 标志）

### Risk 2: Wikitext 模板展开不完整

**风险**：`action=parse&prop=wikitext` 可能无法展开所有模板（例如 Lua/Scribunto 模块生成的动态内容）。

**缓解**：
- 残留的 `{{...}}` 调用在输出中保留为文本，并记录 warning
- 策略文件的 `api.output.template_map` 可以为已知模板提供 fallback 展开规则
- Scribunto 模块通常用于数据查询而非格式渲染，影响范围有限

### Risk 3: API rate limiting 差异

**风险**：不同 MediaWiki 实例的 rate limit 策略不同（balatro 无限制，其他站点可能有严格限制）。

**缓解**：
- 默认 concurrency=5（balatro 经验表明 5 并发完全安全）
- 指数退避 + jitter 重试（1s, 2s, 4s, max 3 retries）
- 如果持续遇到 429，自动降低 concurrency 并记录 recommendation

### Risk 4: registry.json 条目缺失

**风险**：balatrowiki.org 策略文件已存在但 registry.json 中缺少对应条目。这是治理漏洞，可能在 agent 查询 registry 时漏掉该站点。

**缓解**：
- 本次 change 的 writeback 目标包含 registry.json 修复
- 后续可通过 `doctor` 命令增加 registry 一致性检查

### Migration: 现有 MediaWiki 策略文件

**迁移步骤**（在 tasks.md 中细化）：
1. 为 `balatrowiki.org/strategy.md` 添加 `api` 字段（基于 `action=parse` 验证）
2. 为 `vampire.survivors.wiki/strategy.md` 添加 `api` 字段
3. `registry.json` 补充 balatrowiki.org 条目 + 增加 `backend` 字段
4. 现有策略的 Scrapling 路径行为不变
