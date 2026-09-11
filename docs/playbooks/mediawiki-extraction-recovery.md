# MediaWiki 抽取恢复

适用：切换 acquisition 后复用了旧缓存、历史 Markdown 缺 infobox，或表格转换曾挂起。修复代码不会自动补齐历史产物。本手册的联网恢复和下游 ingest 是独立任务；实施 change 时未执行。

## 1. 重新审核发现范围

先用当前已冻结策略执行 discovery-only，读取返回 artifact 中的 manifest 和 summary：

```bash
chrome-agent crawl https://growagarden.fandom.com --discovery-only --pipeline-timeout-seconds 3600
```

核对实际页面身份、ns、目录分配、排除项、列表页决策及与旧 manifest 的差异。不要手改新 manifest 的策略指纹，也不要用历史 1,596/1,602 页作成功标准。旧根目录分配不会自动迁移；当前发现的未分组页应按治理进入 Misc。确认范围后才执行提取。

## 2. 清点缓存

针对审核后的 manifest，使用 `cache.load_page_cache(repo_root, platform, domain, title)` 读取，随后用 `cache.resolve_acquisition(strategy)` 和 `cache.admit_page(raw, title, mode, base_url)` 分类：兼容、缺失、模式冲突、载荷缺失、来源冲突。策略读取使用 `scripts.lib.strategy_loader`，不要按文件名反解 title。

HTML 模式要求非空 `html`。旧 hybrid 只有 wikitext、缺 rendered HTML 时不能靠修改 marker 或跳过 fetch 修复。v2 哈希文件与 legacy 文件可并存，读取验证 exact title；不要批量重命名/删除旧缓存。

## 3. 选择恢复路径

以下命令在仓库根目录运行。替换 manifest 和新输出目录路径；不要覆盖历史交付目录。`.venv/bin/python` 是应用层解释器；无仓库 venv 时先按应用层环境治理完成 preflight，再使用 `python3 -m scripts.pipeline`。

**缺 HTML 或需要重新获取**：审核范围后运行完整管线，强制重抓并禁用旧 completion：

```bash
.venv/bin/python -m scripts.pipeline pipeline https://growagarden.fandom.com \
  --strategy sites/strategies/growagarden.fandom.com/strategy.md \
  --from-manifest /absolute/path/reviewed-manifest.json \
  --output /absolute/path/new-recovery-output \
  --re-fetch --no-resume
```

Python 入口没有 CLI 包装层的十分钟预算。若使用 `chrome-agent crawl --from-manifest ...` 包装入口，可设置 `--pipeline-timeout-seconds 3600`；该参数只控制每个 MediaWiki 子进程，不能替代范围确认或掩盖网络失败。强制重抓失败时旧缓存仍保留，但该页不能进入本次成功结果。

**所有目标均有合格 HTML，仅需重转**：

```bash
.venv/bin/python -m scripts.pipeline pipeline https://growagarden.fandom.com \
  --strategy sites/strategies/growagarden.fandom.com/strategy.md \
  --from-manifest /absolute/path/reviewed-manifest.json \
  --output /absolute/path/new-offline-output \
  --phase convert assemble --no-resume --no-api-probe
```

离线路径要求策略已有 `api.base_url`，不会补抓缺页。准入失败查看 `extraction_results.json` 的 expected/actual mode、reason 和 remediation。修复指纹之前的 completed 状态不能证明 Markdown 新鲜。

## 4. 内容验收与交接

核对本次成功/失败/redirect 与审核范围一致，检查失败页没有进入索引。新目录可以避免旧物理文件被人工误交付；程序不会主动删除历史输出。

抽查实体页（如 Apple）的独有 infobox 字段名、值、单位和出现次数；核对跨目录链接、同名不同物品池目标、正文、文首连续表格及尾文。列表页 Crops 不能替代实体 infobox 验收。缓存命中率和文件数量不能证明内容完整。

当前 Crops golden 与用户已有策略修改不同，须单独审核；本 change 的验证记录证明相同工作区策略下当前输出与 HEAD d10858d 一致。不要直接接受整份 golden diff 来宣称恢复成功。

验收完成后再交接独立 my-wiki ingest，保留原有个人产品拆解与历史产物。本 change 不执行 ingest。
