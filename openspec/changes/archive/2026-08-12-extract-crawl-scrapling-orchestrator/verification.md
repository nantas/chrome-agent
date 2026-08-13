# Verification

## 全量测试

| 套件 | 命令 | 结果 |
|------|------|------|
| Python 单元 | `.venv/bin/python -m unittest discover -s tests` | 100 tests OK |
| Python 管线遗留 | `.venv/bin/python -m unittest discover -s scripts/pipeline/tests` | 51 tests OK |
| Node（全部 .test.mjs） | `node --test tests/*.test.mjs` | 全绿（crawl_scrapling 3 + pages-scope 2 + fetch-strategy-selector 12 + 其余） |
| CLI smoke | `node scripts/chrome-agent-cli.mjs --help` / `doctor` | 正常加载 |

## spec→code 映射

### `crawl-scrapling-orchestrator-is-a-seam-module`

| spec scenario | 实现位置 | 证据 |
|---------------|----------|------|
| orchestrator-extractable-and-importable | `scripts/lib/crawl_scrapling.mjs::runCrawlScrapling(ctx, opts, api)`；测试 `tests/crawl_scrapling.test.mjs` | 3 用例：preflight 失败路径、最小成功 traversal、无循环依赖。提取前函数内联 cli.mjs 不可 import 单测 → 提取后可 |
| crawl-output-byte-identical | 纯结构重构：函数体逐字搬迁，仅签名参数化 + 26 依赖改走 api.* | `crawl-scrapling-pages-scope` 与 `fetch-strategy-selector` 集成回归全绿（pages binding / buildScraplingExtractionArgs 调用不变） |
| api-bundle-built-once-in-cli | `scripts/chrome-agent-cli.mjs::runCrawl` 顶部 `const crawlApi = { fs, ...26 helpers }`；3 调用点（原 2202/2365/2369）传 `crawlApi` | grep 确认 0 个遗留位置参数调用；crawl_scrapling.mjs 不 import cli.mjs（循环依赖测试 GREEN） |

## 行为保真证据

- **函数体逐字搬迁**：381 行 body 仅做 (a) 签名 13 参数→ctx 对象、(b) 26 个 helper 引用加 `api.` 前缀、(c) fs.→api.fs。Python 正则替换，事后 grep 确认零遗留裸调用、零裸 fs。
- **集成回归**：`crawl-scrapling-pages-scope`（pages binding 顺序）+ `fetch-strategy-selector`（buildScraplingExtractionArgs 调用 + 无 hardcoded ai-targeted）全绿——这两组测试直接断言提取前的内部不变量，现仍成立。
- **运行时 smoke**：`chrome-agent-cli.mjs --help` 与 `doctor --check capabilities` 正常。

## 代码量

- `chrome-agent-cli.mjs`：4551 → 4185 行（−366）
- 新增 `scripts/lib/crawl_scrapling.mjs`：394 行（含 header + import path）
- 新增 `tests/crawl_scrapling.test.mjs`：3 行为注入用例
- 更新 2 个既有源码 grep 测试（pages-scope、fetch-strategy-selector）指向新模块位置

## C10 同步证据

- `cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs`（runtime 内容本 change 未变，副本已确认 IDENTICAL）
- `git rev-parse HEAD > ~/.agents/scripts/.chrome-agent-installed-hash`（归档 commit 后刷新至新 HEAD）
- `doctor --check capabilities`：全 `[durable] (checked)`，`next_action: none`
- 顺带闭合既有漂移（原 `8111a3f`）

## 归档前置检查

- [x] 全量测试绿
- [x] spec→code 映射完整
- [x] 行为保真（集成回归 + smoke）
- [x] C10 全局同步（runtime 副本 + hash）
- [x] doctor --check capabilities（C11）
