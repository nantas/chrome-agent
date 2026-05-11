# Obscura 爬取管线交汇分析

> 2026-05-11 | 基于代码审查 + 基准测试

## 1. 核心发现：chrome-agent 内部有两条独立的管线

```
┌──────────────────────────────────────────────────────────────────┐
│            chrome-agent 内容获取管线全景图                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────┐                               │
│  │ 管线 A: 基于 Scrapling 的爬取  │                               │
│  │ 适用: 无 API 的 HTML 站点     │                               │
│  ├──────────────────────────────┤                               │
│  │ crawl/scrape → strategy      │                               │
│  │ → Scrapling get/fetch 串行   │                               │
│  │ → Markdown 转换               │                               │
│  │                              │                               │
│  │ 产出: 完整 HTML → Markdown   │                               │
│  │ 瓶颈: 串行，每页 1-3s        │                               │
│  └──────────────────────────────┘                               │
│                                                                  │
│  ┌──────────────────────────────┐                               │
│  │ 管线 B: MediaWiki API 提取   │                               │
│  │ 适用: wiki.gg, Fandom,      │                               │
│  │       Weird Gloop 等         │                               │
│  ├──────────────────────────────┤                               │
│  │ crawl → strategy             │                               │
│  │ → has api.platform=mediawiki?│                               │
│  │ → Yes → 路由到 API pipeline │                               │
│  │                              │                               │
│  │ Phase A: API 发现             │                               │
│  │  (category_members/allpages) │                               │
│  │ Phase B: API 内容获取         │                               │
│  │  (action=parse / prop=       │                               │
│  │   revisions)                 │                               │
│  │ Phase C: 结构化后处理          │                               │
│  │  (template_map, taxonomy,    │                               │
│  │   图片过滤, link_resolver)    │                               │
│  │                              │                               │
│  │ 产出: 结构化 Markdown + FM   │                               │
│  │ 效率: API 本身已高效          │                               │
│  └──────────────────────────────┘                               │
│                                                                  │
│                 ★ Obscura 能替换哪些？ ★                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 2. Obscura `scrape` 的产出与业务需求的 Gap

```
Obscura scrape 产出:
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ url         │     │ title        │     │ eval (可选)  │
│ time_ms     │     │ worker       │     │ error (可选) │
└─────────────┘     └──────────────┘     └──────────────┘

wiki.gg 业务流需要 (以 slaythespire.wiki.gg 为例):
┌──────────────────────────────────────────────────────────┐
│ ● 完整 HTML（含 infobox, 模板展开）                       │
│ ● 结构化 frontmatter（name, cost, type, rarity, color）  │
│ ● 图片URL 归一化（thumb → full res）                     │
│ ● 分类系统（taxonomy 到 /Cards/{color}/{rarity}.md）    │
│ ● 链接解析（WikiLinks → 相对路径 Markdown）              │
│ ● 模板处理（{{C|name}} → [[name]], {{KW|x}} → [[x]]）  │
│ ● 速率控制（tier: strict, batch_delay: 800ms）          │
└──────────────────────────────────────────────────────────┘

                       ╔═════════════════╗
                       ║   业务Gap: 巨大  ║
                       ╚═════════════════╝
```

## 3. 为什么 Obscura 无法替代 MediaWiki API 管线

```
原因 A: Cloudflare Challenge
  slaythespire.wiki.gg 的 HTML 页面 (/wiki/Slay_the_Spire_2:*)
  返回 403 cf-mitigated——Obscura 的浏览器也逃不掉
  
  API 端点 (/api.php?action=parse) 则无挑战

原因 B: 结构化数据
  API 返回: parsed HTML + wikitext + categories + templates
  → 可做 template_map, taxonomy mapping, image filtering
  
  Obscura 返回: 已渲染的 DOM → 失去模板上下文
  → "Bash" 是 1-cost 的攻击 → 无法从文本推断 rarity/color/type

原因 C: 后处理管线
  Phase C 的 list_page_assembler 按 taxonomy:
  → /Cards/Red/Rare.md, /Relics/Boss.md
  
  Obscura 没有也不应该参与这种 Data Engineering 管线
```

## 4. 两条管线的"数据交汇点"在哪里

```
                  ┌──────────────────┐
                  │ 用户输入一个 URL  │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ 读 strategy       │
                  │ (frontmatter)    │
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ has api.platform │      │ 无 API           │
    │ = mediawiki?     │      │ (纯 HTML 站点)   │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ API Pipeline     │      │ Obscura/Scrapling│
    │ (Python)         │      │ (CLI)            │
    │                  │      │                  │
    │ action=parse     │      │ Phase 1: 遍历    │
    │ Phase A→B→C      │      │  (发现URLs)      │
    │ 结构化Markdown   │      │ Phase 2: 取内容  │
    └──────────────────┘      │  (HTML→Markdown) │
                ▲             └──────────────────┘
                │                       ▲
                │                       │
         API 失败时                   ★ Obscura 能替换的
         fallback 到这里               是这段区域

         "交汇"只发生在 fallback 路径
         不是 mainline 替换
