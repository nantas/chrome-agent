# Tasks

## 1. Python 管线变更

- [x] 1.1 `--phase discover` 值注册
  - 在 `cli.py` 的 `_add_pipeline_args()` 中，将 `discover` 加入 `--phase` 的 `choices`
  - 覆盖 spec: `pipeline-cli-entry` → `phase-discover-value`
  - 验证: `python3 -m scripts.mediawiki_api_extract pipeline --help` 显示 `discover` 选项

- [x] 1.2 `build_discovery_summary()` 实现
  - 在 `orchestrate.py` 中新增 `build_discovery_summary(manifest, strategy, rate_limit_config)` 函数
  - 产出格式符合 `discovery-summary-schema` spec 全部字段
  - API homepage 路径：从 `api.homepage.categories` 交叉 manifest 页面统计
  - API allpages 路径：从 manifest `target_directory` 分组统计
  - 计算 `estimated_time_minutes`（考虑 rate_limit_config）
  - 覆盖 spec: `pipeline-cli-entry` → `discovery-summary-generation`；`discovery-summary-schema` → 全部 requirements
  - 验证: 对 bindingofisaacrebirth.wiki.gg 执行 `--phase discover --discovery homepage`，检查 `discovery_summary.json` 字段完整性

- [x] 1.3 discovery-only 执行分支
  - 在 `run_pipeline()` 中，当 `--phase discover` 时：运行 discovery → 生成 manifest + summary → 初始化 resume state → 退出
  - 不进入 Phase B（extraction）和 Phase C（assembly）
  - 覆盖 spec: `pipeline-cli-entry` → `phase-discover-value`、`phase-discover-with-resume`
  - 验证: `--phase discover` 输出目录只有 `page_manifest.json` + `discovery_summary.json`，无 `.md` 文件

- [x] 1.4 from-manifest 加载支持
  - 当 `--from-manifest` 传入时，`run_pipeline()` 加载已有 manifest 而非运行 discovery
  - 支持 `--phase all`（extraction + assembly）和 `--phase extract`（仅 extraction）
  - 覆盖 spec: `pipeline-cli-entry` → `chrome-agent-cli-fix` (Scenario: cli-mjs-from-manifest-route)
  - 验证: 先用 `--phase discover` 产出 manifest，再用 `--phase all` + 同 manifest 恢复执行

## 2. CLI (chrome-agent-cli.mjs) 变更

--disable-wip [x] 2.1 `--discovery-only` 参数
  - 在 `runCrawl()` opts 中新增 `discoveryOnly` 布尔参数
  - API 路径：route 到 Python 管线 `--phase discover`
  - Scrapling 路径：实现 `runScraplingDiscoveryOnly()` 函数——fetch main page，提取 links_to selector 匹配的链接，分组统计，产出 discovery_summary.json
  - 覆盖 spec: `strategy-guided-crawl` → `discovery-only-mode`
  - 验证: `chrome-agent crawl <url> --discovery-only --format json` 产出 `discovery_summary.json`

- [x] 2.2 `--from-manifest` 参数
  - 在 `runCrawl()` opts 中新增 `fromManifest` 字符串参数
  - API 路径：传递 manifest 路径给 Python 管线（已有行为，确保 `--phase all` 读取已有 manifest）
  - Scrapling 路径：加载 manifest 的 `visited` URLs 作为 traversal queue，跳过 entry-point discovery
  - 覆盖 spec: `strategy-guided-crawl` → `from-manifest-resume`
  - 验证: `chrome-agent crawl <url> --from-manifest <path> --format json` 从已有 manifest 恢复执行

- [x] 2.3 `--yes` / `--no-confirm` 参数
  - 在 `runCrawl()` opts 中新增 `yes` 布尔参数
  - 写入 result JSON: `confirmation_bypassed: true/false`
  - CLI 自身行为不变（不因 `--yes` 改变执行路径）
  - 覆盖 spec: `strategy-guided-crawl` → `yes-no-confirm-flag`
  - 验证: result JSON 包含 `confirmation_bypassed` 字段

- [x] 2.4 `--exclude-category` 参数
  - 在 `runCrawl()` opts 中新增 `excludeCategory` 字符串数组参数
  - API 路径：合并到 Python 管线的 `--exclude-category` 参数（已有支持）
  - Scrapling 路径：在 from-manifest 恢复后过滤 visited URLs（按 manifest 中的 category 信息）
  - 覆盖 spec: `strategy-guided-crawl` → `exclude-category-runtime-filter`
  - 验证: `--exclude-category Music --exclude-category Modding` 排除指定分类

- [x] 2.5 Scrapling 首页链接发现
  - 实现 `runScraplingDiscoveryOnly()`:
    1. 执行 Scrapling preflight
    2. fetch main page（使用 selectFetcher）
    3. 提取 HTML 中匹配 strategy `links_to[*].selector` 的链接
    4. 按 `structure.pages[].url_pattern` 分组
    5. 构建 `discovery_summary.json`（`discovery_method: "first_level_links"`, caveats）
  - 覆盖 spec: `strategy-guided-crawl` → `scrapling-first-level-discovery`
  - 验证: 对非 API 站点执行 `--discovery-only`，产出含 caveats 的 summary

