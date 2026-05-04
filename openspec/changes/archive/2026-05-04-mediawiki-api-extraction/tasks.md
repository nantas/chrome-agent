# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `mediawiki-api-extraction` spec 的管线 Phase A/B/C 行为覆盖完整
- [x] 1.2 确认 `site-strategy-schema` spec 的 `api` 字段定义与受控词汇表无冲突
- [x] 1.3 确认 `strategy-guided-crawl` spec 不需要修改（API 路由为 crawl 的内部逻辑分支，不改变 crawl 的外部契约）
- [x] 1.4 确认 `mediawiki-extraction-patterns` spec 不需要修改（API 路径不走噪声清洗，不改变噪音分类学）

## 2. 核心实现任务

### 2.1 策略 schema 扩展落地

- [x] 2.1.1 为 `balatrowiki.org/strategy.md` 添加 `api` 字段
  - 字段：`platform: mediawiki`, `base_url`, `capabilities`, `taxonomy.list_pages`, `taxonomy.category_filters`, `filename.replacements`, `output.frontmatter_fields`
  - 验证：YAML 解析无误，`api.platform` 为 `mediawiki`
  - 验证：现有字段（`domain`, `protection_level`, `structure`, `extraction`）保持不变
  - 参考：`proposal.md` 中的 `api` 字段示例 + balatro wiki 爬取经验中的 `LIST_PAGE_TO_DIR` 映射表

- [x] 2.1.2 为 `vampire.survivors.wiki/strategy.md` 添加 `api` 字段
  - 字段：`platform: mediawiki`, `base_url: "https://vampire.survivors.wiki/api.php"`, `capabilities`
  - 验证：YAML 解析无误，Crawlers 命名空间页面可被 API 发现
  - 验证：现有 Crawlers 分类结构映射到 taxonomy.list_pages

- [x] 2.1.3 修复 `sites/strategies/registry.json`
  - 新增 `balatrowiki.org` 条目（domain, description, protection_level, page_types, pagination, entry_points, anti_crawl_refs, file, backend）
  - 为 `vampire.survivors.wiki` 和 `balatrowiki.org` 条目增加 `backend: "weird-gloop-mediawiki-1.45"`
  - 验证：`jq '.entries[] | select(.domain == "balatrowiki.org")' registry.json` 返回非空结果
  - 验证：两个条目的 `backend` 字段值一致

### 2.2 CLI 工具实现

- [x] 2.2.1 创建 `scripts/mediawiki-api-extract` Python CLI 骨架
  - 入口：`#!/usr/bin/env python3`，argparse 命令行接口
  - 参数：`url`, `--strategy`, `--output`, `--concurrency` (default 5), `--phase` (A|B|C|all, default all), `--no-api-probe`
  - 验证：`--help` 输出完整，参数解析正确

- [x] 2.2.2 实现 Phase A: Page Discovery（对应 spec `Phase A — 页面发现`）
  - API 端点探测逻辑（`api.php` → `w/api.php` → strategy base_url，每候选 5s timeout）
  - `action=query&list=allpages` 页面清单获取（含 `apcontinue` 分页）
  - `action=query&prop=categories` 分类获取（50 titles/请求批处理）
  - 产出 `page_manifest.json`（page_title → target_directory → target_filename 映射）
  - 列表页内容捕获（`action=parse&prop=wikitext`，列表页集合来自 strategy `taxonomy.list_pages`）
  - 验证：对 balatrowiki.org 执行 Phase A，产出 manifest 含 ~467 页，分类映射正确
  - 验证：端点探测失败时正确 fallback 并记录错误

- [x] 2.2.3 实现 Phase B: Content Extraction（对应 spec `Phase B — 内容提取`）
  - `action=parse&prop=wikitext` 并发获取（ThreadPoolExecutor, max_workers=concurrency）
  - Infobox 模板参数提取（正则匹配 strategy `output.frontmatter_fields` 指定的参数名）
  - Wiki 链接转换：`[[Page|text]]` → `[text](Page.md)`（使用 manifest 暂存临时路径，Phase C 修正）
  - 模板展开：`{{Mult|+4}}` → `**+4 Mult**`（基于 strategy `output.template_map`）
  - 图片转换：`[[File:name.png|thumb|alt]]` → `![alt](https://{domain}/images/name.png)`
  - 过滤：`[[Category:...]]` 行移除，`[[File:...]]` → 只保留图片引用，`[[Template:...]]` → 移除
  - 指数退避重试（1s, 2s, 4s, max 3 retries），200ms 批次间延迟
  - 验证：对 balatrowiki.org 执行 Phase B，产出 467 个 `.md` 文件
  - 验证：抽查 Joker.md 含 frontmatter（effect, rarity, type, buyprice, sellprice）
  - 验证：抽查任意页面无 `{{...}}` 残留（除 unrecognized templates warning）
  - 验证：抽查任意页面无 `[[Category:...]]`、`[[File:...]]` wiki 语法残留

