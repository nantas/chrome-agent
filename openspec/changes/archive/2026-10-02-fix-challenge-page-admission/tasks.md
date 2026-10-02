# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 对照 specs/fetch-content-admission/spec.md、specs/explore/spec.md 与 design，建立每个 scenario 到调用边界的覆盖表；读取 CLI/pipeline/shared-library 必需架构文档及全局安装 playbook。
- [x] 1.2 盘点 runEngineFetch/直接 adapter、sample、API HTML、CDP cache、convert resume 的实际消费者，记录每条 HTML 成功入口；保留已有工作区改动。优先 LSP，不可用则记录检索替代。
- [x] 1.3 从本地 wiki.gg 原始产物提取无 token 的最小 fixture，放 tests/fixtures；加入正常文章/嵌入组件对照，确认不依赖 outputs 或真实网络。

## 2. 核心实现任务

按编号顺序完成每一对 RED→GREEN 后再进入下一片，不集中先写全部测试。

- [x] 2.1 RED：unittest 用 captured-challenge-with-successful-process 场景证明真实 probe adapter 在退出 0、HTTP 200/未知时错误放行。
- [x] 2.2 GREEN：实现共享 content_admission 内核并接入 probe adapter，使 2.1 拒绝成功；输出 title/length/reason/signals 及真实 status 或 null。
- [x] 2.3 RED：加入 invalid-output、unknown-http-forbidden、normal-article-and-widget 用例，覆盖空/缺失/不可读、正常短页、代码引用及不带挑战证据的 403。
- [x] 2.4 GREEN：完善组合证据和错误分类，复用到 protection_identifier；CloakBrowser 最终判定不再因泛化标题词提前误杀，对正常/受阻页面通过同组反例。
- [x] 2.5 RED：真实 probe 链测试 challenge→正常正文与全失败/pending，断言后续引擎调用、成功 HTML 身份及诊断保留。
- [x] 2.6 GREEN：准入控制 fallback，拒绝页只保留诊断路径，修复 success_engine 与 html_content 的选择。
- [x] 2.7 RED：main 边界测试 no-admitted-content，断言 map/generate/convert 调用为零、原草稿字节不变、JSON outcome 与退出码一致。
- [x] 2.8 GREEN：main 提前停止并输出结构化 failure；仅 admitted 内容进入既有 API 发现及后续工作流。
- [x] 2.9 RED：node:test 启动真实 CLI/Python 入口，仅替换引擎/网络边界，覆盖 structured-content-failure、structured-partial-outcome、无效 JSON/未知异常仍走内部 handoff。
- [x] 2.10 GREEN：Node 按已知退出码及 outcome 保留结构化结果、证据和 next_action；无内容不报 completed、不推荐 freeze。
- [x] 2.11 RED：sample 真实消费链测试 rejected-sample，包含全部失败与好坏混合样本，断言不转换失败页、不因空 self-check 误报通过。
- [x] 2.12 GREEN：样本获取/转换准入与失败汇总接线，正常样本输出保持一致。
- [x] 2.13 RED：fetch/crawl 测试 selector-cannot-hide-challenge，覆盖直接 adapter 调用、ai-targeted/显式 selector、失败后遗留旧输出；断言每页仅一次远端获取。
- [x] 2.14 GREEN：实现应用层 JSON bridge，经 resolveAppPython 调用共享校验；HTML 准入后从同一文件做本地提取/转换，失败不发布成功 Markdown。
- [x] 2.15 RED：缓存/生产消费测试 cached-challenge-resume，覆盖 API HTML、CDP HTML、旧成功标记及 stale Markdown，断言当前 assembly 不收录失败页。
- [x] 2.16 GREEN：在现有 cache admission 和 resume 前组合内容校验，保留缓存身份/指纹与诊断文件，验证正常生产输出不变。
- [x] 2.17 RED：跨 probe/sample/CLI/生产的 normal-cross-path-equivalence 测试验证相同 fixture 判定一致，正常选择器内容与已有基线一致。
- [x] 2.18 GREEN：收敛重复分类规则、同步 configs/capability-registry.yaml 的共享模块/关系/等价测试声明，使跨路径测试及 capabilities doctor 通过。

## 3. 收敛与验证准备

- [x] 3.1 运行全部新增回归和 Python unittest discover、Node tests；执行原始本地 HTML 离线回放，记录每片 RED/GREEN 与最终拒绝结果。无需以真实站点是否解开挑战作为修复成功条件。
- [x] 3.2 运行 doctor 与 capabilities 检查；按 C10 同步全局 launcher/skill 副本并刷新 installed-hash，核对全局 CLI 指向本仓修改；保留用户既有改动。
- [x] 3.3 检查 Python 3.9 语法、ESM 顶层函数风格、无新增第三方测试依赖、无遗留调试日志；执行 OpenSpec strict validate 和 diff whitespace 检查。
- [x] 3.4 汇总各 scenario 的代码/测试位置、实际运行命令和目标版本；标记页面回写内容与未覆盖的挑战模板风险，禁止把未执行验证记为通过。

## 4. 验证与回写收敛

- [x] 4.1 基于真实结果生成 verification.md，包含 spec-to-implementation、task-to-evidence 和运行证据，不提前勾选实现任务。
- [x] 4.2 读取 binding 的 spec_standard_ref 后生成 writeback.md，列出项目页目标、摘要、前置条件与证据。
- [x] 4.3 执行绑定项目页回写并记录时间/执行者/结果；归档前合并新增准入规范与 Explore 完整 requirement 到指定真源，复核 doctor capabilities。
