# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 specs/* coverage: explore-workflow (7 requirements), strategy-templates (4 requirements), sample-self-check (8 requirements), explore (2 MODIFIED requirements)
- [x] 1.2 确认依赖前置: `markdownify` + `beautifulsoup4` 作为转换管线依赖已存在
- [x] 1.3 确认已有的 `scripts/mediawiki-api-extract/converters/fandom_html_to_markdown.py` 可作为参考实现

## 2. 核心实现任务

### 2.1 Deep Discovery 引擎链探测（specs/explore-workflow: deep-discovery.chain-engine-probe）

- [x] 2.1.1 实现 `ProbeChain` 模块：按序尝试 scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
- [x] 2.1.2 每级记录: `{engine, status, http_status, error_type, page_title, content_length}`
- [x] 2.1.3 `explore` CLI 集成：strategy-gap 时自动触发 probe chain

### 2.2 Deep Discovery API 发现（specs/explore-workflow: deep-discovery.api-discovery）

- [x] 2.2.1 实现 `ApiDiscovery` 模块：探测 /api.php, /wp-json, /graphql, /sitemap.xml, /robots.txt
- [x] 2.2.2 对 MediaWiki API: 调用 `action=query&meta=siteinfo&siprop=general|statistics` 获取版本、规模
- [x] 2.2.3 记录: `{type, base_url, version, capabilities[]}`

### 2.3 Deep Discovery 结构映射（specs/explore-workflow: deep-discovery.structure-mapping）

- [x] 2.3.1 实现 `StructureMapper` 模块：从 HTML 提取 nav 栏目 (≤10)，页面类型 (home/list/article/gallery)
- [x] 2.3.2 实现内容结构检测：有无表格（>2 `<tr>`）、infobox（特定 class）、列表/卡片模式
- [x] 2.3.3 如果 API 可用: 查询 `categorymembers` 获取各分类成员数

### 2.4 Deep Discovery 保护识别（specs/explore-workflow: deep-discovery.protection-identification）

- [x] 2.4.1 实现 `ProtectionIdentifier` 模块：基于 engine chain 错误 + HTML 特征判断保护类型
- [x] 2.4.2 匹配规则: 403 + "Just a moment..." → cloudflare-managed; 403 + cf-turnstile → cloudflare-turnstile; 429 → rate-limit
- [x] 2.4.3 记录: `{type, detection_basis, engine_override}`

### 2.5 用户交互确认（specs/explore-workflow: user-interactive-confirmation）

- [x] 2.5.1 实现 `ScopeConfirmer` 模块：通过 ask_user 实现 4 轮对话
- [x] 2.5.2 Round 1: 内容范围（全部 / 指定栏目 / 后续指定），基于 discovery 结果动态生成选项
- [x] 2.5.3 Round 2: 页面粒度（汇总+独立 / 仅独立 / 仅汇总），对无独立条目的分类明确提示
- [x] 2.5.4 Round 3: 样本推荐（自动选择 4-8 个覆盖各类型，用户确认或调整）
- [x] 2.5.5 Round 4: 输出格式（Markdown+frontmatter / 纯 Markdown / JSON）

### 2.6 策略模板系统（specs/strategy-templates）

- [x] 2.6.1 创建 `sites/templates/` 目录
- [x] 2.6.2 创建首批模板: `mediawiki.yaml`, `mediawiki-fandom.yaml`, `mediawiki-wiki-gg.yaml`, `static-site.yaml`, `custom.yaml`
- [x] 2.6.3 创建 `sites/templates/registry.json`（索引每个模板的 id/platform/protection_level/file）
- [x] 2.6.4 实现模板选择逻辑：基于 deep discovery 的 platform 和 protection 选择最佳匹配模板

### 2.7 策略 Scaffold 生成（specs/explore-workflow: strategy-scaffold-generation）

- [x] 2.7.1 实现 `StrategyScaffoldGenerator`：基于模板 + discovery 结果填充 frontmatter
- [x] 2.7.2 填入: domain, description, protection_level, anti_crawl_refs, structure.pages[], api config, extraction rules
- [x] 2.7.3 文件头标注 `# Auto-generated scaffold — review recommended`

### 2.8 样本转换（specs/explore-workflow: sample-conversion-and-self-check）

- [x] 2.8.1 实现样本获取：使用 discovery 阶段确定的引擎/API 路径
- [x] 2.8.2 集成转换管线：应用 scaffold 中的 extraction rules
- [x] 2.8.3 复用或适配 `fandom_html_to_markdown.py` 作为 MediaWiki-Fandom 平台的转换引擎

### 2.9 自检体系（specs/sample-self-check）

- [x] 2.9.1 实现 S1 (Image Retention): 原始 `<img>` vs Markdown `![]()` 计数对比
- [x] 2.9.2 实现 S2 (Link Resolution): 内部 wiki 链接的 `.md` 解析验证
- [x] 2.9.3 实现 S3 (Infobox Extraction): wikitext infobox 的结构化提取验证
- [x] 2.9.4 实现 S4 (Empty Content): Markdown 正文非空验证
- [x] 2.9.5 实现 S5 (Text Integrity): 空格缺失 / base64 残留 / 转义残留扫描
- [x] 2.9.6 实现 S6 (Table Integrity): 汇总页表格结构保留验证
- [x] 2.9.7 实现 S7 (Image Wrapper): 图片外链包裹检测
- [x] 2.9.8 实现 Auto-Remediation Loop: 已知可修复问题的自动修正 + 最多 2 轮迭代

### 2.10 策略冻结（specs/explore-workflow: strategy-freeze）

- [x] 2.10.1 实现 `freeze` 子命令: 移除 scaffold 标记，写入 registry.json，生成最终报告
- [x] 2.10.2 实现 `iterate` 子路径: 用户反馈 → 更新 extraction → 重跑样本转换 → 重新提交审阅

### 2.11 explore 命令修改（specs/explore: explore-command-backend）

- [x] 2.11.1 修改 backend：strategy-match 走旧路径，strategy-gap 走新管线
- [x] 2.11.2 扩展输出格式：添加 discovery, scaffold, samples, self_check 字段

## 3. 收敛与验证准备

- [x] 3.1 验证检查点清单：
  - [x] Deep discovery 在 strategy-gap URL 上能正确执行 engine chain
  - [x] API discovery 能正确识别 MediaWiki 并获取 siteinfo
  - [x] Structure mapping 能正确提取 nav 结构和内容类型
  - [x] 用户交互 4 轮对话能正常完成（skill 层基于 discovery JSON 数据驱动）
  - [x] 模板选择能根据 platform 类型选择正确模板
  - [x] Scaffold 生成包含完整 frontmatter
  - [x] 样本转换能正确应用 extraction rules
  - [x] S1-S7 能正确 pass/fail
  - [x] Auto-remediation loop 不超过 2 轮
  - [x] Strategy-matched URL 不受影响（依然走旧路径）
- [x] 3.2 标记 writeback 目标: AGENTS.md (路由规则更新), docs/playbooks/ (新建操作手册)

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
