# 07 — Explore Workflow Architecture

> **Spec reference**: Architecture Gate spec, KI Lifecycle spec
>
> **Source modules**: `scripts/explore/`
>
> **Source**: AGENTS.md §3 Deep Discovery content

## 1. Overview

The Explore workflow implements a **deep discovery pipeline** that analyzes an unknown website, generates a strategy scaffold, validates conversion quality, and produces a frozen strategy file. It operates as an 8-step sequential pipeline with two critical validation gates.

```
URL input
  │
  ├── Step 1: ProbeChain         ──→ Engine chain results + raw HTML
  ├── Step 2: ApiDiscovery       ──→ Platform API endpoints
  ├── Step 3: StructureMapper    ──→ Nav sections, page type, content structure
  ├── Step 4: ProtectionIdentifier ──→ Protection level + engine override
  ├── Step 5: Template Selection ──→ Best-matching scaffold template
  ├── Step 6: Scaffold Generation ──→ strategy.md with YAML frontmatter
  ├── Step 7: Sample Conversion & Self-Check ──→ Markdown outputs + quality checks
  │     ├── Architecture Gate (strategy↔pipeline alignment)
  │     └── Auto-remediation loop (max 2 iterations)
  └── Step 8: Freeze            ──→ Remove scaffold markers, register strategy
```

## 2. CLI Entry Point

```bash
python3 scripts/explore/main.py <repo_root> <url> [--run-dir <dir>] [--samples <json>] [--quick]
```

`main.py` 在导入管线模块前，根据 `__file__` 建立仓库根目录和 `scripts/explore/` 的导入路径。直接脚本入口不依赖调用方 cwd 或 `PYTHONPATH`；CLI 继续通过 `resolveAppPython()` 选择应用层解释器。仅设置子进程 `cwd=repoRoot` 无法替代这一步。

启动回归测试：`python3 -m unittest tests.test_explore_startup -v`；真实 CLI 离线路由与交接测试：`node --test tests/explore-handoff.test.mjs`。后者保留真实入口导入，仅替换引擎/网络 probe 边界。

内部失败交接目录使用 `<timestamp>-<command>-<slug>`，slug 由 `slugify(target)` 生成，与运行目录规则一致；即使尚未创建 runDir 也能生成有效名称。时间辅助函数只提供时间字段。交接出现后仍遵循 Handoff Gate。

**Output**: JSON to stdout with all pipeline phase results:

```json
{
  "target_url": "...",
  "probe_chain": { "results": [...], "success_engine": "..." },
  "api_discovery": [...],
  "structure_mapping": {...},
  "protection": {...},
  "scaffold": { "path": "...", "template_id": "..." },
  "samples": [...],
  "self_check": {...},
  "architecture_gate": {...},
  "run_dir": "..."
}
```

**Exit codes**:
- `0` — Success (all gates passed)
- `2` — Partial success (architecture gate violations)

## 3. 8-Step Pipeline

### Step 1: ProbeChain (`probe_chain.py`)

Sequentially attempts engines until one succeeds:

```
scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
```

Per-engine results include: `engine`, `status`, `http_status`, `error_type`, `page_title`, `content_length`.

**Key function**: `probe(repo_root, url, run_dir) → dict`

### Step 2: ApiDiscovery (`api_discovery.py`)

Probes common API endpoints for the target domain:

| Endpoint | Detection |
|----------|-----------|
| `/api.php` | MediaWiki API (`?action=query&meta=siteinfo`) |
| `/wp-json` | WordPress REST API |
| `/graphql` | GraphQL endpoint (introspection query) |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots file |

**Key function**: `discover(url) → list[dict]`

### Step 3: StructureMapper (`structure_mapper.py`)

Analyzes HTML structure to extract:

- **Navigation sections**: Top nav items (max 10) from primary navigation
- **Page type**: `home` / `list` / `article` / `gallery` / `other`
- **Content structure**: Tables, infoboxes, lists, sections present

**Key function**: `map_structure(html, api_config) → dict`

