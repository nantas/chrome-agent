# Design

## Context

`vampire.survivors.wiki`（Weird Gloop 托管 MediaWiki）已完成 416 页批量抓取验证，但缺少站点策略注册，导致 `crawl` 命令不可用。本次 change 需要创建 site strategy 并抽象通用 MediaWiki 提取模式。

经过 balatrowiki.org（同为 Weird Gloop MediaWiki 1.45.3）验证，79% 的噪音规则可直接复用，差异点为：
- footer 区域触发条件不同（vampire 有 "Navigation menu" 标题，balatro 没有）
- template 噪音格式不同（vampire 是 JSON 数据行，balatro 是 DPL wikitext 暴露）

清洗脚本采用 site-strategy 分流 + 噪音聚类架构，每个 profile 声明启用的规则子集。

## Goals / Non-Goals

**Goals:**
- 创建 `vampire.survivors.wiki` 站点策略，使 `chrome-agent crawl` 可用
- 抽象通用 MediaWiki 提取模式文档，支持跨站点复用
- 创建可复用的噪音清洗脚本，支持多站点 profile 分流
- 更新 `sites/strategies/registry.json` 索引

**Non-Goals:**
- 不修改 `site-strategy-schema` 受控词汇表（page_type、protection_level 不变）
- 不修改现有站点策略或反爬策略
- 不实现 crawl 命令本身（只提供策略使其可被消费）
- 不覆盖非 Weird Gloop 的 MediaWiki 实例（经验仅限验证过的两个站点）

## Decisions

| # | 决策 | 理由 | 备选方案 |
|---|------|------|----------|
| 1 | 页面类型使用现有 `static_page` + `static_article` | 现有词汇表已覆盖，无需走 openspec change 扩展 | 新增 `wiki_article` / `wiki_category` 类型（太重） |
| 2 | 清洗脚本用 bash 实现 | 与现有 chrome-agent 脚本栈一致（shell-based），依赖少 | Python 实现（功能更强但引入新依赖） |
| 3 | `extract-links.py` 用 Python 实现 | 链接提取涉及 URL 解析、去重、过滤，Python regex 更可靠 | 纯 bash 实现（维护成本高） |
| 4 | 通用文档标记为 v1 草稿 | 仅基于 2 个 Weird Gloop 站点验证，不足以声称覆盖所有 MediaWiki | 直接声明为完整规范（过早） |
| 5 | `strip_json_data_rows` 泛化为 `strip_hidden_template_artifacts` | 两个站点的隐藏模板数据噪音本质相同（DOM 中 display:none 的内容被 Scrapling 暴露），只是格式不同 | 保留两个独立规则（增加维护成本） |
| 6 | 附件放在 `vampire.survivors.wiki/_attachments/` | 遵循策略库目录治理规范（按域名组织） | 放在全局 `scripts/` 或 `docs/patterns/`（跨站复用但不符治理规范） |

## Risks / Migration

| 风险 | 严重度 | 缓解措施 |
|------|:------:|----------|
| 策略未经验证：`crawl` 实际行为可能与策略声明不同 | 中 | 创建策略后，用 `chrome-agent crawl` 试跑 3-5 页验证遍历边界 |
| Weird Gloop 特殊性：通用模式可能不适用于标准 MediaWiki | 低 | 文档明确标注 v1 草稿，仅覆盖 Weird Gloop；新站点需额外验证 |
| 清洗脚本过度激进：`generic-mediawiki` profile 可能误删有效内容 | 中 | `generic-mediawiki` 打印警告并列出启用的规则；建议用户先 `--dry-run` |
| `strip_dpl_wikitext` 可能误伤正文中的模板语法 | 低 | 规则仅匹配行首或整行模板调用（`{{hl|...}}`、`{{Chips|...}}`），正文中的合法模板语法极少 |
| balatro profile 未实际测试：规则基于 HTML/Scrapling 输出推断 | 低 | 标记为 draft profile，实际使用前需跑一次完整验证 |