```

## 5. 重新定义 Obscura 的真实价值

### Obscura 能彻底替换的（Tier 1-2 站点）

```
quotes.toscrape.com       ← 静态 JS 渲染，无 API
books.toscrape.com        ← 同上
news.ycombinator.com      ← 动态列表，无 API
普通博客/文档站            ← 无 API

当前: Scrapling 串行 crawl（8页 8-17s）
替换: Scrapling get 遍历 + Obscura 并行 fetch
结果: 8页 < 3.3s，加速比 2.4-5.3×
```

### Obscura 只能当 fallback 的（Tier 3 站点）

```
slaythespire.wiki.gg      ← MediaWiki API
vampire.survivors.wiki   ← MediaWiki API
balatrowiki.org           ← MediaWiki API

当前: MediaWiki API pipeline（高效、结构化）
Obscura 角色: API 不可用时作 fallback
  (比当前 Scrapling fallback 快 2-5×)
```

### Obscura 不适用的（Tier 4 站点）

```
Cloudflare 高保护站       ← 需要 stealth TLS
reCAPTCHA 保护站          ← 需要浏览器指纹绕过
```

## 6. Obscura `scrape` 的"替身困境"

现在最棘手的问题是：**Obscura `scrape` 不返回页面内容。**

| 子命令 | 返回内容 | 能否替代 crawl？ |
|--------|---------|----------------|
| `obscura fetch url --dump html` | ✅ 完整 HTML | 但单 URL，非批量 |
| `obscura scrape <urls...>` | ❌ 仅元数据 | 不能，无内容 |
| `obscura serve --workers N` | ✅ worker pool，可并发 fetch | 需要上游编排 |

所以如果要用 Obscura 做批量内容获取，有两条路径：

```
路径 1: 用 serve 模式（推荐用于批量内容获取）
  ┌──────────────────────────────────────┐
  │ obscura serve --workers 8            │
  │ → 启动 8 个 worker 进程              │
  │ → 每个 worker 是完整 CDP endpoint    │
  │ → 可并行下发 obscura fetch --dump   │
  │    html 到不同 worker                │
  └──────────────────────────────────────┘

  优势: 返回完整 HTML，可走现有 Markdown 管线
  代价: 需要自己编排 worker 分配

路径 2: 分两步走（当前 scrape 模式）
  ┌──────────────────────────────────────┐
  │ Step 1: obscura scrape --eval        │
  │         "document.body.innerHTML"    │
  │  → 用 eval 获取完整 HTML             │
  │  → 但 worker 返回纯文本，结构丢失    │
  └──────────────────────────────────────┘
  
  风险: eval 返回 innerHTML 可能很大
        100 页 × 50KB → 5MB JSON，parsing 可能超时/溢出
```

## 7. 总结：真正的整合策略

```
┌──────────────────────────────────────────────────────────────┐
│              推荐整合策略（基于实际能力边界）                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Tier 1-2 站点（无 API 的 HTML 站点）                        │
│  ├─ 替换方案: ✅ Obscura serve workers + 并行 fetch          │
│  ├─ 加速比:   2-5×                                           │
│  └─ 风险:     需实现 serve 模式的 worker pool 编排            │
│                                                              │
│  Tier 3 站点（MediaWiki API 站点）                            │
│  ├─ 替换方案: ❌ 不能替换 API pipeline                       │
│  ├─ Fallback: ✅ Obscura 可替代 Scrapling fallback（加速~3×）│
│  └─ 条件:     需处理 Cloudflare Challenge                    │
│                                                              │
│  Tier 4 站点（高保护）                                        │
│  └─ 替换方案: ❌ CloakBrowser 仍为权威                       │
│                                                              │
│  ★ 架构启示:                                                 │
│  两条管线 (API / browser) 应保持独立                          │
│  Obscura 的价值在 browser 管线的并行加速                      │
│  不要尝试用 browser 管线覆盖 API 管线的语义                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 8. 下步行动建议

| 优先级 | 行动 | 理由 |
|--------|------|------|
| P0 | 验证 `obscura serve --workers N` + 并发 `fetch` 是否稳定 | 这是替代 crawl 的最可行路径 |
| P1 | 调研 Obscura 上游是否愿意 PR 支持 `scrape --dump html` | 如有，整合路径大幅简化 |
| P2 | 升级 preflight v0.1.2 | 已有 worker binary，立即可做 |
| P3 | 在 engine-registry 区分两条管线 | 明确 API vs browser 的职责边界 |
