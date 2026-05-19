# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-guided-crawl`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: Scrapling 路径支持 `--phase fetch`（保存 HTML 到缓存）和 `--phase convert`（从缓存读取转换）；统一两条路径的 CLI 语义；`--keep-html` 语义变更。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: scrapling-fetch-phase
Scrapling crawl 路径 SHALL 支持 `--phase fetch`。

`--phase fetch` 在 Scrapling 路径的行为：
1. 执行 discovery + traversal，获取页面列表（与当前一致）
2. 对每个页面执行 Scrapling CLI fetch（保存 HTML 到 `.cache/scrapling/<domain>/<slug>.html`）
3. 同时写入 `<slug>.meta.json` 记录元数据
4. 已有缓存的页面默认跳过
5. 不执行 Markdown 转换

#### Scenario: scrapling-fetch-phase
- **WHEN** 执行 `chrome-agent crawl https://example.com --phase fetch`
- **THEN** SHALL 下载 HTML 并保存到 `.cache/scrapling/example.com/`
- **AND** 每个页面 SHALL 生成 `.html` + `.meta.json` 文件对
- **AND** SHALL NOT 执行 Markdown 转换或写入 runDir

### Requirement: scrapling-convert-phase
Scrapling crawl 路径 SHALL 支持 `--phase convert`。

`--phase convert` 在 Scrapling 路径的行为：
1. 加载 manifest（需要 `--from-manifest`）
2. 遍历 manifest 中的 URL
3. 从 `.cache/scrapling/<domain>/<slug>.html` 读取 HTML
4. 通过 Scrapling CLI `--ai-targeted file://` 或 `htmlToMarkdown()` fallback 执行转换
5. 写入 .md 到 runDir
6. 执行链接 relativize

#### Scenario: scrapling-convert-phase
- **WHEN** 执行 `chrome-agent crawl https://example.com --phase convert --from-manifest <path>`
- **THEN** SHALL 从缓存读取 HTML
- **AND** SHALL NOT 发起任何 HTTP 请求
- **AND** SHALL 将 Markdown 输出到 runDir

### Requirement: unified-cli-phase-semantics
`chrome-agent crawl` 的 `--phase` 参数 SHALL 对 MediaWiki API 路径和 Scrapling 路径具有一致的语义：

| `--phase` | MediaWiki API 路径 | Scrapling 路径 |
|-----------|-------------------|---------------|
| `discover` | allpages/homepage discovery | Scrapling first-level link discovery |
| `fetch` | API parse + 缓存写入 | Scrapling download + 缓存写入 |
| `convert` | 缓存读取 + HTML→MD 转换 | 缓存读取 + HTML→MD 转换 |
| `assemble` | 索引生成 + 链接修复 | 链接修复 + 合并（如启用） |
| `all` | discover → fetch → convert | discover → fetch → convert |

#### Scenario: consistent-phase-semantics
- **WHEN** 用户执行 `--phase convert` 对任意站点
- **THEN** 行为 SHALL 为读取缓存 → 转换 → 输出 Markdown（无论 MediaWiki 还是 Scrapling 路径）

## MODIFIED Requirements

### Requirement: keep-html-semantics
`--keep-html` flag 的语义 SHALL 变更：

原行为：保留 runDir 中的 HTML 中间文件。
新行为：已废弃。HTML 持久化由 `--phase fetch` + 缓存层统一处理。

当 `--keep-html` 与 `--phase convert` 或 `--phase all` 同时使用时，SHALL 输出警告 `"--keep-html is deprecated; HTML is now persisted via --phase fetch cache"`
但 SHALL NOT 阻断执行。

#### Scenario: keep-html-deprecation-warning
- **WHEN** 执行 `chrome-agent crawl <url> --keep-html`
- **THEN** SHALL 输出弃用警告
- **AND** 仍继续执行（向后兼容）

### Requirement: no-markdown-alignment
`--no-markdown` flag SHALL 保持现有行为（跳过 Markdown 转换），但同时 SHALL 输出提示建议使用 `--phase fetch` 作为推荐的 HTML-only 工作流。

#### Scenario: no-markdown-suggestion
- **WHEN** 执行 `chrome-agent crawl <url> --no-markdown`
- **THEN** SHALL 输出 `"Tip: Use --phase fetch for persistent caching of raw content"`
- **AND** 正常执行（保存 HTML 到 runDir，不转换）
