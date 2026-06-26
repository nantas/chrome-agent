# Site strategy — reviewed after explore + sample QA
# Last updated: 2026-06-26 (post-sample-QA)

---
domain: rep.taptap.cn
description: TapTap REP 资源置换平台帮助文档站（Vue SPA，27 页）
protection_level: low
anti_crawl_refs:
- default
engine_preference:
  preferred: scrapling-fetch   # SPA requires JS rendering (scrapling-get returns empty shell)
structure:
  platform: vue-spa
  rendering: client-side
  nav_selector: ".framework-container a[href*='/docs/']"
  pages:
  - id: doc_detail
    label: REP 文档详情页
    type: dynamic_content       # triggers scrapling-fetch in selectFetcher()
    content_type: help_doc
    pagination: none
    requires_auth: false
    url_pattern: "/docs/taprep-{slug}"
  entry_points:
  - doc_detail
api:
  capabilities: []              # No public API; content is SPA-rendered HTML
  backend_host: "https://tap-op.tapapis.cn/"  # internal API, requires JWT
extraction:
  engine: scrapling-fetch
  selectors:
    content: ".rep-docs-content"
    title: ".rep-docs-content h1, .rep-docs-content h2"
    nav: ".framework-container"
  # SPA rendering options (consumed by scrapling extract fetch)
  # NOTE: chrome-agent pipeline does NOT yet consume these from strategy —
  # see GAP-S1 below. Until then, manual scrapling invocation passes them directly.
  fetch_options:
    network_idle: true
    wait_ms: 3000
    headless: true
  cleanup: []
  text_normalization: []
---

# rep.taptap.cn Strategy

## Platform Notes

TapTap REP 资源置换平台帮助文档。Vue SPA，所有 `/docs/*` 路由返回同一个
2267 字节空壳 HTML，内容由 JS 在客户端渲染（`#sub-app` 挂载点）。

**关键技术约束**：scrapling-get（静态 HTTP）对该站点产生"假成功"——HTTP 200
但 body 为空。必须使用 scrapling-fetch（Playwright 渲染）+ network-idle + wait。

## Site Map (27 pages, discovered via rendered sidebar)

### 一、平台介绍
- `taprep-about` — 平台介绍

### 二、使用教程
#### 1. 上传资源
- `taprep-brand` — 1.1 官网品牌挂件
- `taprep-game-jump` — 1.2 ❗️游戏跳转
- `taprep-material-auth` — 1.3 软著授权
- `taprep-forum` — 1.4 论坛运营
- `taprep-deep-cooperation` — 1.5 深度合作
- `taprep-research-password` — 1.6 搜索口令词
- `taprep-pc-launcher` — 1.7 ‼️TapPC版置换
- `taprep-pc-emulator` — 1.8 📌TapPC手游模拟器资源置换
- `taprep-pc-game-jump` — 1.9 PC游戏内活动跳转

#### 2. 推荐计划（广告投放）
- `taprep-ref-bid` — 2.1 站内投放
- `taprep-outsidead` — 2.2 站外促活投放
- `taprep-custom-tag` — 2.3 🔥自定义高光Tag
- `taprep-pc-bid` — 2.4 🔥PC首页投放

#### 3-8. 后台管理
- `taprep-task` — 3. 任务中心
- `taprep-defer` — 4. 流量金延期
- `taprep-permission` — 5. 权限开通
- `taprep-external-notice` — 6. 站外消息通知
- `taprep-punish` — 7. TapTap REP风控处罚规则
- `taprep-milestone` — 8. 🏆独家游戏里程碑奖励

### 三-八. 附录章节
- `taprep-income` — 三、各类资源结算收益说明
- `taprep-callback` — 四、推荐计划深度数据对接指引
- `taprep-loginsdk` — 五、登录SDK接入奖励
- `taprep-toBwxcoop` — 六、TOB自媒体置换合作
- `taprep-report` — 七、平台月报汇总
- `taprep-qa` — 八、常见问题

## Extraction Rules

- **Engine**: `scrapling-fetch`（Playwright 动态渲染）
- **Content selector**: `.rep-docs-content`（正文容器，含标题+正文+表格）
- **Render params**: `--network-idle --wait 3000 --headless`
- **Nav discovery**: 渲染入口页后提取 `.framework-container a[href*='/docs/']` 获取全量 slug

## Known Issues (KI)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| GAP-S1 | chrome-agent 策略不支持声明 SPA fetch_options（network_idle/wait） | open | P1 | pipeline | crawl 无法自动应用渲染参数 | openspec change: buildScraplingExtractionArgs 消费 fetch_options |
| GAP-S2 | explore Protection Identifier 无 SPA 空壳检测——HTTP 200 空壳被判 success | open | P1 | strategy | explore 不触发引擎升级 | 加 content_length < threshold 的空壳检测规则 |
| KI-1 | S5 Escape artifacts（×3 页）— markdown 转义符残留 | open | P2 | pipeline | 低危排版瑕疵 | 后处理正则清理 `\\*` 等 |
| KI-2 | S1 game-jump 图片丢失（22→7）— 装饰图被选择器过滤 | open | P2 | strategy | 部分内容图可能丢失 | 评估是否放宽选择器或加 wait-selector |
| KI-3 | S6 表格行偏差（×2 页）— 合并单元格被拆分 | open | P2 | pipeline | 表格行数不一致 | 表格解析处理 rowspan/colspan |
