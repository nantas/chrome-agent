# Verification

## 验证结论

实现 **完全覆盖** 所有 spec requirements 和核心实现任务（Section 2 全部 `[x]`）。Section 3/4 为运行时验证任务，需对 BOI 站点执行 crawl 后确认，不阻塞代码审查归档。

无 CRITICAL 问题。1 个 WARNING（docstring 过时）。1 个 SUGGESTION（minor pattern）。

## Spec-to-Implementation Coverage

### mw-category-aliases (new)

| Requirement | Scenario | Status | Evidence |
|-------------|----------|--------|----------|
| `mw-category-aliases-field` | `alias-based-mw-category-match` | ✅ | `page_assigner.py:262` — alias 遍历 + 匹配；BOI 策略 L73 `mw_category_aliases: ["Collectibles", ...]` |
| `mw-category-aliases-field` | `no-aliases-backward-compat` | ✅ | `page_assigner.py:221` — `c.get("mw_category_aliases", [])` 缺失时返回空列表 |
| `alias-priority-resolution` | `name-and-alias-both-match` | ✅ | `page_assigner.py:248-252` — direct name match 先检查，命中即 break |
| `alias-usage-in-priority-chain` | `alias-priority-overrides-lower-name-match` | ✅ | `page_assigner.py:246` — `for priority_name in assignment_priority` 按 priority 顺序遍历 |

### page-assignment (modified)

| Requirement | Scenario | Status | Evidence |
|-------------|----------|--------|----------|
| `source-category-assignment` | `list-page-source-category-match` | ✅ | `page_assigner.py:130-167` — `_apply_source_category_assignments` 遍历 `assignment_priority`，不限制类型 |
| `source-category-assignment` | `priority-order-for-source-categories` | ✅ | `page_assigner.py:152` — `for cat_name in assignment_priority` + `break` |
| `source-category-assignment` | `category-page-source-category-backward-compat` | ✅ | 同上逻辑——所有类型通过 `assignment_priority` 统一匹配 |
| `page-categories-fallback` | `page-categories-mw-fallback` | ✅ | `page_assigner.py:228-234` — `page_cat_dir_map` 从 `taxonomy.page_categories` 构建 |
| `page-categories-fallback` | `page-categories-sub-path-resolution` | ✅ | `page_assigner.py:233` — `cat_path.split("/")[0]` 取顶层 segment |
| `mw-category-matching-with-aliases` | `alias-match-in-step-3` | ✅ | `page_assigner.py:261-276` — alias match 在 direct match 之后检查 |
| `assignment-method-tracking` | `assignment-method-values` | ✅ | `page_assigner.py:165` `"source_category_match"`；`page_assigner.py:254/269` `"mw_category_match"` |
| ~~REMOVED~~ `category-page-member-only` | — | ✅ | grep 确认 `_apply_category_page_member_assignments` 和 `"category_page_member"` 零残留 |

### pipeline-cli-entry (modified)

| Requirement | Scenario | Status | Evidence |
|-------------|----------|--------|----------|
| `crawl-output-directory` | `custom-output-directory` | ✅ | `chrome-agent-cli.mjs:1998-1999` — `if (outputDir) { runDir = path.resolve(outputDir) }` |
| `crawl-output-directory` | `no-output-flag-default-behavior` | ✅ | L1997 先 `buildRunPaths`，L1998 条件覆盖——无 `--output` 时不覆盖 |
| `crawl-output-directory` | `output-path-for-mediawiki-api-pipeline` | ✅ | `chrome-agent-cli.mjs:2089` — `"--output", runDir` 透传到 Python pipeline |
| `output-flag-parsing` | `output-flag-separated` | ✅ | `chrome-agent-cli.mjs:281-284` |
| `output-flag-parsing` | `output-flag-equals` | ✅ | `chrome-agent-cli.mjs:286-288` |
| `output-flag-parsing` | `output-flag-absent` | ✅ | `chrome-agent-cli.mjs:108` — `let outputDir = null` |

### pipeline-convert-phase (modified)

| Requirement | Scenario | Status | Evidence |
|-------------|----------|--------|----------|
| `incremental-page-write` | `page-written-immediately-after-conversion` | ✅ | `convert.py:296-300` — `os.makedirs` + `open(filepath).write(result["content"])` |
| `incremental-page-write` | `directory-auto-created` | ✅ | `convert.py:298` — `os.makedirs(os.path.dirname(filepath), exist_ok=True)` |
| `incremental-page-write` | `conversion-result-still-in-memory` | ✅ | `convert.py:288` — `results[title] = result` 先于写文件；`extraction_results.json` 仍在末尾写 |
| `skip-already-converted-pages` | `resume-skip-converted-page` | ✅ | `convert.py:255-266` — 检查 `title in completed_pages_set` + `os.path.exists(filepath)` |
| `skip-already-converted-pages` | `force-reconvert-without-resume` | ✅ | `convert.py:243` — `state = load_state(...) if resume_enabled else None` |
| `conversion-output-format` | `output-content-integrity` | ✅ | 写入内容来自 `convert_single_page()` 返回的 `result["content"]`，与 Assembly 写入同一数据 |

### pipeline-resume (modified)

