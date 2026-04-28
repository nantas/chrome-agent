# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `site-strategy-schema` spec 覆盖：frontmatter 字段定义、structure 页面层级、page_type 词汇表、pagination 模式、registry.json 格式、_attachments 目录用途、protection_level 词汇表
- [x] 1.2 确认 `anti-crawl-schema` spec 覆盖：frontmatter 字段定义、protection_type 词汇表、detection 信号结构、engine_sequence 规则、default 默认策略、success/failure signals、registry.json 格式
- [x] 1.3 确认 AGENTS.md 中策略库治理约束的插入位置（在 "参考索引" 之前追加 "策略库治理" Section）

## 2. 目录结构创建

- [x] 2.1 创建 `sites/anti-crawl/` 目录（若不存在）
- [x] 2.2 创建 `sites/strategies/` 目录（若不存在）
- [x] 2.3 将现有 `sites/` 下 5 个文件移出到临时位置，保留 `sites/README.md`

## 3. 反爬策略文件创建

- [x] 3.1 创建 `sites/anti-crawl/default.md` — 默认策略（`scrapling-get → scrapling-fetch → scrapling-stealthy-fetch → chrome-devtools-mcp`）
- [x] 3.2 创建 `sites/anti-crawl/cloudflare-turnstile.md` — 从 `wiki.supercombo.gg-cloudflare-challenge.md` 提取反爬经验
- [x] 3.3 创建 `sites/anti-crawl/login-wall-redirect.md` — 从 `x.com-public-hashtag-search-login-gate.md` 提取登录门经验
- [x] 3.4 创建 `sites/anti-crawl/cookie-auth-session.md` — 从 `fanbox.cc-content-download.md` 提取 cookie 认证经验
- [x] 3.5 创建 `sites/anti-crawl/rate-limit-api.md` — 从 `fanbox.cc-content-download.md` 提取 rate limit 经验
- [x] 3.6 创建 `sites/anti-crawl/registry.json` — 包含上述 5 个反爬策略的索引条目

## 4. 站点策略文件迁移

- [x] 4.1 创建 `sites/strategies/mp.weixin.qq.com/strategy.md` — 从 `wechat-public-article.md` 迁移，填充 YAML frontmatter（`protection_level: low`，单页面 `static_article`，提取选择器）
- [x] 4.2 创建 `sites/strategies/x.com/strategy.md` — 合并 `x.com-public-tweet.md` 和 `x.com-public-hashtag-search-login-gate.md`，两个 entry points（`public_tweet` + `hashtag_search`），per-page anti_crawl_refs
- [x] 4.3 创建 `sites/strategies/wiki.supercombo.gg/strategy.md` — 从 `wiki.supercombo.gg-cloudflare-challenge.md` 迁移站点结构部分（反爬部分已提取到 `cloudflare-turnstile.md`），`anti_crawl_refs: [cloudflare-turnstile]`
- [x] 4.4 创建 `sites/strategies/fanbox.cc/strategy.md` — 从 `fanbox.cc-content-download.md` 迁移站点结构、页面层级、提取流程，操作内容分离到 `_attachments/`
- [x] 4.5 创建 `sites/strategies/fanbox.cc/_attachments/` — 移入 batch download 脚本等相关附件
- [x] 4.6 创建 `sites/strategies/registry.json` — 包含上述 4 个站点策略的索引条目

## 5. 文档更新

- [x] 5.1 重写 `sites/README.md` — 说明两层目录结构、策略文件格式、registry.json 用途、如何新增策略
- [x] 5.2 更新 `AGENTS.md` — 在治理章节中追加策略库治理约束（新增策略需同步更新 registry.json，frontmatter 为权威来源）
- [x] 5.3 更新 `docs/governance-and-capability-plan.md` — Phase 3 描述从 "策略库标准化" 更新为与交付物一致的精确定义
- [x] 5.4 清理旧文件 — 删除临时位置中的 5 个原始站点文件（内容已迁移到新结构）

## 6. 收敛与验证准备

- [x] 6.1 逐文件验证：每个策略文件 YAML frontmatter 字段完整（符合 spec 的 SHALL 要求）
- [x] 6.2 逐文件验证：每个 strategy.md 的 `domain` 与目录名一致
- [x] 6.3 逐文件验证：每个 anti-crawl.md 的 `id` 与文件名 stem 一致
- [x] 6.4 逐 registry 验证：registry.json 中每个条目的 `file` 路径指向存在的文件
- [x] 6.5 交叉引用验证：site-strategy 的 `anti_crawl_refs` 值都存在于 `anti-crawl/registry.json` 的 `id` 列表中
- [x] 6.6 engine_sequence 验证：所有反爬策略的 `engine_sequence` 中的 engine 名使用 `engine-contracts` spec 中的 canonical 标识符，序列为 canonical escalation chain 的子序列

## 7. 验证与回写收敛

- [x] 7.1 基于实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 7.2 基于 `verification.md` 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 7.3 执行 `writeback.md` 中定义的回写目标，记录可审计证据（链接、时间、执行人、结果）
