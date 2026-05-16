# Proposal

## 问题定义

在执行 `chrome-agent explore https://bindingofisaacrebirth.wiki.gg/` 时，explore 工作流出现以下系统性失效：

1. **静默失败链路**：`runExplore()` 调用 `scripts/explore/main.py`（deep discovery 七阶段管线）时，因 `bs4` 模块缺失抛出 `ModuleNotFoundError`，被 `try/catch` 静默捕获后 fallback 到劣化路径，最终只输出一句 "strategy gap"。
2. **劣化 fallback 无用**：legacy fallback 尝试抓取页面 HTML 做后端检测，但 wiki.gg 对 `/wiki/*` 路径返回 Cloudflare 403，检测失败，产出物为空白。
3. **无依赖预检查**：`runDoctor()` 检查 scrapling、obscura、cloakbrowser 等引擎版本，但不检查 deep discovery 管线的 Python 依赖（`bs4`、`yaml`），导致问题在运行时才暴露。
4. **Agent 行为不受控**：SKILL.md 没有定义 explore 后的确认门流程。Agent 在得到 "strategy gap" 后可能直接跳到全量提取，跳过了页面类型分析、采样验证、用户确认三个关键环节。
5. **HTML→Markdown 转换器绑定特定站点**：`HtmlToMarkdownConverter` 硬编码了 `wiki_domain = "slaythespire.wiki.gg"` 和 StS2 特定的 DOM selector / image 过滤规则，无法复用给其他 wiki.gg 站点。
6. **AGENTS.md 缺少 explore→crawl 的治理约束**：未明确禁止 agent 在 explore 未完成确认前直接进入全量提取。

这些问题导致 explore 命令失信于用户预期——它应该产出结构分析、样本和策略 scaffold，而非一句无用的 "strategy gap"。

## 范围边界

### 范围内

| 项 | 说明 |
|----|------|
| 消除 `runExplore()` 中的静默 try/catch | 改用显式 preflight + 非静默错误返回 |
| 新增 `explore_python_deps` doctor 检查项 | 在 `runDoctor()` 中检查 bs4、yaml 导入 |
| SKILL.md 增加 explore 确认门流程 | Gate 1-4：结构分析→采样→自检→用户确认 |
| `HtmlToMarkdownConverter` 通用化 | 移除 StS 硬编码，参数化 domain、selector、image filter |
| `strategy.md` 增加 extraction 配置段 | 为 Isaac wiki 添加 per-template 清洗规则 |
| AGENTS.md 增加 explore→crawl 确认门规则 | 明确禁止跳过确认直接进入全量提取 |
| `scripts/explore/requirements.txt` | 固化管线 Python 依赖声明 |

### 范围外

| 项 | 说明 |
|----|------|
| Isaac wiki 的 infobox 结构化提取 | 本变更仅铺设配置框架（cleanup_selectors, infobox config），具体规则需要站点级调优 |
| 通用 MediaWiki 模板库 | 不在本变更内建立完整的 per-template 转换规则集 |
| SKILL.md 的 `fetch` / `crawl` 流程改动 | 仅触及 explore 路由 |
| `scripts/explore/main.py` 自身功能逻辑修改 | 仅增加启动依赖自检，不改变七阶段管线行为 |

## Capabilities

### Modified Capabilities

- `explore`: 移除 `runExplore()` 中的静默 try/catch 和 legacy fallback；管线执行失败时返回明确错误信息（failure），而非降级到 "strategy gap"
- `explore-workflow`: deep discovery 管线增加启动前依赖预检查（`explore_python_deps`），缺失时硬阻断并给出安装指令
- `doctor-repo-freshness`: doctor 检查项新增 `explore_deps`，检查 `bs4` 和 `yaml` 的 Python 导入可用性
- `pipeline-converters`: `HtmlToMarkdownConverter` 移除 StS 硬编码；`wiki_domain` 改为必传参数；image 过滤和 cleanup selector 从 `extraction` 配置段读取
- `agents-governance`: AGENTS.md 新增「Explore→Crawl Confirmation Gate」治理规则段

### New Capabilities

- `explore-skill-gates`: chrome-agent SKILL.md 新增「Explore Workflow Gates」和「Explore Result Interpretation」章节，定义 Gate 1-4（结构分析确认→采样转换→LLM 自检→用户确认）

## Capabilities 待确认项

- [x] 能力清单已与用户确认
- [x] 已检查现有 `specs/explore/spec.md` 和 `specs/explore-workflow/spec.md`，确认本变更的 Modified Capabilities 与已有 Requirement/Scenario 兼容（加固实现，不改变行为契约）

## Impact

| 影响面 | 说明 |
|--------|------|
| `scripts/chrome-agent-cli.mjs` | `runExplore()` 和 `runDoctor()` 修改 |
| `scripts/explore/main.py` | 增加启动依赖自检 |
| `scripts/explore/requirements.txt` | 新建 |
| `scripts/mediawiki-api-extract/converters/html_to_markdown.py` | 重构，移除 StS 硬编码 |
| `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` | 增加 extraction 段（per-template 清洗规则） |
| `sites/templates/mediawiki-wiki-gg.yaml` | extraction 段 schema 补充 |
| `~/.agents/skills/chrome-agent/SKILL.md` | 新增 explore 确认门章节 |
| `AGENTS.md` | 新增 explore→crawl 确认门规则 |

### 兼容性

- **StS 站点**：`HtmlToMarkdownConverter` 通用化后，StS 策略已有自己的 `extraction` 配置段，可通过显式配置保持现有行为
- **已有策略站点**：所有在 `sites/strategies/registry.json` 中已注册的站点不受影响——explore 命中已有策略时走现有路径
- **Agent 行为**：SKILL.md 新增的门流程是**附加指令**，不改变已有 `fetch` / `crawl` / `doctor` 的行为

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `specs/explore/spec.md`、`specs/explore-workflow/spec.md`、`specs/pipeline-converters/spec.md`、`specs/doctor-repo-freshness/spec.md`、`specs/agents-governance/spec.md`
  - 项目页面：Obsidian `projects/chrome-agent/explore-workflow-hardening`
  - 回写目标：上述 spec 文件的 implementation_status 更新
