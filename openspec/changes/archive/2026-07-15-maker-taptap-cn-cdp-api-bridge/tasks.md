# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 fetch-cdp-api-kernel spec 覆盖范围：list API → content API → 缓存写入 → extraction_results.json
- [x] 1.2 确认 strategy-schema spec 覆盖范围：`api.platform: rest`、`requires_authentication`、`api.auth` 字段
- [x] 1.3 确认 pipeline-orchestration spec 覆盖范围：backend 路由 + convert passthrough

## 2. Vertical Slice 1 — 策略文件重写（纯配置）

- [x] 2.1 重写 `sites/strategies/maker.taptap.cn/strategy.md` 为合法 YAML frontmatter 格式
  - 必填字段：`domain`、`description`、`protection_level`
  - 新字段：`requires_authentication: true`、`api.platform: rest`、`api.auth`、`api.endpoints`
  - 移除 `anti_crawl_refs` 中的 `auth_wall`、`spa_js_render`（仅保留 `default`）
  - 验证：`python3 -c "import yaml; yaml.safe_load(open('sites/strategies/maker.taptap.cn/strategy.md').read().split('---')[1])"` 无报错

- [x] 2.2 同步 `sites/strategies/registry.json` 的 maker.taptap.cn entry
  - 字段对齐 frontmatter（C7 约束）
  - `backend` 改为 `"cdp-api-bridge"`（frontmatter 中已有）

## 3. Vertical Slice 2 — fetch_cdp_api.py（代码，含 TDD）

- [x] 3.1 RED: 创建 `tests/test_fetch_cdp_api.py`，覆盖以下场景
  - 成功 list + content 流程（mock `eval_fn`）
  - `eval_fn` 返回 None 的失败路径
  - 单个 content 调用失败不阻断批次
  - 缓存命中跳过

- [x] 3.2 GREEN: 实现 `scripts/pipeline/pipeline/phases/fetch_cdp_api.py`
  - 函数签名：`run_fetch_cdp_api(eval_fn, strategy, domain, repo_root, project_id, path_prefix=None, re_fetch=False, batch_delay_sec=0.3) -> dict`
  - 步骤：读 token → list API → 过滤 → 逐个 content API → 缓存 → 返回 results dict
  - 过滤目录条目（`mimeType: inode/directory`）
  - 缓存复用 `cache_mod.save_page_cache()` / `cache_mod.is_cached()`
  - 验证：`python3 -m unittest tests.test_fetch_cdp_api -v` 全绿

## 4. Vertical Slice 3 — orchestrator 路由（代码）

- [x] 4.1 修改 `scripts/pipeline/pipeline/orchestrator.py` 的 `validate_api_config()`
  - `api.platform == "rest"` 返回 `None`（跳过 MediaWiki 验证）
  - 其他非 `mediawiki` 和 `rest` 的平台仍返回错误

- [x] 4.2 修改 `run_pipeline()` 的 convert 阶段
  - `api.platform == "rest"` 时跳过 `run_convert()`，走 `_passthrough_convert()`
  - `_passthrough_convert()`：读缓存文件 → 取 `content` 字段 → 组装 `extraction_results.json`

- [x] 4.3 验证：现有 MediaWiki 管线不受影响
  - `python3 -m scripts.pipeline --help` 不报错
  - 现有 `tests/` 中 pipeline 相关测试不回归

## 5. Vertical Slice 4 — 能力注册 & 文档同步

- [x] 5.1 更新 `configs/capability-registry.yaml`
  - `fetch.engines` 追加 `cdp-api-bridge` entry（C11 约束）

- [x] 5.2 更新 `docs/architecture/03-strategy-schema.md`
  - 追加 `api.platform: rest` 到合法值表
  - 追加 `requires_authentication` 字段
  - 追加 `api.auth` 子字段定义
  - `api` 字段 `platform` 的描述从 "仅支持 mediawiki" 改为 "mediawiki | rest"

- [x] 5.3 更新 `docs/architecture/00-target-architecture.md`
  - §1.2 Fetch 表格追加 `fetch_cdp_api.py` 行
  - §3.2 Fetch 决策表和目标模块表同步

- [x] 5.4 更新 `docs/playbooks/api-backed-spa-cdp-bridge.md`
  - 补充 "验证结果" 章节（端到端 list + content 成功）
  - 补充 CLI 命令示例

- [x] 5.5 验证：`chrome-agent doctor --check capabilities` 通过（如 CLI 可用）

## 6. Vertical Slice 5 — 端到端验证

- [x] 6.1 使用当前浏览器中打开的 maker.taptap.cn 页面，通过 `cdp.mjs` + `fetch_cdp_api.py` 完成实际抓取
  - 获取文件清单（list API）
  - 拉取至少 1 篇文档（content API，如 `design/GDD-拼词肉鸽.md`）
  - 验证输出为合法 Markdown

- [x] 6.2 验证 `python3 -m scripts.pipeline assemble` 可从 `extraction_results.json` 正确产出最终输出目录

## 7. 收敛与验证准备

- [x] 7.1 整理 verification.md 所需证据（测试结果、端到端输出、文档截图）
- [x] 7.2 标记 writeback.md 目标与状态变更
