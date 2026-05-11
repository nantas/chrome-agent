# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 `cloakbrowser-fetch-contract` spec 已创建：定义输入参数、stealth 能力、错误契约、smoke-check 场景
- [x] 1.2 `engine-registry` spec 已更新：新增 cloakbrowser-fetch 条目（playwright_stealth, rank 4, draft），scrapling-stealthy-fetch 标记为 superseded
- [x] 1.3 `engine-contracts` spec 已更新：escalation chain 加入 cloakbrowser-fetch（rank 4），错误矩阵新增 binary/challenge/license 类别
- [x] 1.4 `scrapling-stealthy-fetch-contract` spec 已标记 superseded：保留供历史引用，迁移指向 cloakbrowser-fetch
- [x] 1.5 确认 cloakbrowser 已在 macOS 开发机通过 pip install 安装，二进制已下载成功

## 2. 核心实现任务

### 2.1 引擎注册与配置

- [x] 2.1.1 在 `configs/engine-registry.json` 中新增 `cloakbrowser-fetch` 条目
  - 特性评分：efficiency=0.25, stability=0.55, adaptability=0.80
  - composite_score=60, default_rank=4, type=playwright_stealth, status=draft
  - best_for: high_protection, turnstile_protected, recaptcha_protected, tls_fingerprint_detected, dynamic_content, dynamic_list, spa
  - 验证：`openspec status --change "integrate-cloakbrowser-engine"` 确认变更一致性
- [x] 2.1.2 更新 `scrapling-stealthy-fetch` 条目的状态为 `superseded`
  - 保留原始记录，仅修改 status 字段
  - 验证：registry JSON 语法正确，superseded 引擎仍可通过查询发现

### 2.2 Playbook 与文档更新

- [x] 2.2.1 更新 `docs/playbooks/fallback-escalation.md`
  - escalation chain 图更新：rank 4 从 scrapling-stealthy-fetch 改为 cloakbrowser-fetch
  - 新增 CloakBrowser 的 preflight 检查步骤（pip install check + binary existence check）
  - 新增从 scrapling-fetch 升级到 cloakbrowser-fetch 的触发条件
  - 保留 obscura-fetch (rank 2) 的完整描述
  - 验证：playbook 中所有引擎引用可追溯到 `configs/engine-registry.json`
- [x] 2.2.2 更新 `AGENTS.md` 中的引擎选择规则
  - 更新 4. Engine Selection 章节，CloakBrowser 替代 scrapling-stealthy-fetch
  - 在 8. Reference Index 中新增 CloakBrowser 参考条目
  - 验证：grep 检查 AGENTS.md 不再引用 scrapling-stealthy-fetch 为活跃引擎

### 2.3 CloakBrowser 调用包装

- [x] 2.3.1 创建 CloakBrowser preflight 检查脚本 `scripts/cloakbrowser-preflight.sh`
  - 检查 `pip show cloakbrowser` 返回值
  - 检查 `python3 -m cloakbrowser info` 输出中 `installed: True`
  - 若缺失，输出安装提示并退出非零
  - 验证：在已安装环境运行返回 0，未安装环境（若模拟）返回非 0
- [x] 2.3.2 实现 CloakBrowser 页面抓取器函数（可集成到现有 crawl/scrape 管道）
  - 封装为可调用函数：`cloakbrowser_fetch(url, **kwargs)`
  - 默认 headless=True, wait_until='domcontentloaded'
  - 自动处理 Turnstile 挑战：等待页面从 challenge 状态导航到真实内容
  - 返回结构化结果：`{title, url, html, content, success, error, timing}`
  - 超时处理：30s 默认，可配置
  - 验证：对 wiki.supercombo.gg 调用返回 20,000+ 字符内容，非挑战页面
- [x] 2.3.3 将 CloakBrowser 注入现有 escalation chain
  - 在 scrapling-fetch 失败后自动升级到 cloakbrowser-fetch
  - 升级触发条件：空 body + 非空白页（TLS 检测嫌疑），或已知 protection_level=high
  - 验证：mock 场景下从 scrapling-fetch 失败正确跳转到 cloakbrowser-fetch

### 2.4 安装文档

- [x] 2.4.1 更新 `docs/setup/` 中的环境配置文档，添加 CloakBrowser 安装步骤
  - `pip install cloakbrowser`
  - 首次调用自动下载 ~200MB patched Chromium binary
  - 缓存路径：`~/.cloakbrowser/chromium-{version}/`
  - macOS 首次使用：需处理 Gatekeeper（`xattr -cr ~/.cloakbrowser/chromium-*/Chromium.app`）
  - 建议生产环境使用 Linux（Chromium 146）而非 macOS（Chromium 145）

## 3. 收敛与验证准备

- [x] 3.1 Smoke-check 清单：
  - [x] `scrapingbee.com/blog` — TLS 指纹绕过验证（140 links, 5011 chars, 6.92s）
  - [x] `wiki.supercombo.gg` — Turnstile 自动解析验证（23,021 chars, "SuperCombo Wiki" title, 14.42s）
  - [x] reCAPTCHA v3 demo — 评分验证（⏭️ SKIP：需要特定测试页面，代码逻辑已支持）
  - [x] `example.com` — 基础功能基线（title="Example Domain", 129 chars, 2.11s）
- [x] 3.2 已知限制需在 verification 中记录：
  - macOS Chromium 145 vs Linux Chromium 146 版本差异
  - nowsecure.nl 在 macOS headless 下未通过
  - Binary 专有许可证对分发的影响
  - 443 MB 内存占用（含 Playwright node 进程）
  - reCAPTCHA v3 demo 未在本次 smoke-check 中验证（需要特定测试页面）

## 4. 验证与回写收敛

- [x] 4.1 基于实现结果生成 `verification.md`
  - 覆盖所有 spec requirement 的验证结果
  - 记录每个 smoke-check 的通过/失败状态
  - 记录已知限制和未覆盖场景
- [x] 4.2 基于 verification.md 结论生成 `writeback.md`
  - 回写目标：AGENTS.md, configs/engine-registry.json, docs/playbooks/fallback-escalation.md
  - 状态变更：cloakbrowser-fetch 的 draft 状态是否需要更新
- [x] 4.3 执行 writeback.md 中定义的回写目标
  - 更新 AGENTS.md 中的引擎选择规则
  - 更新 docs/playbooks/fallback-escalation.md
  - 更新 configs/engine-registry.json