| Requirement | Scenario | Status | Evidence |
|-------------|----------|--------|----------|
| `incremental-state-update-during-convert` | `state-updated-per-page` | ✅ | `convert.py:305` — `completed_pages_set.add(title)` 每页执行 |
| `incremental-state-update-during-convert` | `state-persistence-on-interrupt` | ✅ | `convert.py:307-311` — 每 50 页 flush；`convert.py:321-322` 最终 flush |
| `convert-resume-skip-completed` | `resume-convert-partial` | ✅ | `convert.py:255-266` |
| `convert-resume-skip-completed` | `resume-file-missing-reconvert` | ✅ | `convert.py:258` — `if os.path.exists(filepath)` 检查文件存在性 |
| `state-flush-interval` | `periodic-flush` | ✅ | `convert.py:239,306-311` — `flush_interval = 50` |

## Task-to-Evidence Coverage

| Task | Status | Evidence |
|------|--------|----------|
| 1.1 确认 capability spec 范围 | ✅ `[x]` | 5 个 spec 目录均含 spec.md |
| 1.2 确认前置条件 | ✅ `[x]` | 依赖 change 已归档 |
| 2.1.1 重命名 Step 2 | ✅ `[x]` | `page_assigner.py:129` `_apply_source_category_assignments` |
| 2.1.2 更新调用点 | ✅ `[x]` | `page_assigner.py:80-82` 传入 `assignment_priority` |
| 2.2.1 构建 alias 查找表 | ✅ `[x]` | `page_assigner.py:218-225` |
| 2.2.2 扩展 MW 匹配逻辑 | ✅ `[x]` | `page_assigner.py:261-276` |
| 2.3.1 读取 page_categories | ✅ `[x]` | `page_assigner.py:228-234` |
| 2.3.2 MW fallback 使用 page_cat_dir_map | ✅ `[x]` | `page_assigner.py:279-287` |
| 2.4.1 parseArgs --output | ✅ `[x]` | `chrome-agent-cli.mjs:108,281-288` |
| 2.4.2 runCrawl 使用 outputDir | ✅ `[x]` | `chrome-agent-cli.mjs:1994,1997-2000` |
| 2.4.3 MW API pipeline 透传 | ✅ `[x]` | `chrome-agent-cli.mjs:2089` |
| 2.4.4 main() 传递 | ✅ `[x]` | `chrome-agent-cli.mjs:3732` |
| 2.5.1 逐页写 .md | ✅ `[x]` | `convert.py:296-300` |
| 2.5.2 批量 flush state | ✅ `[x]` | `convert.py:305-311,321-322` |
| 2.5.3 Resume 跳过已转换 | ✅ `[x]` | `convert.py:255-266` |
| 2.6.1 BOI 策略 mw_category_aliases | ✅ `[x]` | `strategy.md:73-76,81,84` — Items/Bosses/Monsters/Trinkets/Chapters/Achievements |
| 3.1-3.5 运行时验证 | ⬜ `[ ]` | 需对 BOI 站点执行 crawl |
| 4.1-4.3 回写 | ⬜ `[ ]` | 依赖 verification 完成 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| source_category_match 实现 | `scripts/pipeline/pipeline/page_assigner.py:129-167` | source-category-assignment / 2.1 |
| alias 查找 + 匹配 | `scripts/pipeline/pipeline/page_assigner.py:218-276` | mw-category-aliases / 2.2 |
| page_categories fallback | `scripts/pipeline/pipeline/page_assigner.py:228-234,279-287` | page-categories-fallback / 2.3 |
| CLI --output 解析 | `scripts/chrome-agent-cli.mjs:108,281-288` | output-flag-parsing / 2.4.1 |
| runCrawl outputDir 逻辑 | `scripts/chrome-agent-cli.mjs:1994,1997-2000` | crawl-output-directory / 2.4.2 |
| Convert 逐页写 .md | `scripts/pipeline/pipeline/phases/convert.py:296-300` | incremental-page-write / 2.5.1 |
| Convert 批量 flush | `scripts/pipeline/pipeline/phases/convert.py:305-311` | state-flush-interval / 2.5.2 |
| Convert resume skip | `scripts/pipeline/pipeline/phases/convert.py:255-266` | convert-resume-skip-completed / 2.5.3 |
| BOI mw_category_aliases | `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md:73-84` | mw-category-aliases-field / 2.6 |

## Issues

### WARNING

**W1: page_assigner 模块 docstring 过时**
- 文件: `scripts/pipeline/pipeline/page_assigner.py:3`
- 当前: `Uses a priority chain: manual overrides > category_page members > MW category tags`
- 应为: `Uses a priority chain: manual overrides > source category match > MW category tags (with aliases & page_categories fallback) > default`
- 建议: 更新 L3 docstring 和 L25-28 Priority chain 注释以匹配重构后的实际步骤

### SUGGESTION

**S1: assemble.py L46-50 对 content=None 的处理**
- 文件: `scripts/pipeline/pipeline/phases/assemble.py:46-50`
- 当 Convert 增量写入后 resume 时，skipped 页面的 `content` 为 `None`（`convert.py:261`），Assembly 跳过写入但 `written += 1`
- 当前行为正确（幂等），但可添加日志 `"Skipping already-written page"` 以提升可观测性

## 缺口与阻塞项

无代码阻塞项。Section 3/4 运行时验证任务需在目标站点执行 crawl 后关闭。
