# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-guided-crawl`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 crawl 默认输出从 HTML 改为 Markdown，新增 --no-markdown、--merge、--concurrency 参数

## 规范真源声明

- 本文件是 `strategy-guided-crawl` 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/strategy-guided-crawl/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Default Markdown output

The `crawl` command SHALL default to producing Markdown output for each crawled page.

#### Scenario: Default Markdown mode

- **WHEN** `crawl <url>` is invoked without `--no-markdown`
- **THEN** after strategy-guided traversal completes, the command SHALL invoke the shared Markdown conversion pipeline
- **AND** each successfully visited page SHALL produce a `.md` file via `scrapling extract <fetcher> <url> <path>.md --ai-targeted`
- **AND** intermediate `.html` files SHALL be cleaned up after conversion

#### Scenario: HTML fallback mode

- **WHEN** `crawl <url> --no-markdown` is invoked
- **THEN** the command SHALL skip Phase 2 Markdown conversion
- **AND** it SHALL retain intermediate `.html` files as the final output
- **AND** the behavior SHALL match the pre-change crawl implementation

### Requirement: Optional merged output

The `crawl` command SHALL support merging all per-page Markdown files into a single document.

#### Scenario: Merge flag

- **WHEN** `crawl <url> --merge` is invoked
- **THEN** after Phase 2 conversion completes, the command SHALL concatenate all `.md` files into `crawl-output.md`
- **AND** the merged document SHALL include a table of contents derived from each page's first `#` heading

### Requirement: Concurrent Markdown conversion

The `crawl` command SHALL support concurrent Phase 2 Markdown conversion.

#### Scenario: Default concurrency

- **WHEN** Phase 2 conversion runs without an explicit `--concurrency` value
- **THEN** the default concurrency SHALL be 5 concurrent Scrapling invocations

#### Scenario: Custom concurrency

- **WHEN** `crawl <url> --concurrency 10` is invoked
- **THEN** Phase 2 conversion SHALL run with up to 10 concurrent Scrapling invocations

### Requirement: Phase 2 partial failure semantics

The `crawl` command SHALL report `partial_success` when Phase 2 Markdown conversion has failures.

#### Scenario: Conversion partial failure

- **WHEN** Phase 1 traversal succeeds but some Phase 2 conversions fail
- **THEN** the final result SHALL be `partial_success`
- **AND** the manifest SHALL record failed URLs in `phase2.failed_urls`
- **AND** successfully converted `.md` files SHALL remain available

## MODIFIED Requirements

### Requirement: Partial failure semantics

The crawl capability SHALL support partial completion when some pages succeed and others fail.

#### Scenario: Mixed page outcomes (Phase 1)

- **WHEN** a crawl retrieves some pages successfully but encounters blocked, rate-limited, or failed pages during traversal
- **THEN** the command SHALL return `partial_success`
- **AND** it SHALL identify the successful outputs and the pages or stages that failed

#### Scenario: Phase 2 conversion failures

- **WHEN** Phase 1 completes successfully but Phase 2 Markdown conversion has failures
- **THEN** the command SHALL return `partial_success`
- **AND** the successful `.md` files SHALL remain as usable artifacts
- **AND** the manifest SHALL identify which URLs failed conversion

## Requirements from change: split-fetch-convert-phases

### ADDED

#### Requirement: scrapling-fetch-phase
Scrapling crawl 路径 SHALL 支持 `--phase fetch`。

`--phase fetch` 在 Scrapling 路径的行为：
1. 执行 discovery + traversal，获取页面列表（与当前一致）
2. 对每个页面执行 Scrapling CLI fetch（保存 HTML 到 `.cache/scrapling/<domain>/<slug>.html`）
3. 同时写入 `<slug>.meta.json` 记录元数据
4. 已有缓存的页面默认跳过
5. 不执行 Markdown 转换

##### Scenario: scrapling-fetch-phase
- **WHEN** 执行 `chrome-agent crawl https://example.com --phase fetch`
- **THEN** SHALL 下载 HTML 并保存到 `.cache/scrapling/example.com/`
- **AND** 每个页面 SHALL 生成 `.html` + `.meta.json` 文件对
- **AND** SHALL NOT 执行 Markdown 转换或写入 runDir

#### Requirement: scrapling-convert-phase
Scrapling crawl 路径 SHALL 支持 `--phase convert`。

`--phase convert` 在 Scrapling 路径的行为：
1. 加载 manifest（需要 `--from-manifest`）
2. 遍历 manifest 中的 URL
3. 从 `.cache/scrapling/<domain>/<slug>.html` 读取 HTML
4. 通过 Scrapling CLI `--ai-targeted file://` 或 `htmlToMarkdown()` fallback 执行转换
5. 写入 .md 到 runDir
6. 执行链接 relativize

##### Scenario: scrapling-convert-phase
- **WHEN** 执行 `chrome-agent crawl https://example.com --phase convert --from-manifest <path>`
- **THEN** SHALL 从缓存读取 HTML
- **AND** SHALL NOT 发起任何 HTTP 请求
- **AND** SHALL 将 Markdown 输出到 runDir

#### Requirement: unified-cli-phase-semantics
`chrome-agent crawl` 的 `--phase` 参数 SHALL 对 MediaWiki API 路径和 Scrapling 路径具有一致的语义：

| `--phase` | MediaWiki API 路径 | Scrapling 路径 |
|-----------|-------------------|---------------|
| `discover` | allpages/homepage discovery | Scrapling first-level link discovery |
| `fetch` | API parse + 缓存写入 | Scrapling download + 缓存写入 |
| `convert` | 缓存读取 + HTML→MD 转换 | 缓存读取 + HTML→MD 转换 |
| `assemble` | 索引生成 + 链接修复 | 链接修复 + 合并（如启用） |
| `all` | discover → fetch → convert | discover → fetch → convert |

##### Scenario: consistent-phase-semantics
- **WHEN** 用户执行 `--phase convert` 对任意站点
- **THEN** 行为 SHALL 为读取缓存 → 转换 → 输出 Markdown（无论 MediaWiki 还是 Scrapling 路径）

### MODIFIED

#### Requirement: keep-html-semantics
`--keep-html` flag 的语义 SHALL 变更：

原行为：保留 runDir 中的 HTML 中间文件。
新行为：已废弃。HTML 持久化由 `--phase fetch` + 缓存层统一处理。

当 `--keep-html` 与 `--phase convert` 或 `--phase all` 同时使用时，SHALL 输出警告 `"--keep-html is deprecated; HTML is now persisted via --phase fetch cache"`
但 SHALL NOT 阻断执行。

##### Scenario: keep-html-deprecation-warning
- **WHEN** 执行 `chrome-agent crawl <url> --keep-html`
- **THEN** SHALL 输出弃用警告
- **AND** 仍继续执行（向后兼容）

#### Requirement: no-markdown-alignment
`--no-markdown` flag SHALL 保持现有行为（跳过 Markdown 转换），但同时 SHALL 输出提示建议使用 `--phase fetch` 作为推荐的 HTML-only 工作流。

##### Scenario: no-markdown-suggestion
- **WHEN** 执行 `chrome-agent crawl <url> --no-markdown`
- **THEN** SHALL 输出 `"Tip: Use --phase fetch for persistent caching of raw content"`
- **AND** 正常执行（保存 HTML 到 runDir，不转换）
