# Proposal

## 问题定义

Phase 1 完成了治理基础重建（AGENTS.md 纯治理化、capability-contracts 契约元模型），Phase 2 完成了引擎契约冻结（5 个引擎契约 + engine-contracts 聚合索引）。但仓库的站点策略和反爬策略仍处于无结构状态：

1. **站点经验不可查询**：`sites/` 下 5 个文件使用 5 种不同的 Markdown 结构，没有统一的 YAML frontmatter、字段定义或索引机制。Agent 遇到新站点时无法快速检查是否有可复用的既有经验。
2. **反爬策略与站点深度绑定**：现有的 Cloudflare Turnstile、登录门、cookie auth 等反爬应对经验散落在各站点文件中，无法跨站点共享。不同站点面对类似保护机制时，需要重新推理或人工查找。
3. **缺少默认策略**：遇到无已知站点的简单页面时，没有显式定义的默认抓取策略（Scrapling-first 逐级升级），导致 Agent 行为取决于 AGENTS.md 路由规则的隐式推理。
4. **操作内容与策略数据混杂**：`fanbox.cc-content-download.md` 等文件嵌入了 bash 脚本、cookie 表格、CDP 命令等操作细节，与策略描述混合，不利于查询和复用。

## 范围边界

**范围内（本 change）：**
- 创建 `site-strategy-schema` spec：定义站点策略文件的结构化 schema（YAML frontmatter 字段定义、Markdown body 推荐章节、文件与目录存放规范）
- 创建 `anti-crawl-schema` spec：定义反爬策略文件的结构化 schema（YAML frontmatter 字段定义、Markdown body 推荐章节、命名与引用规范）
- 建立两层目录结构：`sites/anti-crawl/`（按保护机制命名）+ `sites/strategies/<domain>/`（按域名命名的文件夹）
- 为两层各创建 `registry.json` 索引文件，提供机器可查询的字段摘要
- 定义 `default.md` 默认反爬策略（Scrapling-first 逐级升级链）
- 创建受控词汇表（protection_type、page_type 等枚举值）
- 将现有 5 个站点文件迁移到新结构，操作内容分离到 `_attachments/`
- 通过 AGENTS.md 治理约束确保新增策略时自动更新 registry.json

**范围外（留到后续 Phase）：**
- 不涉及引擎调度（策略文件描述推荐引擎但不实现自动选择）
- 不涉及策略自动匹配（Agent 读取 registry.json 后自主判断，无自动路由引擎）
- 不创建新的抓取引擎
- 不涉及引擎注册或扩展机制（Phase 4）
- 不涉及输出生命周期管理（Phase 5）

## Capabilities

### New Capabilities
- `site-strategy-schema`: 定义站点策略文件的结构化 schema——YAML frontmatter 字段（domain, protection_level, anti_crawl_refs, structure.pages, extraction）、Markdown body 推荐章节、目录存放规范（`sites/strategies/<domain>/strategy.md` + `_attachments/`）、registry.json 索引格式
- `anti-crawl-schema`: 定义反爬策略文件的结构化 schema——YAML frontmatter 字段（id, protection_type, sites, detection, engine_sequence, success_signals, failure_signals）、Markdown body 推荐章节、命名规范（按保护机制而非站点命名）、registry.json 索引格式、default.md 默认策略

### Modified Capabilities
（无）

## Capabilities 待确认项

- [x] 能力清单已与用户确认（对话中确认：两层分离架构、site-strategy 按域名文件夹组织、anti-crawl 按保护机制命名、per-page 粒度的 anti_crawl_refs、受控词汇表、registry.json 索引、default.md 默认策略）

## Impact

**益处：**
- 站点结构化数据可通过 registry.json 快速查询（按域名、页面类型、分页机制、保护级别）
- 反爬策略可被多个站点引用，Cloudflare Turnstile / login-wall 等通用保护机制无需重复描述
- 新站点入库时只需填写结构化 frontmatter，Agent 可通过 registry.json 快速判断是否有可复用的策略
- 操作内容（脚本、命令）从策略文件中分离到 `_attachments/`，保持策略文件精简可读
- 默认策略为无已知策略的简单页面提供明确的行为定义

**影响到的既有文件：**
- `sites/` 目录完全重组为 `sites/anti-crawl/` + `sites/strategies/<domain>/`
- `sites/` 下现有 5 个文件迁移为新结构（内容保留，格式改造）
- `sites/README.md` 重写为两层目录说明
- `docs/governance-and-capability-plan.md` Phase 3 描述微调以反映实际交付物
- `AGENTS.md` 追加策略库治理约束（新增策略需同步更新 registry.json）

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
  - `writeback_targets`: Obsidian 项目页 + Writeback 记录页
