# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-strategy-selector`
- 来源: `proposal.md` / 用户已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认采用单一新增 capability `fetch-strategy-selector`，范围覆盖 `fetch` 命令（`runFetch()`）与 `crawl` 命令的提取循环（一次性修复所有内容获取路径的同类 `--ai-targeted` 硬编码缺陷）。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: strategy-content-selector-passthrough

当内容获取后端（`fetch` 命令的 `runFetch()` 或 `crawl` 命令的提取循环）使用 `scrapling-get` fetcher 将 HTML 转换为 Markdown 时，系统 SHALL 从匹配的站点策略读取 `extraction.selectors.content` 字段；当该字段存在且非空时，系统 SHALL 通过 scrapling 的 `-s <selector>` 参数传递该选择器，而不是使用 `--ai-targeted` 启发式。

此要求适用于以下 scrapling 调用点：
- `runFetch()`（`scripts/chrome-agent-cli.mjs` fetch 命令路径）
- crawl 提取循环的每页 scrapling 调用（`scripts/chrome-agent-cli.mjs` crawl 命令路径）
- crawl 预取 HTML 经由 `file://` 的 scrapling 转换点

`mediawiki-api` fetcher 路径不在此要求范围内（其参数传递机制独立，经 `strategy.path`）。

#### Scenario: fetch-with-strategy-content-selector

- **WHEN** 运行 `chrome-agent fetch <url>` 且 `<url>` 匹配一个声明了 `extraction.selectors.content: "div[class*='@container/reader-content']"` 的策略
- **AND** 该策略的 fetcher 解析为 `scrapling-get`
- **THEN** 系统 SHALL 调用 scrapling 并传入 `-s "div[class*='@container/reader-content']"`
- **AND** 系统 SHALL NOT 同时传入 `--ai-targeted`
- **AND** 提取出的 Markdown SHALL 包含该选择器命中的正文内容（含页内 `<h1>`），而非导航栏

#### Scenario: crawl-with-strategy-content-selector

- **WHEN** 运行 `chrome-agent crawl <url>` 且遍历到的页面匹配一个声明了 `extraction.selectors.content` 的策略
- **AND** 该页面使用 `scrapling-get` fetcher
- **THEN** crawl 提取循环 SHALL 对该页面调用 scrapling 并传入 `-s <selector>`
- **AND** 预取 HTML 经 `file://` 转换的路径 SHALL 同样使用 `-s <selector>`

#### Scenario: selector-source-is-strategy-not-hardcoded

- **WHEN** 构造 scrapling extraArgs 时
- **THEN** 选择器值 SHALL 来源于策略的 `extraction.selectors.content` 字段
- **AND** 系统 SHALL NOT 在代码中硬编码任何站点特定的选择器值
- **AND** 未匹配任何策略的 URL SHALL 不传入 `-s`（交由回退要求处理）

### Requirement: ai-targeted-fallback-when-no-selector

当匹配的策略未声明 `extraction.selectors.content`（字段缺失或为空字符串），或未匹配到任何策略时，系统 SHALL 回退至 scrapling 的 `--ai-targeted` 启发式模式，以保持与当前行为向后兼容。

回退 SHALL 是确定性的：仅当"无可用 content 选择器"这一条件成立时触发，不依赖提取结果质量。

#### Scenario: fetch-strategy-without-content-selector

- **WHEN** 运行 `chrome-agent fetch <url>` 且匹配的策略未声明 `extraction.selectors.content`
- **THEN** 系统 SHALL 调用 scrapling 并传入 `--ai-targeted`
- **AND** 系统 SHALL NOT 传入 `-s` 参数
- **AND** 行为 SHALL 与本 change 实施前完全一致（向后兼容）

#### Scenario: fetch-no-strategy-match

- **WHEN** 运行 `chrome-agent fetch <url>` 且 `<url>` 未匹配任何站点策略
- **THEN** 系统 SHALL 调用 scrapling 并传入 `--ai-targeted`
- **AND** 系统 SHALL NOT 传入 `-s` 参数

### Requirement: shared-arg-builder-helper

系统 SHALL 提供一个共享的 extraArgs 构造 helper（如 `buildScraplingExtractionArgs(strategy, matchingPage)`），统一为 `fetch` 与 `crawl` 路径构造 scrapling 参数。该 helper SHALL：

- 当 fetcher 为 `mediawiki-api` 时返回 `[strategy.path]`（保持既有行为）
- 当 fetcher 为 `scrapling-get` 类且策略存在 `extraction.selectors.content` 时返回 `["-s", selector]`
- 否则返回 `["--ai-targeted"]`

`fetch` 与 `crawl` 路径 SHALL 共同调用此 helper，禁止各自重新实现选择器判断逻辑。

#### Scenario: helper-encapsulates-selector-decision

- **WHEN** `runFetch()` 与 crawl 提取循环需要构造 scrapling extraArgs
- **THEN** 两者 SHALL 调用同一 helper 函数
- **AND** 该 helper 的返回值 SHALL 完全决定 scrapling 收到的参数
- **AND** 新增任何站点策略无需修改 `fetch` 或 `crawl` 的调用代码

#### Scenario: helper-preserves-mediawiki-api-path

- **WHEN** fetcher 为 `mediawiki-api`
- **THEN** helper SHALL 返回 `[strategy.path]`
- **AND** SHALL 不受 `extraction.selectors.content` 是否声明的影响
- **AND** mediawiki-api 路径行为 SHALL 与本 change 实施前一致

### Requirement: selector-injection-safety

系统 SHALL 将策略提供的 CSS 选择器作为 scrapling CLI 的独立参数传递，禁止将选择器值与其它参数拼接为单一 shell 字符串。选择器值 SHALL 未经 shell 解释直接作为 argv 元素传入子进程，以防止选择器内容（可能含特殊字符如 `[`、`*`、`'`）引发注入或参数解析错误。

#### Scenario: selector-with-special-characters

- **WHEN** 策略声明 `extraction.selectors.content: "div[class*='@container/reader-content']"`
- **THEN** 该字符串 SHALL 作为单一 argv 元素传递给 scrapling 子进程（紧跟 `-s` 之后）
- **AND** SHALL NOT 经由 shell 字符串拼接（如 `sh -c "scrapling ... -s $SELECTOR"`）
- **AND** scrapling SHALL 正确解析该选择器并返回匹配元素

## 非目标（显式排除）

以下行为明确不在本 capability 范围内，记录以防 scope creep：

- **`extraction.selectors.title` 与 `cleanup` 字段的消费**：本 capability 仅消费 `content` 选择器；title/cleanup 的 pipeline 消费留作后续 change。
- **`scrape` 与 `explore` 路径的同类修复**：这些路径（`chrome-agent-cli.mjs:2669/3450`）共享相同缺陷模式，但本 change 不修复；共享 helper 的引入使其可在后续 change 中低成本启用。
- **提取质量的自适应回退**：本 capability 的 `--ai-targeted` 回退是"无选择器"触发的确定性回退，不基于提取结果质量（如字节数阈值）做动态切换。质量驱动的回退属另一独立设计，不在本次范围。
- **选择器有效性校验**：本 capability 不在运行时校验选择器语法或命中率；无效选择器的诊断由站点策略维护流程（explore / 样本质量检测）负责。
