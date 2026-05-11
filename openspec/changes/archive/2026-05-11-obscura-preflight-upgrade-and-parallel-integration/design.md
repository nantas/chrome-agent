# Design

## Context

chrome-agent 的 Browser 管线（管线 A）目前使用 Scrapling CLI 串行 fetch 页面内容。基准测试显示 8 页串行需 8-17s，而 Obscura v0.1.2 的 `serve --workers N` + 并发 fetch 可将同一批次的耗时降低到 3.3s（3 workers, 4 URLs）。Obscura `scrape` 子命令本身不返回页面内容，因此实际可行的路径是 serve pool 模式。

MediaWiki API 管线（管线 B）保持独立，不受本次 change 影响。两条管线由 strategy frontmatter 的 `api.platform` 字段在运行时路由。

当前 preflight 固定在 v0.1.0，且未安装/验证 `obscura-worker` binary。升级到 v0.1.2 是 serve pool 模式的前提。

## Goals / Non-Goals

**Goals:**
- Obscura preflight 升级到 v0.1.2，同时安装和验证 `obscura` + `obscura-worker`
- 新增 `obscura-serve-pool` 引擎，通过 `obscura serve --workers N` + 并发 `obscura fetch` 实现批量内容获取
- `crawl`/`scrape` 命令新增 `--parallel` / `--workers` 标志，启用三阶段并行工作流
- 新增 `batch` 命令，直接接收 URL 列表并发并行 fetch
- crawl 管线路由逻辑区分 API/Browser 管线
- 引擎注册表新增条目，更新 obscura-fetch 稳定性备注

**Non-Goals:**
- 改造 MediaWiki API 管线（管线 B）
- 替换高保护页面（Tier 4）的 CloakBrowser 引擎
- 修改 Obscura 上游代码
- 替换 Scrapling 遍历逻辑（Phase 1 URL 发现仍用 Scrapling get）
- 自适应并发调节（adaptive concurrency — 未来 iterative improvement）

## Decisions

### Decision 1: serve pool 而非 scrape 子命令

**选择**: 使用 `obscura serve --workers N` + 并发 `obscura fetch` 模式。

**理由**: `obscura scrape` 只返回 `{url, title, eval, time_ms}` 元数据，不返回页面内容。serve pool 模式下每个 `fetch` 返回完整 HTML。

**代价**: chrome-agent 需要管理 serve 进程的生命周期（启动、就绪检测、停止清理）。

### Decision 7: Markdown 转换使用 Scrapling `--ai-targeted`（file://）而非 htmlToMarkdown

**选择**: 当 Obscura serve pool 获取的 HTML 需要转换为 Markdown 时，不直接使用 `htmlToMarkdown()` 正则转换器，而是将 HTML 写入临时文件，然后调用 `scrapling extract get file://<TEMP>.html <OUTPUT>.md --ai-targeted`，利用 Scrapling 的 DOM 引擎进行高质量转换。

**理由**: 
- 基准测试显示 Scrapling `--ai-targeted` 在 Wiki 文章上保留 413 个链接（vs htmlToMarkdown 317），保留 4 张图片（vs 2），零多余空白（vs 6）
- `file://` URL 经验证可直接被 Scrapling CLI 接受，无需启动本地 HTTP 服务器
- `htmlToMarkdown()` 是纯正则转换器，不理解 DOM 语义，对表格、嵌套列表、复杂的 Wiki 页面处理质量显著低于 Scrapling 引擎

**代价**: 
- 每个 URL 的 Markdown 转换需要一次额外文件写入 + 一次 Scrapling CLI 调用
- 转换速度取决于 Scrapling 启动开销（~200-500ms/页，远少于网络 fetch 时间）
- 需要临时文件管理（写入 + 清理）

**回退**: 若 Scrapling CLI 不可用于后处理，fallback 到 `htmlToMarkdown()` 确保管线不中断

### Decision 2: 管线路由由 strategy frontmatter 驱动

**选择**: crawl 命令在读取 strategy 后检查 `api.platform` 字段。

**理由**: 已有代码在 2026-03 就实现了这个检测模式（1180 行附近），将 API 路由逻辑整合到主流程中。本次 change 只是明确化并扩展 Browser 管线的并行选项。

### Decision 3: 默认 workers=5，上限 30

**选择**: 默认 5 个 worker，通过 `--workers` 可配置，上限 30。

**理由**: 基准测试显示并发 >10 后收益递减（瓶颈移至目标站响应速度），且每个 worker ~50MB RSS 峰值。5 是保守但安全的值，10 是性价比最佳点，30 是资源上限。

### Decision 4: 三阶段分离（不修改遍历逻辑）

**选择**: Phase 1（遍历）仍用 Scrapling get，Phase 2（内容获取）改为 Obscura serve pool，Phase 3（Markdown 转换）不变。

**理由**: Scrapling get 在 URL 发现上更快更稳定（无需启动浏览器），且遍历逻辑本身不是性能瓶颈（8 页遍历仅需 ~500ms vs fetch 8-17s）。分离架构也避免了同时修改遍历和 fetch 两部分的 breakage risk。

### Decision 5: 端口管理策略

**选择**: 从 9200 开始向上扫描可用端口，serve 进程使用 `detached: true` 的 spawn，通过 `process.kill(-pid)` 清理进程组。

**理由**: 避免端口冲突（devtools-mcp 使用 9222），进程组 kill 确保 worker 子进程一并清理。

### Decision 6: batch 命令独立于 crawl/scrape

**选择**: 新增独立的 `batch` 命令，而非在 `fetch` 命令上加多 URL 支持。

**理由**: `batch` 的语义是"已知 URL 列表的批量并行 fetch"，与 `fetch`（单 URL）和 `crawl`（遍历+fetch）都有本质区别。独立命令使参数解析和输出处理更清晰。

## Risks / Migration

### Preflight 升级风险

| 风险 | 缓解 |
|------|------|
| v0.1.0 用户有本地修改 | preflight 检测到已有有效路径时跳过下载 |
| v0.1.2 下载失败 | 保留 source compilation fallback |
| 旧版 `obscura` 无 `serve --workers` 支持 | preflight 验证 serve 子命令；若失败则标记 Obscura 不可用 |

### serve pool 稳定性风险

| 风险 | 缓解 |
|------|------|
| serve 启动超时 | 加入就绪检测循环（轮询端口 5s 内），超时标记为 Obscura 不可用 |
| 某个 worker 挂掉 | 负载均衡器自动跳过不可达 worker；其他 URL 继续处理 |
| serve 未正确关闭 | 加入 timeout kill（serve 使用后超过 30s 自动 kill） |

### 回退/迁移

- 所有 Obscura 路径失败后自动回退到 Scrapling 串行
- `--parallel` 是可选标志，不设默认值，现有脚本零改动
- 引擎注册为 `draft` 状态，可随时降级或移除
