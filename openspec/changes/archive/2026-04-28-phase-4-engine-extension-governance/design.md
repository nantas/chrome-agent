# Design

## Context

Phase 1-3 完成了治理基础重建、5 个引擎契约冻结、策略库标准化。当前引擎生态的注册信息内联在 `engine-contracts/spec.md` 的多张表格中。添加新引擎需要同时修改注册表、选择映射、错误矩阵、smoke-check 清单——没有独立的注册索引、没有接入模板、没有优先级模型。

Phase 3 的策略库已经建立了 `registry.json` + spec 的双层模式，验证了 JSON 索引 + YAML frontmatter 的可行性。Phase 3 的 `anti-crawl-schema` 中的 `engine_sequence.purpose` 是一个简单枚举（primary/fallback/diagnostic），无法表达多维度的引擎优先级排序。

Phase 4 在 Phase 2（契约冻结）和 Phase 3（策略库标准化）的基础上，为引擎生态添加可扩展性治理。核心洞察来自 explore mode 讨论：引擎需要多维评分（执行效率、稳定性、适配性），并按加权公式推导优先级，同时允许站点策略和反爬策略进行上下文调制。

## Goals / Non-Goals

**Goals:**
1. 创建 `configs/engine-registry.json` 作为独立引擎注册索引（解耦自 `engine-contracts`）
2. 定义三维引擎特性评分模型（efficiency/stability/adaptability）和加权 `composite_score` 公式
3. 定义 `default_rank` 推导规则，体现 Scrapling-first 原则
4. 将 `anti-crawl-schema` 的 `engine_sequence` 迁移为 `engine_priority`（`purpose` → `rank`）
5. 为 `site-strategy-schema` 新增 optional `engine_preference` 字段
6. 定义 `extension-api` 作为新引擎接入的 artifact checklist、模板和治理规则
7. 创建 `scrapling-bulk-fetch-contract` 作为通过 extension-api 接入的示例引擎
8. 更新 AGENTS.md 中 engine-registry 状态和引擎扩展治理章节
9. 创建决策记录，更新总体规划文档

**Non-Goals:**
- 不实现运行时引擎自动选择——只定义数据模型（特性评分、rank），选择算法由 agent 决策
- 不实现引擎编排层（调度、并发、重试策略）
- 不修改任何引擎的工具实现
- 不新增除 `scrapling-bulk-fetch-contract` 以外的引擎契约
- 不修改 4 个现有站点策略文件（engine_preference 为 optional，无需强制填充）
- 不修改操作手册（docs/playbooks/）——优先级模型是数据层变更，操作流程不变

## Decisions

### Decision 1: `configs/engine-registry.json` 作为引擎注册索引

`configs/engine-registry.json` 作为独立的 JSON 索引文件，而非继续将引擎列表内联在 `engine-contracts/spec.md` 中。

```
Before (Phase 2):                      After (Phase 4):
─────────────────                      ─────────────────
engine-contracts/spec.md               engine-contracts/spec.md
  ├─ Registry table (inline)             ├─ Error matrix (kept)
  ├─ Selection mapping (inline)          ├─ Selection mapping (updated)
  ├─ Error matrix                       ├─ Compliance criteria (kept)
  ├─ Smoke-check inventory              ├─ Smoke-check inventory (updated)
  └─ Compliance criteria                 └─ → ref: configs/engine-registry.json
                                       configs/engine-registry.json ← NEW
                                         └─ engines: [{id, type, characteristics, 
                                              composite_score, default_rank, ...}]
```

**Rationale**: 继承 Phase 3 验证过的 `registry.json` 模式——JSON 索引适合快速机器扫描，规格（contract spec）是行为规范真源。`engine-contracts` 的表格模式在引擎数量增长时会越来越臃肿；解耦后 `engine-contracts` 聚焦于跨引擎关注点（错误矩阵、选择映射），`configs/engine-registry.json` 聚焦于引擎发现和排序。

选择 `configs/` 目录而非 `openspec/specs/`：`engine-registry.json` 是运行时配置数据（机器可查询的索引），不同于 spec（行为规范）。这遵循了 AGENTS.md 的目录治理规则——configs/ 存放工具与运行配置。

### Decision 2: 三维加权特性评分

引擎特性采用三个评分维度（efficiency, stability, adaptability），每个维度 0.00-1.00，通过加权公式推导 `composite_score`（0-100）：

```
composite_score = round((adaptability × 0.50 + stability × 0.30 + efficiency × 0.20) × 100)
```

