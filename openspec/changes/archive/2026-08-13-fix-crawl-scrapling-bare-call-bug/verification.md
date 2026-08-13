# Verification

## 验证结论

**PASS — 所有 spec scenario 已被可执行证据覆盖；缺陷已修复；无回归；C10 未触发。**

缺陷 `scripts/lib/crawl_scrapling.mjs:328` 的裸调用已修复为 `api.collectMarkdownArtifacts(runDir)`。两个新测试（静态纪律检查 + `markdown:true` 回归）均通过；通过临时回退修复证实二者都能真实捕获该缺陷。原有测试 + 同级 crawl 测试全绿（19/19）。

## Spec-to-Implementation Coverage

规范真源：`specs/fetch/spec.md` → MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`（5 个 scenario）。

| Scenario | 实现位置 | 证据 |
| --- | --- | --- |
| `orchestrator-extractable-and-importable` | `scripts/lib/crawl_scrapling.mjs:15`（`runCrawlScrapling(ctx, opts, api)`） | `tests/crawl_scrapling.test.mjs` 既有注入式测试（stub `api`，preflight failure + minimal traversal 用例） |
| `crawl-output-byte-identical` | 纯结构重构（commit `04a35fb`）的既有不变量；本 change 未改控制流/产出格式 | 既有 "minimal successful traversal" 用例验证 manifest 结构不变；本 change diff 仅 1 行调用点 + 测试 |
| `api-bundle-built-once-in-cli` | `scripts/chrome-agent-cli.mjs:2130`（`crawlApi` bundle 构造一次，3 个 dispatch 点传入） | "no circular import" 既有用例（模块不 import cli.mjs）+ 本 change 未改 bundle 定义 |
| `all-bundled-helpers-called-via-api-prefix`（新增） | `scripts/lib/crawl_scrapling.mjs:328`（已修复为 `api.collectMarkdownArtifacts`） | `tests/crawl_scrapling.test.mjs` 新增 "all bundled helpers are called via the api. prefix" 静态纪律检查用例；RED→GREEN 已证实（回退修复即失败，见下） |
| `markdown-true-branch-produces-artifacts-not-reference-error`（新增） | `scripts/lib/crawl_scrapling.mjs:327-328`（`if (markdown)` → `api.collectMarkdownArtifacts(runDir)`） | `tests/crawl_scrapling.test.mjs` 新增 "markdown:true (default) path collects markdown artifacts and does not throw ReferenceError" 用例；断言 sentinel artifact 进入 `result.artifacts` |

## Task-to-Evidence Coverage

| Task | 证据 |
| --- | --- |
| 1.1–1.3 准备 | spec delta 已写（5 scenario）；`collectMarkdownArtifacts` 已在 `crawlApi` bundle（`cli.mjs:2136`）；防御性扫描脚本输出 28 key × ~40 调用点，唯一裸调用 = line 328 |
| 2.1.A RED（纪律检查） | 用例加入后首次运行：RED，violations = `[{key:'collectMarkdownArtifacts', line:328}]`（精确捕获缺陷） |
| 2.2.A GREEN（修复） | `crawl_scrapling.mjs:328` 改为 `...api.collectMarkdownArtifacts(runDir)`；重跑纪律检查：通过 |
| 2.1.B/2.2.B（markdown:true 回归） | 新用例通过；**回退验证**：临时把 line 328 改回裸调用 → 该用例抛 `ReferenceError` 失败 + 纪律检查失败；恢复修复 → 5/5 绿。证明两测试都是真实回归守卫 |
| 3.1 全量 crawl 测试 | `node --test tests/crawl_scrapling.test.mjs tests/crawl-scrapling-pages-scope.test.mjs tests/fetch-strategy-selector.test.mjs` → **19/19 pass** |
| 3.2 烟测 | 按 design D2 由 `markdown:true` stub 测试覆盖（该用例驱动 runCrawlScrapling 到达 final-artifact 块并断言不抛 + artifact 就位）；真实 crawl 需 network + engine preflight，对 1 字符修复不增加置信，跳过 |
| 3.3 markdown:false 字节不变 | 原有 2 个 `markdown:false` 用例仍在 19/19 内绿 |
| 3.4 C10 不触发 | `git diff --name-only` = `scripts/lib/crawl_scrapling.mjs` + `tests/crawl_scrapling.test.mjs`；无 tracked files（runtime/cli/SKILL） |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 修复点 | `scripts/lib/crawl_scrapling.mjs:328` | scenario `markdown-true-branch-produces-artifacts-not-reference-error` / task 2.2.A |
| 静态纪律检查测试 | `tests/crawl_scrapling.test.mjs`（"all bundled helpers are called via the api. prefix"） | scenario `all-bundled-helpers-called-via-api-prefix` / task 2.1.A |
| markdown:true 回归测试 | `tests/crawl_scrapling.test.mjs`（"markdown:true (default) path …"） | scenario `markdown-true-branch-produces-artifacts-not-reference-error` / task 2.1.B |
| 测试运行输出 | `node --test tests/crawl_scrapling.test.mjs …` → pass 19 / fail 0 | task 3.1 |
| 回退验证 | 临时 sed 回退 → 2 测试失败（含 ReferenceError）；恢复 → 5/5 绿 | task 2.1.B 回归守卫真实性 |
| C10 不触发证据 | `git diff --name-only`（无 tracked files） | task 3.4 |

## 缺口与阻塞项

**无缺口，无阻塞。**

- 所有 5 个 spec scenario 有可执行证据覆盖。
- J3 测试完备检查：修改的代码模块 `scripts/lib/crawl_scrapling.mjs` 已有对应测试文件 `tests/crawl_scrapling.test.mjs`，且本次新增 2 个用例 → 无 CRITICAL/WARNING。
- 静态纪律检查的已知 ceiling（`ponytail:` 注释已标注）：string literal 内的 bundled key 未剥离——但当前模块无 bundled key 出现在字符串字面量内；dotted-base 规则顺带覆盖了 `console.log` / 文件名 `.log` 的误报。若将来有 bundled key 进入字符串，需细化。
- C10 全局同步不触发（已核实 tracked files 清单）。