### Step 4: ProtectionIdentifier (`protection_identifier.py`)

Determines protection level based on:

- Engine chain error patterns (which engines failed and how)
- HTML content features (challenge pages, CAPTCHA elements)

Output includes `protection_level` and optional `engine_override`.

**Key function**: `identify(engine_results, html_content) → dict`

### Step 5: Template Selection (`strategy_scaffold_generator.py`)

Selects the best-matching template from `sites/templates/`:

| Template | Platform Match |
|----------|---------------|
| `mediawiki` | Standard MediaWiki |
| `mediawiki-fandom` | Fandom-hosted MediaWiki |
| `static-site` | Static HTML sites |
| `custom` | Fallback for unknown platforms |

**Key function**: `_select_template(repo_root, platform, protection) → dict`

### Step 6: Scaffold Generation (`strategy_scaffold_generator.py`)

Generates a `strategy.md` file with YAML frontmatter populated from discovery results:

- `domain`, `platform`, `protection_level`, `protection_type`
- `page_type` array mapped from nav sections
- `api` config (if MediaWiki detected)
- `extraction` rules (selectors, cleanup, infobox, image filtering)
- `anti_crawl` references

The scaffold file is written to `sites/strategies/<domain>/strategy.md` with a first line `# Auto-generated scaffold — review recommended`.

**Overwrite Guard**：如果 `strategy.md` 已存在且首行不是 `# Auto-generated scaffold`，scaffold 生成器将跳过写入并返回 `{"skipped": true, "reason": "Manually-edited strategy exists — delete it first to regenerate."}`。这保护了手动编辑的策略文件不被 explore 流程重置。自动生成的 scaffold（首行以 `# Auto-generated scaffold` 开头）则允许正常覆盖，支持重新生成。

**Key function**: `generate(repo_root, domain, description, platform, protection, structure, api_config) → dict`

### Step 7: Sample Conversion & Self-Check

This is the most complex step, involving multiple sub-phases:

#### 7a: Sample Conversion (`sample_converter.py`)

Fetches sample pages and converts them using the scaffold extraction rules:

```python
def _apply_extraction(html, extraction_rules, known_pages):
    infobox_md = extract_infobox(html, extraction_rules, wiki_domain)    # Step 1
    cleaned_html = preprocess_html(html, extraction_rules, "explore")    # Step 2
    md = convert_html_to_markdown(cleaned_html, wiki_domain, rules)      # Step 3
    md = infobox_md + "\n\n" + md                                        # Step 4
    # Post-conversion normalization...
```

**Key function**: `convert(repo_root, samples, extraction_rules, engine, run_dir) → list[dict]`

#### 7b: Self-Check (`self_check.py`)

Runs S1–S12 quality checks against each converted sample:

| Check | What it validates |
|-------|------------------|
| S1 | Image retention (count + full URL verification) |
| S2 | Link resolution (no unresolved references) |
| S3 | Infobox extraction completeness |
| S4 | Non-empty content |
| S5 | Text integrity (version regex check) |
| S6 | Table structure preservation |
| S7 | Image wrapper cleanup |
| S8 | Section extraction completeness |
| S9 | Navigation removal from content |
| S10 | YouTube title extraction |
| S11 | Relative link conversion |
| S12 | Infobox semantic quality |

Each check returns: `{check, status: pass|fail|skip, detail, fixable_type?}`

**Key function**: `run_checks(html, markdown, wikitext, known_pages, type, ...) → list[dict]`

#### 7c: Auto-Remediation Loop

`plan_remediation(extraction, issues, evidence=None)` 返回独立的 `{extraction, applied, unresolved, changed}` 报告，深拷贝输入。`auto_remediate()` 保持只返回 extraction 字典的兼容接口。支持 wrapper/table/space 配置更新；lazyload 仅使用完整已有配置或显式证据提供的 placeholder_pattern/real_src_attr。不支持的 consumer 或缺少证据分别返回 `unsupported_consumer` / `missing_evidence`，保留原 failure，供 KI 分类；applied 不代表质量已修复。