权重设计逻辑：
- **adaptability (0.50) 最高**：引擎能处理多少种场景是核心竞争力。一个只能处理静态页面的引擎即使极快极稳也不足以应对复杂任务。
- **stability (0.30) 第二**：在已知目标场景中的可靠性。引擎不出错比引擎快更重要。
- **efficiency (0.20) 最低但非零**：速度有影响，但不应以牺牲能力和稳定性为代价。

`composite_score` 衡量引擎的"综合能力"，`default_rank` 控制"尝试顺序"。两者不同：stealthy-fetch 的 composite_score 可能高于 get（因为 adaptability 极高），但 default_rank 仍然是 get 排第一（Scrapling-first 原则强制 lighter engine 优先）。

### Decision 3: default_rank 的 Scrapling-first 强制执行

`default_rank` 不像 `composite_score` 那样纯粹由公式推导。它遵循额外的规则：

1. 所有 Scrapling 引擎（type: http, playwright, playwright_stealth, playwright_bulk）排在 CDP 引擎（type: cdp_managed, cdp_live）之前
2. Scrapling 家族内部按轻到重排序：get → fetch → stealthy-fetch
3. CDP 家族内部：chrome-devtools-mcp（诊断）排在 chrome-cdp（实时会话）之前
4. Bulk variants 放在其 non-bulk 对应引擎附近（在实现中，bulk-fetch 放在 fetch 和 stealthy-fetch 之间）

5 个现有引擎的 default_rank：
| Engine | Type | composite_score | default_rank |
|--------|------|-----------------|-------------|
| scrapling-get | http | 61 | 1 |
| scrapling-fetch | playwright | 66 | 2 |
| scrapling-stealthy-fetch | playwright_stealth | 79 | 3 |
| chrome-devtools-mcp | cdp_managed | 81 | 4 |
| chrome-cdp | cdp_live | 71 | 5 |

注意：虽然 chrome-devtools-mcp 的 composite_score (81) 高于 scrapling-get (61)，但 Scrapling-first 原则强制 get 的 default_rank 为 1。`composite_score` 是"能力评分"，`default_rank` 是"尝试顺序"，两者服务于不同目的。

**Rationale**: Scrapling-first 是框架的核心原则（参见 AGENTS.md），不应被纯粹的计算公式破坏。`default_rank` 是带有策略约束的排名，不是 raw composite_score 的排序。

### Decision 4: engine_priority 替代 engine_sequence

Phase 3 的 `engine_sequence` 使用 `purpose`（primary/fallback/diagnostic）表达角色。新的 `engine_priority` 使用 `rank`（integer, 1-based）表达执行顺序。

```
Before:                               After:
engine_sequence:                      engine_priority:
  - engine: scrapling-stealthy-fetch    - engine: scrapling-stealthy-fetch
    config: { solve_cloudflare: true }    rank: 1
    purpose: primary                      config: { solve_cloudflare: true }
  - engine: chrome-devtools-mcp         - engine: chrome-devtools-mcp
    purpose: diagnostic                   rank: 2
```

`rank` 是显式的整数排序，消除了 `purpose` 枚举的歧义（"fallback 和 diagnostic 谁先？"）。`rank` 值必须连续（1, 2, 3...），不允许跳跃。最少 1 个引擎。

**Migration impact**: `sites/anti-crawl/` 下 5 个策略文件的 frontmatter 需要更新。`default.md` 的默认链表述从隐式变为显式 rank。

**Rationale**: `purpose` 枚举（3 个值）无法表达"我要先试 engine A，如果失败试 engine B，再失败试 engine C"这种精确执行顺序。`rank` = integer 可以直接表达任意长度的优先级链，且可以作为 agent 的明确排序输入。

### Decision 5: engine_preference 作为 site-strategy 的 optional 字段

在 `site-strategy-schema` 中新增 `engine_preference`（optional）：

- **File level**: `engine_preference: { preferred: "<engine-id>", reason: "..." }`，应用于所有页面
- **Per-page level**: `structure.pages[].engine_preference`，覆盖文件级别设置

优先级链：`per-page preference > file-level preference > anti-crawl priority > engine default_rank`

**Rationale**: 不同站点/页面可能有不同的引擎偏好。例如 fanbox.cc 有 cookie 认证，chrome-cdp 更快；x.com 的公开推文不需要 stealthy-fetch 的开销。`engine_preference` 让站点策略能直接表达这种偏好，而不需要依赖反爬策略的匹配。

由于是 optional，现有 4 个站点策略文件无需立即填充此字段，向前兼容。新增站点时可以根据实际需求选择是否声明偏好。

### Decision 6: scrapling-bulk-fetch 作为示例扩展

选择 `scrapling-bulk-fetch` 而非 `scrapling-screenshot` 或 `scrapling-bulk-stealthy-fetch` 作为示例扩展。

