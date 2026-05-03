# Tasks

## 1. 验证准备

- [x] 1.1 确认验证前置条件
  - [x] Obscura 源码仓库已克隆（`/Volumes/Shuttle/projects/agentic/obscura`）
  - [x] Rust 工具链可用（`rustc 1.93.1`）
  - [x] Scrapling CLI 可用（`$HOME/.cache/chrome-agent-scrapling/bin/scrapling`，stealthy-fetch 子命令存在）
  - [x] 目标 web 站点可达（无代理/网络限制）
  - 验证方式：逐一运行依赖检查命令

- [x] 1.2 确认验证范围（引用 `design.md` → Decisions）
  - [x] 并行抓取：`obscura scrape` 对 3 个混合场景 URL 的并行执行
  - [x] Stealth 对比：`wiki.supercombo.gg`（CF challenge）+ `video.dmm.co.jp`（JS 动态）+ `nowsecure.nl` / `scrapingpass.com`
  - 引用：`design.md` Decision 2、Decision 3

## 2. 并行抓取验证

- [x] 2.1 构建 `obscura-worker` 二进制
  - 命令：`cd /Volumes/Shuttle/projects/agentic/obscura && cargo build --release`
  - 产物：`target/release/obscura-worker`
  - 安装：复制到 `$HOME/.cache/chrome-agent-obscura/bin/`（与主二进制同目录）
  - 验证：`obscura-worker` 存在且可执行，`obscura scrape` 成功调用 worker
  - 耗时：~15 分钟
  - 注：`--features stealth` 因 `boring-sys2` 链接错误未使用；worker 无 stealth 依赖，功能正常

- [x] 2.2 执行并行抓取测试
  - 命令：
    ```bash
    obscura scrape \
      "https://httpbin.org/html" \
      "https://quotes.toscrape.com" \
      "https://news.ycombinator.com" \
      --concurrency 3 \
      --eval "document.querySelector('h1')?.innerText || document.title" \
      --format json
    ```
  - 验证结果：
    1. ✅ 3/3 URL 成功返回，无 `error` 字段
    2. ✅ 内容正确（httpbin: Moby-Dick; quotes: Quotes to Scrape; HN: Hacker News）
    3. ✅ 总时间 1,994 ms << 串行总和 ~4,400 ms
    4. ✅ 无 worker 进程残留
  - 输出：`reports/2026-05-02-obscura-parallel-test.md`

- [x] 2.3 串行对比基线
  - 对 3 个 URL 顺序执行 `obscura fetch --dump html`
  - 耗时记录：httpbin 1,143 ms; quotes 1,924 ms; HN 1,334 ms
  - 并行 vs 串行：1,994 ms vs ~4,401 ms，速度提升 ~2.2×

## 3. Stealth 对比验证

- [x] 3.1 选择并确认测试站点可达
  - ✅ 必测 1：`https://wiki.supercombo.gg/w/Street_Fighter_6/A.K.I.` — 返回 Cloudflare "Just a moment..." 挑战页（curl GET 验证）
  - ✅ 必测 2：`https://video.dmm.co.jp/av/content/?id=mkmp00718` — HTTP 200，text/html
  - ✅ 补充 1：`https://nowsecure.nl` — HTTP 200，含 CF Turnstile 元素（`.cf-turnstile`, `challenges.cloudflare.com`）
  - ❌ 补充 2：`https://www.scrapingpass.com/test-website` — HTTP 404，无可替代测试路径
  - ✅ Fallback：`https://www.scrapingbee.com/blog/` — HTTP 200，text/html
  - 最终测试站点：wiki.supercombo.gg、nowsecure.nl、video.dmm.co.jp、scrapingbee.com/blog

- [x] 3.2 对每个测试站点执行 A/B 对比
  - 测试站点：wiki.supercombo.gg、nowsecure.nl、video.dmm.co.jp、scrapingbee.com/blog
  - 对比矩阵：Obscura plain / Obscura stealth / Scrapling stealthy-fetch
  - 关键发现：
    - wiki.supercombo.gg：三者均收到 CF "Just a moment..." 挑战页，无绕过
    - nowsecure.nl：Obscura 双模式均超时（JS 执行错误 `Cannot read properties of null (reading 'replace')`）；Scrapling 成功获取 178KB 完整内容
    - video.dmm.co.jp：三者均收到年龄认证页；Obscura 伴随 JS 错误
    - scrapingbee.com/blog：Obscura 双模式仅获取 CSS 骨架（空 `<body>`），无动态内容；Scrapling 成功获取 215KB 完整博客内容

- [x] 3.3 产出 stealth 对比报告
  - 文件：`reports/2026-05-02-obscura-stealth-comparison.md`
  - 内容：4 站点 × 3 模式对比矩阵、原始输出大小、关键观察、结论分级
  - 结论：⚠️ CONDITIONAL PASS — Obscura 在 heavy JS / SPA 场景下出现 hang、空 body、stealth 模式无效果

## 4. 结论收敛

- [x] 4.1 统合两份验证报告，判断 `obscura-fetch` 是否应升级为 `frozen`
  - 并行验证：✅ PASS（速度提升 ~2.2×，无 worker 泄漏）
  - Stealth 验证：⚠️ CONDITIONAL（heavy JS hang、SPA 空 body、stealth 模式无效）
  - 结论：**维持 `draft`** — stealth 验证暴露重大限制，不满足 `frozen` 升级条件
  - 触发动作：更新 `obscura-fetch-contract` spec 修正边界描述，记录已知限制

- [x] 4.2 根据验证结论创建或更新以下产出
  - ✅ 报告文件：`reports/2026-05-02-obscura-parallel-test.md` + `reports/2026-05-02-obscura-stealth-comparison.md`
  - ✅ 决策记录：`docs/decisions/2026-05-02-obscura-verification-outcome.md`（记录维持 `draft` 的决定）
  - ✅ Spec 修正：`openspec/specs/obscura-fetch-contract/spec.md` 新增 Known Limitations 章节
  - ⏭️ Status 更新：维持 `draft`，不修改 `configs/engine-registry.json`
  - ⏭️ AGENTS.md 更新：不涉及

- [x] 4.3 清理临时构建产物
  - ✅ `obscura-worker` 已安装至 `$HOME/.cache/chrome-agent-obscura/bin/obscura-worker`
  - ✅ 已清理所有 `/tmp/*` 临时测试 HTML 文件
