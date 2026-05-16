# Design

## Context

2026-05-16 实战 `chrome-agent explore https://bindingofisaacrebirth.wiki.gg/` 揭示了 explore 工作流中四个层级的实现缺陷：

1. **运行时层**：`runExplore()` 的 `try/catch` 静默吞掉 `scripts/explore/main.py` 的 `ModuleNotFoundError`，造成 pipeline 完全未执行但对外表现为"strategy gap"
2. **依赖层**：doctor 检查引擎（scrapling/obscura/cloakbrowser）但不检查 deep discovery 管线的 Python 依赖（bs4, yaml），问题在运行时才暴露
3. **转换层**：`HtmlToMarkdownConverter` 硬编码 StS 特定 selector 和 domain，无法复用给其他 wiki.gg 站点
4. **治理层**：SKILL.md 和 AGENTS.md 均未定义 explore→crawl 的确认门，agent 可以跳过采样验证直接全量提取

以上各层的 spec 已分别在本次 change 的六个 capability spec 中定义行为契约。本 design 说明实现层面的架构决策。

## Goals / Non-Goals

**Goals:**

- 消除 `runExplore()` 中的静默失败，所有 pipeline 执行失败均产生明确、可操作的错误输出
- doctor 新增 `explore_deps` 检查项，使依赖问题在 preflight 阶段即可发现
- `HtmlToMarkdownConverter` 移除所有 StS 硬编码，改为配置驱动
- SKILL.md 增加结构化的确认门流程，agent 必须依序通过 Gate 1-4
- AGENTS.md 增加治理规则，明确禁止跳过确认直接全量提取

**Non-Goals:**

- 不改变 `scripts/explore/main.py` 的七阶段管线逻辑（仅增加启动依赖自检）
- 不为 Isaac wiki 建立完整的 per-template 转换规则集（仅铺设配置框架）
- 不修改 `chrome-agent-cdp`、`obscura-fetch`、`cloakbrowser-fetch` 等引擎
- 不修改 `scrape` 和 `bounded-crawl` 的内部逻辑

## Decisions

### Decision 1: 在 `runExplore()` 内做 preflight，而非在 `runDoctor()` 内

`explore_deps` 检查同时在两个位置部署：
- `runDoctor()` 新增检查条目，供用户主动诊断
- `runExplore()` 在执行 deep discovery 前独立执行检查，不依赖 doctor 是否已被调用过

理由：doctor 是可选的诊断入口，agent 可能在未执行 doctor 的情况下直接进入 explore。`runExplore()` 自身的 preflight 确保每次 explore 调用都受保护。

### Decision 2: converter 配置注入点选在 Phase B 的 converter 实例化处

转换器通用化的配置注入点在 `phase_b.py`（和 `phase_c.py`）中创建 `HtmlToMarkdownConverter` 实例时：

```python
converter = HtmlToMarkdownConverter(
    wiki_domain=domain,
    extraction_config=strategy.get("extraction", {})
)
```

strategy 的 `extraction.cleanup_selectors` 和 `extraction.image_filtering.skip_patterns` 通过 `extraction_config` dict 传入。

理由：这是 converter 的唯一构造点，改动最小，不影响 `__init__` 签名以外的代码。

### Decision 3: 移除全部 legacy fallback 代码，不做配置化保留

`runExplore()` 中 legacy fallback 的全部代码（HTML fetch via `runEngineFetch`、`detectBackend` 调用、bootstrap-strategy 建议生成）将被移除，而非通过 feature flag 保留。

理由：
- 已有 spec (`explore.command-backend` scenario `strategy-gap`) 明确规定 deep discovery 是唯一路径
- legacy fallback 在 wiki.gg 上已证实无效（Cloudflare 403），在其他站点上未经测试
- 保留 dead code 增加维护负担和混淆风险
- `bootstrap-strategy` 命令仍可通过手动调用使用，不受影响

### Decision 4: SKILL.md gates 使用 ask_user 进行交互确认

Gate 4（用户确认）的交互机制使用 `ask_user` 工具而非纯文本输出。Agent 在确认点暂停，用户必须显式批准才能继续。

理由：纯文本输出容易被 agent 跳过或误解为已确认。`ask_user` 提供结构化的交互机制，确保确认是显式的。

### Decision 5: StS 策略文件显式声明 cleanup 配置以保持向后兼容

`HtmlToMarkdownConverter` 通用化后，StS 策略需要在其 `strategy.md` 的 `extraction` 段显式声明之前硬编码的 cleanup 规则。本 change 将在 StS 策略中补全 `cleanup_selectors` 和 `image_filtering.skip_patterns`。

理由：这是 converter 通用化的必要配套步骤，确保 StS 站点的输出不变。不在此 change 中处理将导致 StS 提取行为退化。

## Risks / Migration

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 移除 legacy fallback 后，少数未覆盖站点无法 explore | 低 | 当前所有已知站点类型（MediaWiki / wiki.gg / Fandom / static-site）在 `sites/templates/` 和 deep discovery 中已有覆盖；新站点类型通过 deep discovery + 模板选择处理 |
| Converter 通用化可能引入 StS 提取差异 | 中 | Decision 5 通过显式 StS 策略配置保持向后兼容；verification 中包含 StS 全量对比测试 |
| SKILL.md gates 可能被旧版 agent（不读取 SKILL.md）忽略 | 低 | AGENTS.md 中同步添加治理规则（`explore-crawl-confirmation-gate`）作为第二道防线 |
| `bs4` 和 `selectolax` 功能重叠 | 低 | `bs4` 仅用于 `scripts/explore/`（deep discovery），`selectolax` 仅用于 `scripts/mediawiki-api-extract/converters/`（Markdown 转换）；两者不互斥，各自服务于不同模块 |
