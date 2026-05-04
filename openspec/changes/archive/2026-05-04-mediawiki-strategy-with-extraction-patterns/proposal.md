# Proposal

## 问题定义

当前 chrome-agent 的 `crawl` 命令依赖 `site strategy` 存在才能执行。`vampire.survivors.wiki`（Weird Gloop 托管 MediaWiki）已完成 416 页批量抓取验证，但缺少站点策略注册，导致每次都必须通过 `fetch × N` 手动执行，无法使用 `crawl` 的 bounded traversal 能力。

此外，MediaWiki 内容提取面临 7+ 类噪音（infobox 空列、DPL wikitext 泄露、导航菜单、Category 链接、嵌套图片链接等），每次抓取后需要大量后处理。这些经验未沉淀为可复用的提取模式，新遇到 MediaWiki 站点时需从零清洗。

## 范围边界

**范围内：**
- 为 `vampire.survivors.wiki` 创建完整 site strategy（frontmatter + Markdown body）
- 创建通用 MediaWiki 提取模式参考文档（docs/patterns/mediawiki-extraction.md）
- 创建可复用的噪音清洗脚本（clean-mediawiki.sh），支持 site-strategy 分流 + 噪音聚类
- 创建分类页链接提取脚本（extract-links.py）
- 更新 `sites/strategies/registry.json` 索引

**范围外：**
- 不修改 site-strategy-schema 的受控词汇表（page_type、protection_level 不变）
- 不修改现有站点策略
- 不创建新的反爬策略（protection_level = low，无需 anti-crawl）
- 不实现 crawl 命令本身（只提供策略，使其可被 crawl 消费）

## Capabilities

### New Capabilities

- `mediawiki-site-strategy`: 为 Weird Gloop 托管 MediaWiki 创建 vampire.survivors.wiki 站点策略，使 crawl 命令可识别入口点、遍历边界和分页模式
- `mediawiki-extraction-patterns`: 定义跨站点的 MediaWiki 内容提取模式与噪音分类学，覆盖 navigation / template / link / table 四类噪音集群
- `mediawiki-cleanup-script`: 提供基于 site-strategy 分流的噪音清洗脚本，支持 vampire-survivors、balatro、generic-mediawiki 三个 profile

### Modified Capabilities

- （无 — 所有变更均为新增，不修改既有规范 schema）

## Capabilities 待确认项

- [x] 能力清单已与用户确认（3 个 New，0 个 Modified）
- [x] 通用模式文档的维护边界已确认（v1 草稿，以 vampire 经验为主，balatro 验证为辅）

## Impact

| 维度 | 影响 |
|------|------|
| 用户体验 | vampire.survivors.wiki 下次可直接 `chrome-agent crawl`，无需手动 fetch + 链接提取 |
| 复用性 | 新遇到 Weird Gloop / MediaWiki 站点时，可直接复用提取模式和清洗脚本，减少 80%+ 重复工作 |
| 维护成本 | 策略库索引自动扩展，7 类噪音规则集中维护，避免散落在各处 |
| 验证 | balatrowiki.org 实测验证 79% 规则复用率，2 个差异点已纳入通用文档 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md`、`repo://chrome-agent/openspec/specs/strategy-guided-crawl/spec.md`
  - 项目页：`repo://my-wiki/docs/workflow-experience/vampire-survivors-wiki-scrape.md`
  - 回写目标：`sites/strategies/vampire.survivors.wiki/strategy.md`、`sites/strategies/vampire.survivors.wiki/_attachments/`、`docs/patterns/mediawiki-extraction.md`、`sites/strategies/registry.json`