- [x] 2.2.4 实现 Phase C: Output Assembly（对应 spec `Phase C — 输出组装`）
  - 基于 manifest 的目录组织（page → target_directory 映射）
  - 跨目录链接修正（全量 manifest 正向映射算法）
  - Index.md 生成（合并 list page 内容 + "Pages in this category" 清单）
  - _index.md 顶层索引生成
  - 验证：对 balatro 产出执行 Phase C，`Jokers/Joker.md` 中的 `[Tarot Cards](Tarot_Cards.md)` 修正为 `[Tarot Cards](../Consumables/Tarot_Cards/index.md)`
  - 验证：Misc 占比 < 5%
  - 验证：所有 index.md 含 frontmatter + 正文 + 文件清单

- [x] 2.2.5 实现 Fallback 逻辑（对应 spec `Fallback 到 Scrapling`）
  - API 端点探测失败 → 退出码标识 + 错误信息
  - Phase A 失败 → 退出码标识 + 错误信息
  - Phase B 失败率 > 50% → 退出码标识 + 错误信息
  - 验证：模拟 API 不可用场景，工具正确报告 fallback 原因

### 2.3 Crawl 命令集成

- [x] 2.3.1 在 `crawl` 命令路由逻辑中增加 API 检查分支
  - 读取匹配的 strategy 文件
  - 检查 `api` 字段是否存在且 `api.platform` 为已知值
  - 满足条件时调用 `scripts/mediawiki-api-extract` 替代 Scrapling 路径
  - API 路径失败时自动 fallback 到 Scrapling crawl
  - 验证：`chrome-agent crawl https://balatrowiki.org/w/Jokers` 触发 API 路径
  - 验证：`chrome-agent crawl https://vampire.survivors.wiki/w/Crawlers:Wiki` 触发 API 路径
  - 验证：对无 `api` 字段的策略（如 `fanbox.cc`），行为不变

- [x] 2.3.2 在 crawl report 中记录提取方法
  - 报告字段：`extraction_method: "mediawiki_api"` 或 `"scrapling"`
  - fallback 发生时记录 `fallback_reason`
  - 验证：API 路径和 Scrapling 路径的 report 字段区分明确

## 3. 收敛与验证准备

- [x] 3.1 整理 verification 检查点
  - Spec-to-implementation 覆盖矩阵（每个 spec requirement → 对应实现位置）
  - balatrowiki.org 全量 crawl 验证（Phase A+B+C 完整执行）
  - vampire.survivors.wiki 对比验证（API 路径 vs Scrapling 路径输出质量对比）
  - Fallback 验证（模拟 API 不可用时的 Scrapling fallback）
  - 输出格式契约验证（Markdown 文件结构、frontmatter 完整性、链接可解析性）

- [x] 3.2 标记 writeback 目标
  - `site-strategy-schema` spec 更新（合并 delta 到 frozen spec）
  - `mediawiki-api-extraction` spec 冻结
  - `balatrowiki.org/strategy.md` 和 `vampire.survivors.wiki/strategy.md` 的 `api` 字段
  - `registry.json` 条目修复
  - `AGENTS.md` crawl 路径路由更新
  - 经验回写：`my-wiki/docs/workflow-experience/` 中记录 API 路径的使用经验

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）

## 5. DPL 表格还原与噪音清理增强

- [x] 5.1 在 Phase B wikitext 转换中增加 HTML 注释过滤（`<!-- ... -->` 整块移除）
- [x] 5.2 在 Phase B wikitext 转换中增加 DPL 块占位标记（`<dpl>...</dpl>` 替换为占位符，供 Phase C 识别和替换）
- [x] 5.3 扩展 `balatrowiki.org/strategy.md` 的 `output.frontmatter_fields`，增加 `number`, `image`, `unlock`, `activation` 以覆盖 DPL 表格所需的全部列
- [x] 5.4 在 Phase C index.md 生成中实现数据驱动的 DPL 表格还原：从 Phase B frontmatter 数据 + Phase A manifest 分类归属组装 Markdown 汇总表格，替换 DPL 占位符
- [x] 5.5 验证：重新提取 Jokers/Jokers.md，确认 DPL 块被替换为结构化 Markdown 表格，HTML 注释已清除
