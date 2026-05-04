# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `mediawiki-site-strategy` spec 的实现范围：创建 strategy.md + registry.json 更新
  - 验证方式：检查 `sites/strategies/vampire.survivors.wiki/strategy.md` 存在且 frontmatter 完整
- [x] 1.2 确认 `mediawiki-extraction-patterns` spec 的实现范围：创建 docs/patterns/mediawiki-extraction.md
  - 验证方式：检查文件存在且包含 Platform Taxonomy / Noise Taxonomy / Cleanup Pipeline / Cross-site Reuse 四节
- [x] 1.3 确认 `mediawiki-cleanup-script` spec 的实现范围：创建 clean-mediawiki.sh + extract-links.py
  - 验证方式：检查两个脚本存在且可执行，`--help` 返回 profile 列表和规则说明

## 2. 核心实现任务

- [x] 2.1 创建 `sites/strategies/vampire.survivors.wiki/strategy.md`
  - 实现路径：基于 spec `mediawiki-site-strategy` 的 Requirement: 策略文件创建
  - frontmatter 字段：domain, description, protection_level=low, anti_crawl_refs=[], engine_preference=scrapling-get, structure, extraction.cleanup
  - 验证方式：`yamllint` 通过（如可用）或人工确认 YAML 结构
- [x] 2.2 创建 `docs/patterns/mediawiki-extraction.md`
  - 实现路径：基于 spec `mediawiki-extraction-patterns` 的 Requirement: 通用模式文档
  - 必须覆盖：Platform Taxonomy, Noise Taxonomy (4 clusters), Cleanup Pipeline, Cross-site Reuse checklist
  - 验证方式：grep 确认四个章节标题存在
- [x] 2.3 创建 `sites/strategies/vampire.survivors.wiki/_attachments/clean-mediawiki.sh`
  - 实现路径：基于 spec `mediawiki-cleanup-script` 的 Site-Strategy 分流 + 噪音规则聚类
  - 必须支持：`--site vampire-survivors|balatro|generic-mediawiki`
  - 必须包含 4 个 cluster（navigation/template/link/table），每个 cluster 含具体规则
  - 验证方式：`bash -n clean-mediawiki.sh` 通过 + 试运行 `--help`
- [x] 2.4 创建 `sites/strategies/vampire.survivors.wiki/_attachments/extract-links.py`
  - 实现路径：提取分类页中的内部 wiki 链接，过滤噪音（?action=, ?oldid=, redlink, Template:, File:, Category:, Special:）
  - 必须输出：去重的 URL 列表
  - 验证方式：`python3 -m py_compile extract-links.py` 通过 + 用 balatrowiki.org 首页测试一次
- [x] 2.5 更新 `sites/strategies/registry.json`
  - 实现路径：新增 vampire.survivors.wiki 条目
  - 必须包含：domain, description, protection_level, page_types=[static_page, static_article], pagination=[none], entry_points=[wiki_category], anti_crawl_refs=[], file
  - 验证方式：`python3 -c "import json; json.load(open('registry.json'))"` 通过 + domain 字段匹配

## 3. 收敛与验证准备

- [x] 3.1 整理 verification 证据清单：
  - strategy.md YAML frontmatter 完整性
  - registry.json 可解析性
  - clean-mediawiki.sh `--site vampire-survivors` 对已知吸血鬼 wiki 输出执行一次
  - clean-mediawiki.sh `--site balatro` 对 balatrowiki.org Jokers 页 Scrapling 输出执行一次
  - extract-links.py 对 balatrowiki.org 首页执行一次，检查链接数量 > 0
- [x] 3.2 标记 writeback 摘要：策略库新增 1 站点，引擎注册表无需变更，AGENTS.md section 7 无需变更（遵循既有治理规则）

## 4. 验证与回写收敛

- [x] 4.1 运行 `chrome-agent crawl` 试跑（3-5 页）验证策略 traversal 边界
  - 验证方式：确认 crawl 从 wiki_category 入口开始，正确识别 wiki_article 链接，bounded traversal 不越界
- [x] 4.2 生成 verification.md：记录 spec-to-implementation 对照和 task-to-evidence
- [x] 4.3 生成 writeback.md：定义回写目标、字段映射、执行摘要
- [x] 4.4 执行回写：将策略文件、脚本、文档、registry 更新提交到仓库
