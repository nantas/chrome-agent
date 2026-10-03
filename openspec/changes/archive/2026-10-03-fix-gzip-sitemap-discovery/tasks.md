# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 阅读 `specs/sitemap-driven-crawl/spec.md`、design 与 CLI/测试相关必读文档，核对工作区基线，保留其他 change 的修改。
- [x] 1.2 确认生产 discovery 的可调用测试 seam；只隔离网络边界，保留真实下载文件读取、解码、解析、合并与 handoff。fixture 不依赖本机 outputs 或未跟踪站点策略。

## 2. 核心实现任务

按顺序完成每个 RED→GREEN slice 后再进入下一个；下述 spec 名称均指本 change 的 delta spec。

- [x] 2.1 RED：针对 sitemap-discovery-fetch-and-parse，以普通 index + gzip 子文件驱动真实 discovery 文件读取，断言应产出预期 URL，记录当前 parse_error 失败。
- [x] 2.2 GREEN：新增内置 zlib 的字节解码 helper，接入子文件读取；保留 XML parser 字符串接口与原始下载文件，使 2.1 通过。
- [x] 2.3 RED：增加顶层 gzip urlset 场景，断言 URL 与明文一致，记录顶层读取缺陷。
- [x] 2.4 GREEN：顶层接入相同 helper，使 2.3 通过；补充 gzip index + 混合子文件去重/过滤、无 .gz gzip 和 .gz 明文反例。若新增用例失败，逐项修复后再继续。
- [x] 2.5 RED：针对 sitemap-decompression-failure-diagnostics，使用损坏顶层 gzip，断言结构化 sitemap_decompress_error 与原始证据保留，无未捕获异常。
- [x] 2.6 GREEN：捕获解压异常并映射顶层失败；验证解压成功但非 XML 仍为 sitemap_parse_error。
- [x] 2.7 RED：针对 sitemap-index-partial-failure-resilience，添加一个子文件解压失败另一个正常的测试，断言有效 URL、decompress_error、warnings/caveats 与 failure_rate。
- [x] 2.8 GREEN：扩展 fetchFn 显式失败原因并在 resolver 保留，兼容旧 HTTP 失败对象；验证全损坏仍为 sitemap_all_subs_failed，解压后非法 XML 仍为 parse_error。
- [x] 2.9 RED：针对 sitemap-handoff-existing-evidence，驱动真实失败报告生成，断言顶层与两个子文件链接存在、原始压缩字节未改、缺失 manifest 不被列出。
- [x] 2.10 GREEN：收集本次下载证据，经 internalFailure 传入 generateHandoff；仅列实际存在文件并去重，使 2.9 通过。补充下载前失败无文件、有效 manifest/log 保留及无 artifacts 的既有调用者兼容测试。

## 3. 收敛与验证准备

- [x] 3.1 运行 `node --test tests/sitemap-driven-crawl.test.mjs` 和新增/受影响的 handoff 测试；保留各 slice RED/GREEN 及最终结果。
- [x] 3.2 对已有捕获文件离线重放生产解码路径，验证过滤前 957/99、去重 1056 URL 与零错误；文件缺失时如实记录，不能替代固定 fixture 回归。
- [x] 3.3 按 global-install playbook Case 6 履行 C10，检查并同步 runtime/skill，全局 installed-hash 为当前 HEAD；确认 CLI 仍由 repo-backed launcher 调用。
- [x] 3.4 使用新 runDir 对原目标显式运行 discovery-only，核对生成的 page_manifest/discovery_summary、过滤结果和 warnings；不执行 extraction，不覆盖原故障证据。不将实时数量强制等同离线基线。
- [x] 3.5 执行治理要求的 Node/Python 全量测试、doctor 及 doctor --check capabilities；区分已有问题、外部环境失败与本 change 回归，并记录结果，不伪称全绿。

## 4. 验证与回写收敛

- [x] 4.1 基于实际结果创建 verification.md，建立四个 spec requirement 到实现/测试的映射，记录离线与在线验收边界及 task-to-evidence。
- [x] 4.2 读取 binding 的 spec_standard_ref，依据 verification 创建 writeback.md，明确 CLI reference、tech stack 的更新内容及审计证据；标准无法访问时记录具体缺口。
- [x] 4.3 执行文档回写并记录结果；归档前按治理将 delta spec 回填永久 sitemap-driven-crawl 规范，检查能力注册一致性及 C10 同步状态。
