# Design

## Context

当前 `chrome-agent explore` 遇到 strategy gap 时无深度分析能力。本次变更为其增加完整的探索工作流，覆盖 deep discovery、策略模板选择、用户交互确认、样本转换与自检、策略冻结全流程。变更的核心是将 explore 从"查表返回"升级为"探测→交互→产出"管线。

设计基于以下 spec 中输入：
- `specs/explore-workflow/spec.md` — 工作流整体规范
- `specs/strategy-templates/spec.md` — 模板系统规范
- `specs/sample-self-check/spec.md` — 自检体系规范
- `specs/explore/spec.md` — explore 命令修改规范

## Goals / Non-Goals

**Goals:**

- 实现 deep discovery 管线（引擎链 + API 发现 + 结构映射 + 保护识别）
- 实现平台策略模板系统（`sites/templates/` 首批 4 个模板）
- 实现用户交互确认流程（ask_user 多轮对话驱动样本选择）
- 实现 agent 样本自检体系（S1-S7 + auto-remediation loop）
- 实现策略冻结管线（scaffold 生成 → 用户确认 → registry 写入）
- 保持与已有 strategies（已注册域名）的向后兼容

**Non-Goals:**

- 不修改 `fetch` / `crawl` CLI 命令
- 不修改 engine-registry 或 anti-crawl 策略库
- 不实现 WordPress / GraphQL 模板的完整内容（v1 仅骨架）
- 不修改 doctor preflight 流程
- 不需要认证/鉴权探测

## Decisions

### D1: 深度探测分层设计

deep discovery 不需要完整链接拓扑。分层如下：

```
Layer 1: Engine Probe Chain
  scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
  每级: status + error + page_title + content_length

Layer 2: API Discovery (从 Layer 1 成功页面执行)
  /api.php → MediaWiki siteinfo
  /wp-json  → WordPress REST
  /graphql  → GraphQL
  /sitemap.xml, /robots.txt

Layer 3: Structure Mapping (从 Layer 1/2 成功结果执行)
  nav labels (≤10) → 内容分类
  page type (home/list/article/gallery) → DOM 特征
  template patterns (infobox/table/card) → HTML class 检测
  category counts → API categorymembers (if MediaWiki)

Layer 4: Protection Identification (从 Layer 1 失败结果执行)
  403 + "Just a moment..." → cloudflare-managed
  403 + cf-turnstile → cloudflare-turnstile
  429 + ratelimited → rate-limit
  redirect to /login → login-wall
```

### D2: 模板系统以平台类型为主轴

模板目录：`sites/templates/{platform}.yaml`，保护等级下沉到 `anti_crawl_refs`。

```
sites/templates/
├── registry.json         # {id, platform, protection_level, file}[]
├── mediawiki.yaml        # generic MediaWiki
├── mediawiki-fandom.yaml # Fandom-specific
├── mediawiki-wiki-gg.yaml
├── wordpress.yaml        # skeleton (partial in v1)
├── static-site.yaml
└── custom.yaml           # empty scaffold fallback
```

模板 YAML 用 `# SCAPFOLD: auto-generated — review recommended` 标记头部。

### D3: 用户交互通过 ask_user 实现，CLI 参数由 skill 路由

不要求用户了解 CLI 参数。`chrome-agent` skill 层整理用户意图路由到正确的命令。use `ask_user` 实现多轮对话：

```
Round 1: 内容范围
  → 基于检测到的栏目列表
  → 选项: 全部 / 指定 N 个栏目 / 后续指定

Round 2: 页面粒度
  → 选项: 汇总+独立 / 仅独立 / 仅汇总
  → 如 Pets/Pickups/Upgrades 只有汇总页，明确告知

Round 3: 样本确认
  → agent 推荐 4-8 个（按类型覆盖+边缘 case）
  → 用户确认或调整

Round 4: 输出格式
  → Markdown+frontmatter / 纯 Markdown / JSON
```

### D4: 自检体系以 pass/fail 二元输出

没有 warn 级别。除非源页面含有无效链接或错误，所有检查应通过。

- 已知可自动修复问题：base64 残留、空格不足、链接解析遗漏、table class 未覆盖
- 非自动修复：内容空、infobox 模板不匹配、结构性失败
- auto-remediation loop 上限 2 轮，超出标记 "needs human review"

### D5: 策略冻结流程

```
用户确认通过
  → strategy.md 移除 scaffold 标记
  → registry.json 追加条目
  → 最终报告生成
  → 修改 `AGENTS.md` 路由规则（explore 路径补充）
  → 操作手册 `docs/playbooks/explore-workflow-conduct.md` 产出
```

## Risks / Migration

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 模板系统与现有策略格式不一致 | 低 | 模板仅用于 scaffold 生成，不影响已有策略文件格式 |
| 用户交互流程太长（4 轮 ask_user） | 中 | 支持 CLI 参数跳过（由 skill 层处理），用户熟悉后可加 `--quick` |
| auto-remediation 循环无限 | 低 | 硬性上限 2 轮 |
| 新流程破坏已有 `explore` 行为 | 低 | strategy-matched 场景走旧路径，strategy-gap 场景走新路径，互不干扰 |
| 模板内容过时（平台升级） | 低 | 模板跟随 repo 版本管理，可按需更新 |
