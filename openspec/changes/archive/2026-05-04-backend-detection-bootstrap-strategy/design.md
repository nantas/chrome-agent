# Design

## Context

当前 chrome-agent 的 `crawl` 命令被 `strategy-guided-crawl/spec.md` 严格门控：只有 `sites/strategies/registry.json` 中存在精确域名匹配的策略时才能执行。当遇到与已有策略共享同一后端平台（如 Weird Gloop MediaWiki）的新站点时，agent 必须手动完成策略创建——这是一个无 CLI 辅助的冗长过程。

本 design 基于三个已确认的 spec：
- `specs/explore-backend-detection/spec.md`：增强 explore 的后端检测能力
- `specs/bootstrap-strategy-cli/spec.md`：新增 bootstrap-strategy CLI 命令
- `specs/site-strategy-schema/spec.md`：新增可选 `backend` 字段

## Goals / Non-Goals

**Goals:**

1. 当 `explore` 遇到无策略的站点时，自动抓取样本页并检测后端类型（Weird Gloop MediaWiki 为首个支持目标）。
2. 检测到后端后，`explore` 输出应推荐可复用的已有策略，并提供具体的 `bootstrap-strategy` 命令。
3. 新增 `bootstrap-strategy` CLI 命令，能够从参考策略一键派生新策略并自动更新 `registry.json`。
4. 策略 schema 新增可选 `backend` 字段，用于标记后端家族关系，方便 registry 查询。

**Non-Goals:**

1. 不改变 `crawl` 的策略门控逻辑——crawl 仍然要求策略存在才能执行。
2. 不支持全自动静默策略创建——bootstrap 必须显式调用，agent 必须感知策略派生行为。
3. 不扩展除 Weird Gloop MediaWiki 之外的其他后端指纹——`configs/backend-signatures.json` 预留结构，但首期只填充一条数据。
4. 不修改 `findStrategy()` 的域名精确匹配策略——保持现有行为，后端检测仅在精确匹配失败时触发。
5. 不替代 agent 对派生策略的 review——bootstrap 生成的策略标记为 "Bootstrapped — review recommended"。

## Decisions

### Decision 1: 后端检测放在 explore 中而非 crawl 中

- **依据**: `strategy-guided-crawl/spec.md` 明确要求 crawl 必须拒绝无策略的执行请求。后端检测作为诊断行为，自然归属 explore。
- **影响**: explore 现在需要执行一次轻量 HTML 抓取（`scrapling-get` 获取 raw HTML），增加约 1-3 秒延迟。此延迟仅在无策略时发生。

### Decision 2: 独立 `configs/backend-signatures.json` 而非扩展 registry.json

- **依据**: registry.json 是轻量索引，职责是快速域名查询。后端指纹是跨站点的元数据，独立文件避免 registry.json 膨胀。
- **影响**: 新增一个配置文件；CLI 需要读取两个文件（registry.json + backend-signatures.json）才能完成检测。
- **结构**:
  ```json
  {
    "backends": [
      {
        "id": "weird-gloop-mediawiki-1.45",
        "label": "Weird Gloop MediaWiki 1.45.x",
        "detection": {
          "meta_generator": "MediaWiki",
          "dom_selector": "#mw-content-text",
          "url_patterns": ["/w/", "/wiki/"]
        },
        "reusable_strategies": [
          "vampire.survivors.wiki",
          "balatrowiki.org"
        ],
        "cleanup_profile_options": ["vampire-survivors", "balatro", "generic-mediawiki"],
        "notes": "Server-side rendered static HTML. scrapling-get sufficient."
      }
    ]
  }
  ```

### Decision 3: bootstrap-strategy 的字段适配规则

| 字段 | 行为 | 理由 |
|------|------|------|
| `domain` | 替换为目标 URL hostname | 核心标识 |
| `description` | 替换域名；尝试从页面 title 推断主题名 | 需要人工 review |
| `url_example` | 替换 hostname | 同后端共享路径结构 |
| `url_pattern` | 保持不变 | 同后端共享路径模式 |
| `extraction.selectors` | 复制 | 同后端共享 DOM 结构 |
| `extraction.image_handling` | 复制 | 同后端共享 |
| `extraction.cleanup` | 复制；可被 `--profile` 覆盖 | 可能需微调 |
| `engine_preference` | 复制 | 同后端共享引擎需求 |
| `protection_level` | 复制 | 同后端共享保护级别 |
| `anti_crawl_refs` | 复制 | 同后端共享反爬策略 |
| `structure.pages` | 整体复制，仅替换 `url_example` | 同后端共享页面结构 |

### Decision 4: 后端检测采用 AND 逻辑

- **依据**: 单一检测方法（如只匹配 `meta_generator`）可能导致误判（很多网站使用 MediaWiki）。
- **规则**: 若 backend signature 声明多个 detection 方法，则 ALL 必须同时匹配才算命中。
- **回退**: 检测未命中时 explore 保持现有策略缺口行为，不引入新错误路径。

### Decision 5: `backend` 字段为 advisory 而非 runtime key

- **依据**: 避免引入复杂的策略继承或运行时解析逻辑。`backend` 仅用于标记、查询和 bootstrap 参考。
- **影响**: `findStrategy()` 不读取 `backend` 字段；策略匹配仍然只依赖域名。

## Risks / Migration

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| **后端检测误判** | 中 | 高 | AND 联合检测（meta + DOM + URL pattern）；误判时 fallback 到现有策略缺口报告 |
| **bootstrap 策略质量不足** | 中 | 中 | 生成的策略标记 "Bootstrapped — review recommended"；agent 应在 crawl 前检查策略 |
| **explore 执行时间增加** | 低 | 低 | 仅无策略时触发；使用 `scrapling-get` 轻量请求 |
| **registry.json 写入冲突** | 低 | 中 | 写入前检查 domain 是否已存在；并发场景依赖文件锁（当前 CLI 为单进程，暂无并发风险） |
| **cleanup profile 名称漂移** | 低 | 低 | profile 名称由 `clean-mediawiki.sh` 内定义；bootstrap 只做字符串替换，不验证 profile 存在性 |

**迁移说明:**
- 现有策略文件无需修改（`backend` 是可选字段）。
- 建议在后续维护中为已有 Weird Gloop MediaWiki 策略（`vampire.survivors.wiki`、`balatrowiki.org`）补充 `backend` 字段，便于 registry 查询。
- CLI 帮助文本需要更新以展示新命令。