main 仅在候选准入且 changed=true 时重转换/重检，最多两次更新；无有效变化立即停止。质量状态仍以 self-check 为准，Architecture Gate 和冻结确认继续生效。

所有注册 MediaWiki 模板在真实生成时遵守共享 schema。generic/wiki.gg 的编辑清理使用 strip_edit_links，TOC 使用 .toc/#toc cleanup_selectors。iterate 先规划候选并校验，非法 MediaWiki 规则返回字段诊断，原文件字节不变且不调用转换；非 MediaWiki 描述性规则保持原边界。普通 image 反馈可应用 wrapper，同时报告 lazyload 缺证据。

验证入口：[producer 修复 verification](../../openspec/changes/archive/2026-10-02-fix-explore-extraction-config-producers/verification.md)。2026-10-02 原 URL 验证已解除 schema 错误，Explore 为 partial_success，HTML 仍有 Cloudflare 挑战标记；未进入提取。

#### 7d: Architecture Gate (`architecture_gate.py`)

**Runs after self-check passes, before final output.** Validates bidirectional alignment between strategy config and pipeline converters.

See §4 below for details.

### Step 8: Freeze (`freeze.py`)

After user confirmation:

1. Removes scaffold `<!-- Bootstrapped -->` marker
2. Writes final strategy to `sites/strategies/<domain>/strategy.md`
3. Appends entry to `sites/strategies/registry.json`

**Key function**: `freeze(repo_root, scaffold_path) → dict`

## 4. Architecture Gate

The Architecture Gate (`scripts/explore/architecture_gate.py`) validates **strategy↔pipeline bidirectional alignment** — ensuring no dead config and no hardcoded site-specific values.

### Two-Part Validation

#### Check 1: Strategy → Pipeline (Dead Config Detection)

Scans all extraction config keys to ensure each is consumed by `converter.py` / `preprocessor.py`:

- Checks `.get("key")`, `["key"]`, `"key" in variable`, and `if "key"` patterns in pipeline source
- Validates each `cleanup` operation name appears in pipeline source
- Also checks cleanup operation names via `detect_dead_cleanup_operations()`

**Result**: `dead_config: list[str]` — config keys with no pipeline consumer

#### Check 2: Pipeline → Strategy (Hardcoded Value Audit)

Audits `converter.py` + `preprocessor.py` for site-specific values not sourced from strategy config:

| Check Type | What it detects |
|------------|----------------|
| `hardcoded_selector` | CSS selectors not from `cleanup_selectors` or `infobox.selector` config |
| `hardcoded_css_class` | CSS class names not in strategy's known class set |
| `hardcoded_list_value` | CSS class names in list literals not from config |
| `hardcoded_domain` | Domain names not derived from `image_handling.base_url` |
| `hardcoded_filename_pattern` | File patterns not from `image_filtering.skip_patterns` |
| `unconditional_operation` | Site-specific operations not guarded by config `enabled` checks |

**Result**: `violations: list[dict]` — each with `type`, `detail`, `location`, `remediation`

### Gate Result

```json
{
  "status": "pass" | "fail",
  "strategy_to_pipeline": {
    "status": "pass" | "fail",
    "dead_config": [...],
    "files_checked": ["converter.py", "preprocessor.py"]
  },
  "pipeline_to_strategy": {
    "status": "pass" | "fail",
    "violations": [...]
  }
}
```

The gate runs on the pipeline extraction files defined in `_PIPELINE_FILES` (currently `converter.py` + `preprocessor.py`): `converter.py` for conversion/hardcoded-value audit, `preprocessor.py` for cleanup-operation consumption.

## 5. KI Lifecycle Gate

The KI (Known Issue) Lifecycle module (`scripts/explore/ki_lifecycle.py`) runs **after the Architecture Gate passes** and provides structured management of self-check failures that could not be auto-remediated.

### KI Classification

Each self-check failure is classified with an **owner domain**:

| Owner | Meaning |
|-------|---------|
| `strategy` | Fix requires strategy config changes |
| `pipeline` | Fix requires converter/pipeline code changes |
| `self_check` | Check methodology issue (false positive, scope problem) |

