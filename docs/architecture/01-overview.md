# 系统总览（System Overview）

## 定位

**chrome-agent** 是**跨仓库网页抓取服务（cross-repo web scraping service）**，为 AI agent 提供标准化、可复用的网页内容获取流程。其核心职责是获取和分析网页内容，将浏览器访问与诊断能力作为下层服务能力层使用。

## 核心设计原则

| 原则 | 说明 |
|------|------|
| **Scrapling-first** | 默认使用 Scrapling 作为抓取引擎，仅在需要结构化诊断证据时 fallback 到浏览器工具 |
| **Workflow-driven** | 通过 `AGENTS.md` + skills 定义标准化工作流程，而非依赖临时脚本 |
| **Read-only by default** | 对已登录页面只做读操作，不写回，除非用户明确扩大范围 |
| **Evidence-driven** | 每次任务产出可追溯的报告，为后续流程改进和策略库积累提供依据 |

## 多后端架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     用户 / AI Agent                                 │
│          (通过 SKILL.md 或全局 chrome-agent CLI 入口)                │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   CLI 入口 (.mjs)       │
          │   scripts/chrome-agent-  │
          │   cli.mjs               │
          │   parseArgs() → main()  │
          └────┬────────────────┬───┘
               │                │
     ┌─────────▼──────┐  ┌─────▼──────────────┐
     │  Scrapling 路径 │  │  MediaWiki API 路径  │
     │  (Scrapling CLI)│  │  (scripts/pipeline/)│
     └────┬───────────┘  └────┬────────────────┘
          │                   │
  ┌───────▼────────┐   ┌─────▼──────────────────┐
  │  引擎链         │   │  五阶段管线             │
  │  scrapling-get  │   │  discovery → fetch →   │
  │  obscura-fetch  │   │  convert → assemble →  │
  │  scrapling-fetch│   │  link-fix + validation │
  │  cloakbrowser   │   └────┬──────────────────┘
  │  chrome-devtools│        │
  │  chrome-cdp     │        │
  └───────┬────────┘        │
          │                  │
  ┌───────▼──────────────────▼──┐
  │       策略层 (Strategy)      │
  │  sites/strategies/<domain>/  │
  │  sites/anti-crawl/           │
  │  + 共享库 scripts/lib/       │
  └─────────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **CLI 入口** | Node.js ESM（`.mjs`） | 无 TypeScript，无编译步骤；依赖 `yaml` |
| **MediaWiki 管线** | Python 3.9+ | `scripts/pipeline/`，纯 stdlib + `requests` + `pyyaml` |
| **Explore 管线** | Python 3.10+ | `scripts/explore/`，额外依赖 `beautifulsoup4`、`selectolax` |
| **共享库** | Python | `scripts/lib/`（strategy_loader、config_resolver、extraction） |
| **抓取引擎** | Scrapling / Obscura / CloakBrowser | preflight 受管安装，版本锁定 |
| **策略格式** | YAML frontmatter + Markdown | `sites/strategies/<domain>/strategy.md` |
| **Shell 脚本** | Bash / POSIX sh | preflight、版本检测、安装脚本 |
| **测试** | `node:test` + `unittest` | 无第三方测试框架依赖 |

## 目录结构

