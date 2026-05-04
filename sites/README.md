# Sites — 策略库

本目录按两层结构组织策略文件：反爬策略 + 站点策略。

## 目录结构

```
sites/
├── anti-crawl/                      # 反爬策略（按保护机制命名）
│   ├── default.md                   #   默认策略（无匹配时的 fallback）
│   ├── cloudflare-turnstile.md      #   Cloudflare Turnstile 挑战
│   ├── login-wall-redirect.md       #   登录墙重定向
│   ├── cookie-auth-session.md       #   Cookie 认证会话
│   ├── rate-limit-api.md            #   API 频率限制
│   └── registry.json                #   反爬策略索引
│
├── strategies/                      # 站点策略（按域名文件夹组织）
│   ├── mp.weixin.qq.com/
│   │   └── strategy.md              #   微信公众文章
│   ├── x.com/
│   │   └── strategy.md              #   X (Twitter) 推文 + 搜索
│   ├── wiki.supercombo.gg/
│   │   └── strategy.md              #   SuperCombo Wiki
│   ├── fanbox.cc/
│   │   ├── strategy.md              #   pixivFANBOX
│   │   └── _attachments/            #   操作附件（脚本、配置）
│   └── registry.json                #   站点策略索引
```

## 策略文件格式

每个策略文件包含 YAML frontmatter（结构化字段）和 Markdown body（描述性文档）。

### 反爬策略 (`sites/anti-crawl/<mechanism>.md`)

- **frontmatter 必填字段**: `id`, `protection_type`, `sites`, `detection`, `engine_priority`, `success_signals`, `failure_signals`
- **命名**: 按保护机制命名（如 `cloudflare-turnstile.md`），而非站点名
- **引用**: 站点策略通过 `anti_crawl_refs` 引用反爬策略的 `id`

### 站点策略 (`sites/strategies/<domain>/strategy.md`)

- **frontmatter 必填字段**: `domain`, `description`, `protection_level`, `anti_crawl_refs`, `structure`, `extraction` (可省略)
- **可选字段**: `engine_preference`，可在文件级或 `structure.pages[]` 级别声明首选引擎
- **命名**: 按域名文件夹组织（如 `x.com/strategy.md`）
- **附件**: `_attachments/` 目录存放脚本、配置等操作内容

## registry.json 索引

两层各有一个 `registry.json`，提供策略的查询摘要：

- **`sites/anti-crawl/registry.json`**: 按 `id`, `protection_type`, `sites`, `detection_summary`, `primary_engine`, `file` 索引
- **`sites/strategies/registry.json`**: 按 `domain`, `protection_level`, `page_types`, `pagination`, `entry_points`, `anti_crawl_refs`, `file` 索引

### 用途

- Agent 遇到 URL 时，先查询 registry.json 判断是否有已知策略
- 通过 frontmatter 字段匹配（protection_level, page_types, pagination 等）
- 无匹配时使用 `default` 反爬策略（Scrapling-first 逐级升级）

### 一致性

- **frontmatter 为权威来源**，registry.json 仅为索引摘要
- 不一致时以 frontmatter 为准
- 新增/修改策略文件时需同步更新 registry.json

## 新增策略流程

1. **For 新站点**: 在 `sites/strategies/<domain>/` 下创建 `strategy.md`（含完整 frontmatter）
2. **For 新反爬**: 在 `sites/anti-crawl/` 下创建 `<mechanism>.md`（按保护机制命名）
3. **更新 registry.json**: 新策略必须添加对应索引条目
4. **如果站点首次遇到新反爬机制**: 先创建 anti-crawl 文件，再在 strategy.md 的 `anti_crawl_refs` 中引用

受控词汇表（`protection_level`, `page_type`, `protection_type`）定义在 `openspec/specs/site-strategy-schema/spec.md` 和 `openspec/specs/anti-crawl-schema/spec.md` 中。新增值需要通过 openspec change 扩展。

## 从已有后端派生策略（Bootstrap）

当 `explore` 检测到已知后端（如 Weird Gloop MediaWiki）但无匹配策略时，可以使用 `bootstrap-strategy` 命令从同后端的已有策略一键派生新策略：

```bash
chrome-agent bootstrap-strategy <target-url> --from <reference-domain> [--profile <cleanup-profile>]
```

### 前置条件

- `--from` 指定的参考域名必须已存在于 `sites/strategies/registry.json`
- 目标 URL 的域名在 registry.json 中**不能**已有策略
- 参考策略必须包含完整的 YAML frontmatter 和结构定义

### 生成内容

- `sites/strategies/<target-domain>/strategy.md`：基于参考策略的 frontmatter，替换 `domain`、`description`、`url_example`，并标记 `backend` 字段
- 自动更新 `sites/strategies/registry.json`，追加新条目

### 后续步骤

1. **Review 生成的策略**：检查 `description`、`url_example`、`structure.pages` 是否适配目标站点
2. **补充 Markdown body**：替换占位符章节（Page Structure、Extraction Flow、Known Issues）为实际操作细节
3. **验证 crawl**：运行 `chrome-agent crawl <target-url>` 验证策略有效性
4. **标记完成**：将 strategy.md 顶部的 `<!-- Bootstrapped from ...; review recommended -->` 移除或替换为验证日期

> **注意**: bootstrap 生成的策略是**草稿级别**，必须在生产使用前完成 review 和验证。
