# Design

## Context

行为依据为 `specs/sitemap-driven-crawl/spec.md` 的四个 requirement：fetch-and-parse、partial-failure-resilience、decompression-failure-diagnostics、handoff-existing-evidence。

当前 `runCrawlSitemapDiscovery()` 对顶层和子文件分别 curl 下载，再 `readFileSync(path, "utf8")`。`parseSitemapXml()` 接收字符串，`resolveSitemapIndex()` 注入 fetchFn。两个下载分支都缺少二进制解码。`internalFailure()` 接收 artifacts，但未转交 `generateHandoff()`；后者无条件拼出 manifest 路径且只枚举 log/json。

诊断已经证明只增加解压即可读取本次两个捕获文件（957 + 99 = 1056 URL）；并未验证修复后完整 CLI discovery。现有 39 项 sitemap 测试通过不能代替压缩边界回归。

## Goals / Non-Goals

**Goals:** 顶层及子文件统一支持普通 XML/gzip；区分解压与解析失败；保留失败韧性、原始证据及可用 handoff 链接；用真实读取/编排测试锁定缺陷。

**Non-Goals:** 不重写 XML parser，不新增爬取引擎，不改站点策略，不新增递归索引，不自动抓取正文，不扩大到通用 HTTP 客户端重构。

## Decisions

### 1. 字节读取在 parser 之前完成

在 CLI 内新增顶层 function 声明的 sitemap 文件解码 helper，使用 `fs.readFileSync(path)` 得到 Buffer；前两字节为 gzip magic `1f 8b` 时由内置 `node:zlib` 解压，再转 UTF-8，否则直接转 UTF-8。顶层与子 sitemap 必须调用同一 helper。parser 保持纯字符串接口；原始文件不覆盖。

不按文件扩展名决定解压，避免 .gz 返回明文或无后缀返回 gzip 的误判。仅给 curl 加压缩选项无法替代文件内容层解码，因此本 change 的判定依据是落盘字节。

### 2. 错误沿既有编排传播

helper 返回结构化成功/失败结果，捕获解压异常；顶层映射到 `sitemap_decompress_error`，子 fetchFn 提供明确 `decompress_error` 原因。`resolveSitemapIndex()` 消费显式原因，同时兼容既有仅含 httpCode 的 fetch 失败对象。解压后的非 XML 继续由 parser 报 parse_error。

部分失败的计数、warnings/caveats、去重及 all-subs-failed 分支保留。顶层/全部失败不进入过滤或 extraction。

### 3. 复用 artifacts 通道传递诊断文件

Sitemap discovery 收集本次已存在的顶层与子文件，失败时传给 `internalFailure()`；后者通过可选 artifacts 字段传给 `generateHandoff()`。渲染显式 artifacts 与现有 log/json 入口时按绝对路径去重并检查存在性。移除无条件 manifest 链接，保留实际存在的 manifest。无新增参数的其他调用者保持兼容。

不遍历任意目录寻找证据，也不把本次未下载的旧子文件宣称为本次响应。共享 handoff 的改动需要验证其他命令的有效 manifest/log 仍可见。

### 4. 回归必须覆盖生产读取边界

沿用 node:test、临时目录和当前测试 seam；用内置 gzip 构造小型固定 XML。至少一项测试执行真实 `runCrawlSitemapDiscovery()` 编排和文件解码，只替换 curl/网络边界及最终输出接收；不得用已经解码的 fake content 代替这一测试。若使用真实 CLI 子进程，则提供临时最小策略/可执行 curl fixture，避免访问网站或依赖未跟踪的当前策略。

逐个 vertical slice：一个失败测试、最小实现、通过，再覆盖下一个行为。依次覆盖 gzip 子文件、顶层 gzip/索引、后缀反例、损坏文件及 handoff 证据。现有纯 parser/合并测试继续运行。

## Risks / Migration

- 同步解压有内存开销；本 change 不承诺任意大小 sitemap 的流式处理，不引入压缩算法扩展。
- 全局失败报告共享渲染器可能影响其他命令，新增兼容回归验证已有入口保留。
- 不增加能力实现文件或第三方依赖，保持 Node ESM；若实施时改为新增能力模块，则按 C11 同步注册并验证。
- C10 同步 runtime、skill 与 installed-hash，CLI 仅作为同步触发文件，不能复制为 launcher。
- 在线验收使用新 runDir 和显式 `--discovery-only`，保护历史诊断。1056 仅是捕获文件的过滤前离线基线，实时站点数量可变。
- 无数据迁移；回滚代码时无需改动站点策略或已保存的原始文件。工作区其他 change 不属于本变更。