Owner inference decision tree:
1. Explicit override provided → use it
2. `fixable_type` suggests pipeline fix → `pipeline`
3. Check ID has predefined mapping → use mapping
4. Heuristic keyword matching in detail text
5. Default → `self_check`

### Priority Assignment

| Priority | Criteria |
|----------|----------|
| P0 | Data corruption (wrong field values, broken links/images, navigation text in IDs) |
| P1 | Quality impact (readability reduction, false positives, minor pollution) |
| P2 | Check methodology (scope/precision issues, no output impact) |
| P3 | Skip/cosmetic (negligible visual impact) |

### Status State Machine

```
open ──→ in_progress ──→ resolved
  │           │
  │           └──→ wontfix (terminal)
  ├──→ open_systemic (terminal)
  └──→ wontfix (terminal)
```

### Fix Batch Planning

KIs are grouped into priority-based batches for sequential fix iterations:

- Batch 0: All P0 KIs
- Batch 1: All P1 KIs
- Batch 2: All P2 KIs (P3 are cosmetic, not batched)

Maximum 3 iterations (`MAX_ITERATIONS = 3`).

### KI Table Generation

Produces a Markdown table for inclusion in `strategy.md`:

```markdown
## Known Issues (Post-Validation)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | ... | open | P1 | pipeline | ... | ... |
```

**Key function**: `run_ki_lifecycle(failures, owner_overrides) → list[dict]`

## 6. Confirmation Gates

### Explore → Crawl Confirmation Gate

When `explore` returns `partial_success` with a strategy gap, the agent **must not** proceed directly to crawl or fetch. The gate requires:

1. **Agent presents**: Structure analysis, sample conversions, self-check results, architecture gate result
2. **Agent self-audits**: Before user review, verify self-check report completeness
3. **User confirms**: Explicit approval to proceed
4. **3-iteration limit**: Maximum 3 remediation iterations before requiring user intervention

### Crawl Confirmation Gate (Discovery → Extraction)

When SKILL routes `crawl` intent without `--yes`:

1. **Discovery-only**: `chrome-agent crawl <url> --discovery-only --format json`
2. **Presentation**: Tree visualization of discovery results
3. **Confirmation**: User approves/adjusts/cancels
4. **Extraction**: `chrome-agent crawl <url> --from-manifest <path>`

`--yes` bypasses the gate entirely.

## 7. Module Dependency Map

```
main.py
  ├── probe_chain.py          (Phase 1)
  ├── api_discovery.py        (Phase 2)
  ├── structure_mapper.py     (Phase 3)
  ├── protection_identifier.py(Phase 4)
  ├── strategy_scaffold_generator.py (Phase 5+6)
  ├── sample_converter.py     (Phase 7a)
  │     ├── lib/extraction/infobox.py
  │     ├── lib/extraction/preprocessor.py
  │     └── lib/extraction/converter.py
  ├── self_check.py           (Phase 7b+7c)
  ├── architecture_gate.py    (Phase 7d)
  └── ki_lifecycle.py         (Post-gate)
```

External dependencies (from `scripts/explore/requirements.txt`):
- `beautifulsoup4>=4.12`
- `pyyaml>=6.0`
- `selectolax>=0.3`

## 关联文档

- [00 — 目标架构](00-target-architecture.md) — **架构真源**：explore 作为 B 轴执行路径的 4 维坐标
- [01 — 系统总览](01-overview.md) — 多后端架构全景

## Page enumeration using an existing frozen strategy

`python3 -m scripts.explore.page_discovery --strategy <path> --output <run-dir>` is separate from the eight-step site-analysis workflow. It dispatches existing allpages/homepage kernels, resolves canonical list identities within retained scope and produces a v2 manifest plus evidence-based summary. Public crawl invokes it for discovery-only; no re-probing/scaffolding of an already known site is required. Unknown counts/estimates remain null with reasons; observed API failures result in partial/failure, never fabricated success.