- [x] 2.6 from-manifest 排除过滤
  - Scrapling 路径：加载 manifest 后，根据 manifest 中记录的 category 信息过滤 excluded categories
  - API 路径：Python 管线在 `run_pipeline()` 中处理（已支持 `--exclude-category`）
  - 覆盖 spec: `strategy-guided-crawl` → `from-manifest-with-exclusions`
  - 验证: `--from-manifest <path> --exclude-category Bosses` 跳过 Bosses 分类页面

## 3. SKILL.md 变更

- [x] 3.1 Crawl Confirmation Gate 章节
  - 在 SKILL.md 的 `## Intent Routing` 下，`## Agent Gate` 之后新增 `## Crawl Confirmation Gate` 章节
  - 内容涵盖: gate 触发条件、两阶段流、tree 构建、ask_user 选项、`--yes` 绕过、错误处理
  - 同步更新 `~/.agents/skills/chrome-agent/SKILL.md` 和 `skills/chrome-agent/SKILL.md`
  - 覆盖 spec: `global-workflow-skill` → `crawl-gate-skill-section`
  - 验证: 读取 SKILL.md 确认包含完整 gate 章节

- [x] 3.2 Gate 触发逻辑
  - 在 Intent Routing 中，当意图为 `crawl` 且无 `--yes` 时，触发 Crawl Confirmation Gate
  - 执行 `chrome-agent crawl <url> --discovery-only --format json`
  - 读取 `discovery_summary.json`
  - 覆盖 spec: `global-workflow-skill` → `crawl-confirmation-gate-interception`；`crawl-confirmation-gate` → `discovery-summary-consumption`
  - 验证: SKILL 调用 `crawl <url>` 时先执行 discovery-only

- [x] 3.3 树状图生成
  - 从 `discovery_summary.categories` 构建目录树
  - 显示：📁 目录名 (页数)、📄 index.md（如有）、3-5 样本页、⚠️ excluded、caveats、warnings、est. time
  - 覆盖 spec: `crawl-confirmation-gate` → `tree-diagram-generation`
  - 验证: 对 BOI wiki 的 summary 生成树状图，含 18 个分类 + excluded + misc

- [x] 3.4 ask_user 确认流
  - `type: "preview"` 问题显示树状图
  - 选项: proceed、adjust (多选排除分类)、cancel
  - adjust 后重建树状图并重新确认
  - 覆盖 spec: `crawl-confirmation-gate` → `user-confirmation-ask`
  - 验证: 完整执行 proceed / adjust + re-confirm / cancel 三条路径

## 4. AGENTS.md 变更

- [x] 4.1 Crawl Confirmation Gate 治理规则段
  - 在 AGENTS.md Governance Rules 区域新增「Crawl Confirmation Gate」章节
  - 内容: gate 触发条件、两阶段流、`--yes` 绕过、禁止行为（不得在未确认前执行 extraction）
  - 覆盖 spec: `global-workflow-skill` → `crawl-gate-skill-section`（文档引用）
  - 验证: 读取 AGENTS.md 确认包含完整 gate 治理规则

## 5. 集成验证

- [x] 5.1 API 管线端到端
  - 场景: `crawl --discovery-only` → 生成 manifest + summary → `crawl --from-manifest` → 产出完整 Markdown
  - 验证目标: bindingofisaacrebirth.wiki.gg（homepage discovery）
  - 覆盖 spec: `crawl-confirmation-gate` → `extraction-execution`

- [ ] 5.2 Scrapling 管线端到端
  - 场景: `crawl --discovery-only` → 生成 summary（含 caveats）→ `crawl --from-manifest` → 产出完整 Markdown
  - 验证目标: 有 strategy 的非 API 站点

- [x] 5.3 `--yes` 绕过
  - 场景: `crawl <url> --yes` → 不触发闸门，完整原子执行
  - 覆盖 spec: `crawl-confirmation-gate` → `yes-flag-bypass`

- [x] 5.4 `--exclude-category` 过滤
  - 场景: `crawl <url> --from-manifest <path> --exclude-category Music` → Music 分类页面不出现
  - 覆盖 spec: `strategy-guided-crawl` → `exclude-category-runtime-filter`

- [ ] 5.5 错误处理
  - 场景: discovery 部分失败（如 3/18 分类超时）→ summary 含 warnings → 闸门呈现警告但不阻断
  - 场景: discovery 完全失败 → 闸门阻断，呈现失败信息
  - 覆盖 spec: `crawl-confirmation-gate` → `confirmation-gate-error-handling`

- [x] 5.6 向后兼容
  - 场景: `crawl <url>` 不带任何新参数 → 行为完全不变
  - 覆盖: 现有 behavior 不受影响

## 6. 测试

- [x] 6.1 Python 管线单元测试
  - `build_discovery_summary()` 对 homepage / allpages manifest 的输出验证
  - `--phase discover` 出口验证（无 extraction artifacts）

- [x] 6.2 CLI 集成测试
  - 扩展 `tests/chrome-agent-runtime.test.mjs`：
  - `--discovery-only` 产出 `discovery_summary.json`
  - `--from-manifest` 恢复执行
  - `--yes` 写入 `confirmation_bypassed`
  - `--exclude-category` 合并逻辑
