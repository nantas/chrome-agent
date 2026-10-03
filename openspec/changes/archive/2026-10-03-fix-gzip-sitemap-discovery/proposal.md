# Proposal

## 问题定义

2026-10-03 的 darkestdungeon.wiki.gg discovery 下载了合法 sitemap index 及两个 gzip 子文件，却将压缩字节直接按 UTF-8 交给 XML parser，最终以 `sitemap_all_subs_failed` 停止。属于 P-line 通用代码能力缺失。

本地原始证据 `outputs/dd1-full-discovery/_sitemap_sub_0.xml`、`_sitemap_sub_1.xml` 均为 gzip；现有解析/合并函数离线重放得到两个与 handoff 相同的 parse_error。仅增加解压即可分别得到 957、99 个 URL，去重后 1056 个（过滤前，不代表 DD1 页面范围）。现有 sitemap 测试 39 项全部通过，未覆盖真实压缩文件读取边界。

失败报告还引用了不存在的 `manifest.json`，未链接真正有用的子 sitemap 文件。

## 范围边界

包含顶层/子 sitemap 的通用 gzip 解码、明确解压错误、原始证据链接和回归测试。保持既有 URL 过滤、去重、部分失败及 Crawl Confirmation Gate。

不改变站点策略、DD1/DD2 范围规则、正文抓取引擎、递归索引支持或 XML parser 实现；不自动执行 extraction。当前只完成规划 artifacts。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `sitemap-driven-crawl`: 顶层及子 sitemap 支持按实际字节识别 gzip，解压失败遵循现有失败契约，并在 handoff 中链接存在的原始证据。

## Capabilities 待确认项

- [x] 能力范围已与用户确认；归属现有 sitemap-driven-crawl，无新增独立 capability。

## Impact

- `scripts/chrome-agent-cli.mjs`：统一 sitemap 字节解码；顶层/子文件接入；失败 artifacts 传递与 handoff 渲染的最小兼容修正。
- `tests/sitemap-driven-crawl.test.mjs` 及必要的 CLI handoff 测试：真实文件读取和编排回归，使用 node:test 与临时目录。
- 使用 Node 内置 `node:zlib`，不增加第三方依赖。
- CLI 修改触发 C10 全局同步；不直接把 CLI 复制成全局 launcher。
- docs 与永久 spec 在验证后回写；新测试不依赖未跟踪的站点策略或本机 outputs。

## 关联绑定

- 关联 binding: `binding.md`。
- 标准页、项目页和回写目标遵循 binding；项目页面为 CLI reference 与 tech stack，行为变更由本 change 的 delta spec 承载。
