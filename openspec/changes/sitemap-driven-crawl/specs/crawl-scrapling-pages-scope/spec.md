# Specification Delta

## Capability 对齐（已确认）

- Capability: `crawl-scrapling-pages-scope`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 修复 `runCrawlScrapling` 函数体内 `pages` 变量作用域 bug。`pages` 定义于外层 `runCrawl()`（line 2018），被 `runCrawlScrapling`（独立 `async function`）体内 4 处引用但未绑定，导致 `ReferenceError`。修复方案：函数体顶部添加 `const pages = doc?.structure?.pages ?? []`（与姊妹函数 `runCrawlScraplingDiscovery` line 2241 一致）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: runCrawlScrapling-pages-binding

`runCrawlScrapling` (`scripts/chrome-agent-cli.mjs`) SHALL 在函数体内显式绑定 `pages` 变量，所有函数体内对 `pages` 的引用 SHALL 解析为该局部绑定，不得依赖调用方作用域的标识符穿透。

实现方式：在函数体顶部（`opts` 解构之前或之后，line 2315 附近）添加：

```javascript
const pages = doc?.structure?.pages ?? [];
```

`doc` 已是函数参数，无需修改函数签名或调用点。

#### Scenario: pages-is-defined-after-binding

- **WHEN** `runCrawlScrapling` 被调用且 `doc.structure.pages` 为非空数组
- **THEN** 函数体内 `pages.find()` 解析为 `doc.structure.pages` 的浅拷贝引用
- **AND** 不抛出 `ReferenceError: pages is not defined`

#### Scenario: pages-empty-on-missing-structure

- **WHEN** `runCrawlScrapling` 被调用且 `doc.structure.pages` 为 `undefined` 或 `null`
- **THEN** `pages` 解析为 `[]`
- **AND** 函数体内的 `pages.find(...)` 返回 `undefined`（不抛异常）

#### Scenario: selector-bfs-crawl-succeeds

- **WHEN** 对已 freeze 的非 MediaWiki 站点（如 `www.leagueofgamemakers.com`）执行 `chrome-agent crawl --max-pages 3 --yes`
- **THEN** 遍历不抛 `ReferenceError`
- **AND** `result` 不为 `failure`
- **AND** at least 1 page is fetched and converted

#### Scenario: anti-pattern-disallowed-global

- **WHEN** 实现本 requirement
- **THEN** 不得将 `pages` 声明为全局变量（`globalThis.pages` / 模块级 `let pages`）
- **AND** 不得使用 `typeof pages !== 'undefined' ? pages : []` 等防御性写法掩盖绑定缺失

### Requirement: scrapling-crawl-fallback-regression-test

`tests/` 下 SHALL 新增针对 scrapling crawl fallback 路径的回归测试（`node:test`），覆盖：

1. **`runCrawlScrapling` 可独立调用**：构造最小 `strategy` + `doc`（含 `structure.pages`）+ `opts` 输入，断言函数能进入 traversal 循环且不抛 `ReferenceError`
2. **pages 解析正确**：断言函数体内 `pages` 解析为 `doc.structure.pages`（非 `undefined`）
3. **端到端 smoke**：对已 freeze 的非 MediaWiki 策略站点执行 `chrome-agent crawl --max-pages N --yes`，断言 `result != failure`

#### Scenario: unit-test-no-reference-error

- **WHEN** 运行 `node --test tests/crawl-scrapling-pages-scope.test.mjs`
- **THEN** 测试用例中调用 `runCrawlScrapling` 不抛异常
- **AND** 断言 `pages` 绑定值等于 `doc.structure.pages`

#### Scenario: live-smoke-existing-non-mediawiki-strategy

- **WHEN** 执行 `chrome-agent crawl <已 freeze 的非 MediaWiki 站点> --max-pages 3 --yes --format json`
- **THEN** `result` 不为 `failure`
- **AND** `summary` 不含 `is not defined`

## ADDED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_

## Verification Plan

1. `node --test tests/crawl-scrapling-pages-scope.test.mjs` 全绿
2. Live smoke: 对非 MediaWiki 站点执行 crawl 不抛 ReferenceError
3. 作用域审查: `grep -n "pages\.find\|pages\.filter\|pages\.map" scripts/chrome-agent-cli.mjs` 确认所有引用均在函数作用域内有绑定