```
.
├── AGENTS.md                    # 治理文档（服务身份、能力契约、治理规则）
├── README.md                    # 仓库全景
├── package.json                 # Node.js 依赖（yaml）
├── configs/
│   ├── engine-registry.json     # 引擎注册索引（类型、评分、状态）
│   ├── engine-versions.json     # 引擎版本清单（权威来源）
│   └── backend-signatures.json  # 后端检测签名
├── docs/
│   ├── architecture/            # 架构文档（本目录）
│   ├── decisions/               # 架构决策记录（ADR）
│   ├── playbooks/               # 操作手册
│   ├── plans/                   # 实现规划
│   └── setup/                   # 环境配置
├── openspec/
│   ├── changes/                 # 进行中 + 已归档的变更
│   └── specs/                   # 已冻结的能力规范
├── outputs/                     # 抓取产出暂存区（.gitignore）
├── reports/                     # 执行报告与证据
├── scripts/
│   ├── chrome-agent-cli.mjs     # CLI 主入口（所有命令逻辑）
│   ├── chrome-agent-runtime.mjs # 全局 launcher（repo 解析 + 分发）
│   ├── *.sh                     # Preflight / 安装 / 版本检测脚本
│   ├── lib/                     # 共享 Python 库
│   │   ├── strategy_loader.py   #   策略 frontmatter 解析
│   │   ├── config_resolver.py   #   速率限制 + 分类排除优先级解析
│   │   └── extraction/          #   共享提取引擎（infobox / preprocessor / converter）
│   ├── pipeline/                # MediaWiki API 提取管线
│   │   ├── __main__.py          #   python3 -m scripts.pipeline 入口
│   │   ├── cli.py               #   子命令路由（pipeline/fetch/reprocess/fix-links/reconvert）
│   │   ├── client.py            #   MediaWiki API 客户端（重试 + 退避）
│   │   ├── standalone.py        #   单页 fetch+convert
│   │   ├── pipeline/            #   管线核心
│   │   │   ├── orchestrator.py  #     主编排器（run_pipeline 入口）
│   │   │   ├── registry.py      #     策略注册表（_STRATEGY_REGISTRY）
│   │   │   ├── cache.py         #     持久化页面缓存
│   │   │   ├── state.py         #     断点续传状态
│   │   │   ├── discovery_summary.py  # 发现摘要生成
│   │   │   ├── homepage_parser.py    # 首页解析
│   │   │   ├── page_assigner.py      # 页面→目录分配
│   │   │   ├── phases/          #     各阶段实现
│   │   │   │   ├── discovery_homepage.py  # Phase 0: 首页发现
│   │   │   │   ├── discovery_allpages.py  # Phase A: 全页发现
│   │   │   │   ├── fetch.py              # Phase Fetch: API 内容获取
│   │   │   │   ├── convert.py            # Phase Convert: 内容→Markdown
│   │   │   │   └── assemble.py           # Phase C: 输出装配
│   │   │   └── strategies/      #     策略实现类
│   │   │       ├── discovery.py        # 发现策略（allpages, category_members）
│   │   │       ├── acquisition.py      # 内容获取策略
│   │   │       ├── link_resolver.py    # 链接解析策略
│   │   │       ├── template.py         # 模板处理策略
│   │   │       └── list_assembler.py   # 列表页装配策略
│   │   ├── converters/          #   格式转换器（wikitext / card_stats / link_fixer）
│   │   │   ├── wikitext_to_md.py
│   │   │   ├── card_stats.py
│   │   │   └── link_fixer.py
│   │   └── tests/               #   Python 单元测试
│   └── explore/                 # Deep discovery 管线
│       ├── main.py              #   CLI 入口
│       ├── probe_chain.py       #   引擎链探测
│       ├── api_discovery.py     #   API 端点发现
│       ├── structure_mapper.py  #   结构映射
│       ├── protection_identifier.py  # 保护识别
│       ├── sample_converter.py  #   样本转换
│       ├── self_check.py        #   自检
│       ├── architecture_gate.py #   架构闸门
│       ├── ki_lifecycle.py      #   Known Issue 生命周期
│       ├── freeze.py            #   策略冻结
│       ├── iterate.py           #   迭代优化
│       ├── scope_confirmer.py   #   范围确认
│       └── strategy_scaffold_generator.py  # 脚手架生成
├── sites/
│   ├── strategies/              # 站点策略（按域名文件夹组织）
│   │   ├── <domain>/strategy.md #   YAML frontmatter + 正文
│   │   └── registry.json        #   策略索引
│   └── anti-crawl/              # 反爬策略（按保护机制命名）
│       ├── default.md           #   默认 Scrapling-first 策略
│       ├── <mechanism>.md       #   具体反爬策略
│       └── registry.json        #   索引
├── skills/                      # 全局 workflow skill 源码
│   └── chrome-agent/SKILL.md    #   推荐 agent-first 入口
└── tests/                       # Node.js 测试
```

## 关键数据流

1. **用户请求** → SKILL.md / CLI → 意图路由（explore/fetch/crawl/scrape）
2. **策略匹配** → `sites/strategies/<domain>/strategy.md` → frontmatter 解析
3. **引擎选择** → Scrapling-first → 按需 fallback 到 obscura/cloakbrowser/devtools/cdp
4. **MediaWiki 站点** → 自动路由到 API 管线（`scripts/pipeline/`）
5. **输出** → `outputs/` 暂存 + `reports/` 持久报告

## 关联文档

- [00 — 目标架构](00-target-architecture.md) — **架构真源**：4 维能力模型、声明 Schema、能力注册表
- [02 — 管线数据流](02-pipeline-flow.md) — MediaWiki API 五阶段管线详解
- [06 — 引擎选择](06-engine-selection.md) — 引擎选择决策树与 fallback 机制
- [07 — Explore 工作流](07-explore-workflow.md) — 站点分析 deep discovery 管线
- [08 — 技术栈](08-tech-stack.md) — 运行时依赖与组件关系图


---