Freeze now validates before removing any markers or publishing registry metadata. New drafts require recorded lifecycle.review_evidence and valid target entry points; failures retain original files and produce diagnostic evidence. Bootstrap drafts cannot be used by production strategy lookup.

## 正文准入与失败传播（2026-10-02）

probe 每个成功候选先检查原始 HTML。无可用正文时 main 返回 result=failure、reason=content_unavailable、exit 3；结构分析、草稿生成、样本转换不执行。诊断仍保留各引擎结果，末级 pending 不代表已运行浏览器。CLI 保留该外部失败，不生成内部崩溃 handoff 或 freeze 建议。exit 2 的结构化 partial_success 保留；未知错误/无效 JSON 仍走内部 handoff。样本获取失败参与 self-check failure 汇总，不能因零检查而通过。

此前 wiki.gg 挑战页被误当 success 的缺口由 fix-challenge-page-admission 处理；验证见 `openspec/changes/archive/2026-10-02-fix-challenge-page-admission/verification.md`。

## Probe 尝试证据

每次尝试记录 stage、executed、process_exit、error_type 和证据路径；stage 区分 preflight/process/admission/pending。未执行的浏览器 fallback 为 pending，不能当作已尝试成功。每个 attempt 落盘 JSON，stderr 与 HTML 分开，probe-chain.json 汇总尝试链；CLI 的 discovery-result.json 保留完整 discovery 结果。

没有正文时仍返回 engine_path 和诊断 artifacts。参数/响应协议等内部错误触发现有 handoff；内容拒绝继续呈现明确的失败与授权 fallback 指引，不自动接管用户浏览器。恢复取得正文只允许进入后续 discovery，策略审查、freeze 和 crawl 确认门保持有效。

## Self-check 来源契约（2026-10-03）

采样结果声明 `input_scope`：HTML 引擎为 full_document，MediaWiki API 为 content_fragment。main/iterate 每次用当前 extraction 调用 `build_source_context`，把 raw 来源、正文范围、独立 infobox 和明确排除区域传入 `run_checks(source_context=...)`。全文 selector 不命中明确报错；旧调用仍可用，证据不足的检查显式 skip。

S1 比较应保留图片 multiset，过滤皮肤图并检测同数量换图、重复图丢失；S9 比较来源导航区域的链接序列，内容词不再触发失败，正文/导航重叠无法归因时 skip；S5 对可见文本逐次匹配来源重复，源文笔误进入 notes，新增重复仍 fail。图片位置保留为文本边界，避免图标旁数值被拼接。汇总保留 pass/fail/skip、notes 与 skipped_checks，notes 不进入自动修复。

[验证记录](../../openspec/changes/archive/2026-10-03-fix-crawl-strategy-conversion-and-self-checks/verification.md) 包含真实六页重放与来源反例；skip 不代表该项已经完整验证。

## 离线批量来源审计（2026-10-04）

运行 `.venv/bin/python -m scripts.explore.batch_audit --manifest <json> --output <report.json>`。manifest 包含 extraction 快照及 pages；每页提供 id、绝对 HTTP(S) source_url、html_path、markdown_path、input_scope。相对文件路径以 manifest 目录解析；可选 link_mapping 将本地文件映射到来源 URL。报告不得覆盖输入，缺文件/重复身份/缺来源 URL 显式报错，不访问网络。

S6 按表格位置和单元格语法识别 delimiter，短横线数据行仍计数；S8 核对原始保留范围及声明配对的标题层级/次数；S5 的版本样式候选与来源有限预算归因，已有标识记 note，真实新增仍失败。嵌套图片链接与括号目的地址正确解析。

报告给出每项 pass/fail/skip、notes、未映射目标与 complete_validation，缺来源不能伪造 pass。exit 2 表示输入/检查失败，overall_pass 不代表所有检查适用且完成。209 页验证仍有 Crypt Keeper 合并单元格重复词归因边界，S9 正文/导航重叠及跨集未映射链接会显式 skip。

[验证与限制](../../openspec/changes/fix-conversion-structure-and-audit-fidelity/verification.md)。