理由：
- 已验证可用（双 URL 测试通过，example.com + httpbin.org）
- 支持 `session_id` 参数（session 复用能力）
- 输出格式与非批量版本一致，合同定义清晰
- 展示的是"能力维度扩展"（单 → 批量），而非"全新领域"（截图是不同维度），更贴近大多数扩展场景
- 复杂度适中——不会因为过重而失去示例的教学价值

同时，`scrapling-bulk-fetch` 的存在也为未来的 `scrapling-bulk-stealthy-fetch` 和 `scrapling-bulk-get` 提供了参照模式。

### Decision 7: 合约模板嵌入 extension-api spec

合同模板（`contract-template.md`）嵌入在 `extension-api/spec.md` 的 Requirement 中，而非独立文件。模板包含 `{{ }}` 占位符，开发者在创建新引擎时拷贝并填充。

**Rationale**: 模板是 spec 的一部分，不是独立的实现工件。嵌入 spec 中确保模板与 specification 要求同步演进。开发者通过 openspec change 流程使用模板——模板的修改也需要通过 openspec change，防止 drift。

### Decision 8: 引擎生命周期三态

| State | Condition | Transition |
|-------|-----------|------------|
| `draft` | 新引擎接入，合约 spec 已创建但未经验证 | → `frozen` (验证通过) |
| `frozen` | 合约已验证，被策略引用 | → `superseded` (被新引擎替代) |
| `superseded` | 已被新引擎或新能力替代 | 保留历史引用，不再更新 |

状态存储在 `configs/engine-registry.json` 的 `status` 字段中。

**Rationale**: 简单的三态模型足以覆盖当前需求。相比两态（只有 frozen/superseded），`draft` 状态允许引擎在正式发布前有验证窗口。这避免了"要么完全冻结，要么不存在"的二选一困境。

## Risks / Migration

### 风险 1: anti-crawl 策略文件的 engine_sequence → engine_priority 迁移

**风险**: 5 个 anti-crawl 策略文件的 YAML frontmatter 需要修改字段名和结构。如果遗漏某个文件或迁移错误，会导致策略文件与 schema spec 不一致。

**缓解措施**:
- 在 tasks 中列出明确的迁移清单（5 个文件 + registry.json）
- 迁移后执行逐文件验证（frontmatter 字段完整性检查）
- `anti-crawl-schema` spec 明确声明 `engine_sequence` 为废弃字段

### 风险 2: engine-contracts spec MODIFIED 的向前兼容

**风险**: `engine-contracts/spec.md` 的 MODIFIED 变更删除内联 engine 列表和 compliance status 子 scenario。如果其他 spec 或文档直接引用了这些被删除的内容，会导致引用断裂。

**缓解措施**:
- 被删除的 engine 列表由 `configs/engine-registry.json` 接管
- 被删除的 compliance status 子 scenario 由 registry 的 `status` 字段接管
- MODIFIED spec 保留了所有功能性需求（错误矩阵、选择映射、合规标准），只改变了数据位置

### 风险 3: engine-registry.json 与 contract specs 的漂移

**风险**: `configs/engine-registry.json` 和引擎 contract spec 是两份独立文件。手动维护可能导致 characteristic scores、default_rank 等数据不一致。

**缓解措施**:
- AGENTS.md 声明 contract spec 为权威来源（类似 Phase 3 的 frontmatter vs registry.json 模式）
- registry.json 的 `contract_spec` 字段建立显式链接
- 未来可添加验证脚本，但 v1 不强制

### 风险 4: composite_score 公式的 subjectiveness

**风险**: efficiency/stability/adaptability 的评分带有主观判断。不同评分者可能给出不同的值，影响 default_rank 的可比性。

**缓解措施**:
- 每个特性维度包含 `note` 字段（评分理由），强制评分者解释其判断
- 评分通过 openspec change 流程讨论和确认
- 公式本身（权重分配）在 spec 中明确定义，不可随意修改
- 这不是精确科学——评分的有用性在于提供比较框架，而非绝对精确度

### 风险 5: site-strategy 的 engine_preference 不被填充

**风险**: `engine_preference` 是 optional 字段。现有的 4 个站点策略文件可能长期不被填充，使这个字段成为一个"理论存在"的特性而没有实际使用。

**缓解措施**:
- 这不是真正的风险——optional 字段本身就允许"不使用"。字段存在的目的是为未来站点提供更细粒度的控制。
- Phase 4 的设计目标是为决策提供数据基础，不强制所有现有站点都必须声明偏好。
- 默认行为（无 preference → 走 default_rank 或 anti-crawl priority）已经合理。
