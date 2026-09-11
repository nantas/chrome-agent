# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 对照四份 `specs/*/spec.md` 建 requirement/scenario→测试/实现映射，记录diagnosis D1-D7与列表标记缺口；核对cli/strategy原合并spec的精确回填目标。
- [x] 1.2 记录git基线与现有用户修改，读P0及相关playbook，确认Python3.9+/Node ESM环境、离线fixture和站点样本可用；列出旧extraction配置受影响域名，不改历史产物。

## 2. 核心实现任务

### Slice A — 清单消费边界（discover-kernel / cli manifest-input-compatibility）

- [x] 2.1 RED：在tests/用unittest/node:test覆盖缺manifest先于probe失败、pipeline discover无论有无manifest均拒绝、v2字段/版本/domain/fingerprint错误、无版本清单精确列表匹配内存适配、歧义拒绝/孤立content skip、源文件字节和目标路径不变。
- [x] 2.2 GREEN：实现共享清单schema/兼容校验，前置公共CLI与pipeline消费校验；去掉pipeline无效discover成功路径；保留scope与旧路径，不重发现、不写输入；通过2.1测试。

### Slice B — 冻结策略发现公共链（discover-kernel / cli Phase-based execution）

- [x] 2.3 RED：公共CLI离线spawn/API stub覆盖冻结allpages/homepage策略路由、无完整probe/scaffold调用、discovery-only含--yes均不抽取、all默认确认停止、--yes完整成功续跑、partial不自动抽取、冲突选项拒绝。
- [x] 2.4 GREEN：接通explore薄枚举入口与allpages/homepage内核；公共crawl分发并写run artifacts，pipeline保持manifest-only；--phase discover仅公共兼容alias；通过2.3测试。

### Slice C — 页面/列表资格与输出（discover-kernel）

- [x] 2.5 RED：真实枚举+assemble离线fixtures覆盖ns0未分类Misc、ns14/ns3000/StS前缀不变、已分类不变、canonical列表纳入与标记、排除/缺失/孤立content skip、重定向/路径冲突、真实index正文及链接可达而非generic替代。
- [x] 2.6 GREEN：两条发现路径输出v2列表资格与skip reasons，完善身份/排除判定、去重/冲突处理及限定Misc兜底；装配和链接索引使用同一资格契约；通过2.5测试。

### Slice D — 真实summary与失败范围（discover-kernel）

- [x] 2.7 RED：覆盖最终目录计数相等、真实/自动index一致、过滤计数、失败率分母、未知null、估时basis、相对artifact路径、partial与全失败不可伪success。
- [x] 2.8 GREEN：内核返回可计量outcomes并聚合统一summary，补失败/未知说明与confirmation metadata；不硬编码1596或固定秒数为实测；通过2.7测试。

### Slice E — 错误与fallback语义（cli）

- [x] 2.9 RED：node:test对公共MediaWiki CLI模拟exit20、策略错误、status=null/error/signal/timeout、外部网络故障；断言内部handoff、原stderr/mode保留、无Scrapling错误降级、允许降级时scope/path保持。
- [x] 2.10 GREEN：实现subprocess分类并复用internalFailure信封；不兼容discoveryOnly/fromManifest的后端停止；结构化保留上游和fallback决策；通过2.9测试。

### Slice F — extraction统一验证（explore-architecture-gate / strategy Extraction）

- [x] 2.11 RED：unittest覆盖cleanup非list/dict条目、unknown op、legacy text_normalization、dead nested/top-level key、有效shared op覆盖、Gate不抛TypeError、生产入口无网络前失败、consumer/registry不一致失败。
- [x] 2.12 GREEN：共享schema与实际操作声明供Gate/scaffold/freeze/生产消费复用；先shape/name后audit，更新共享consumer inventory与结构化诊断；通过2.11测试。

### Slice G — Fandom模板及Neon配置迁移（strategy）

- [x] 2.13 RED：以受控HTML/Markdown fixture验证lazyload/edit/TOC/ambox/image-wrapper及normalizer实际行为，覆盖模板实例schema检查；记录当前失败，避免只断言操作名。
- [x] 2.14 GREEN：按实际consumer迁移Fandom模板和neon规则，删除死描述字段并校验相关嵌套配置，保留用户站点改动；通过2.13测试，不重生成历史批量输出。

### Slice H — bootstrap草稿与freeze发布（strategy）

- [x] 2.15 RED：离线临时repo覆盖跨游戏bootstrap白名单、目标API/image域名、无来源topic/version/taxonomy冒充、invalid profile失败、新draft无生产registry、旧Bootstrapped标记拒绝、旧无标记冻结策略schema通过兼容、freeze/re-freeze失败保留marker及registry、发布故障回滚。
- [x] 2.16 GREEN：实现draft metadata/明确缺项输出、统一资格验证与可回滚freeze发布，生产lookup仅接受registry登记且非draft的合法策略；缺registry不得作为绕过freeze的资格；通过2.15测试。

## 3. 收敛与验证准备

- [x] 3.1 整理公共CLI离线完整discovery→confirmation→manifest extraction证据，确认无完整站点重测/网络测试依赖、无历史文件修改、分类目录/实际列表索引保持；记录最终md数与输入页数不同的原因。
- [x] 3.2 运行 `python3 -m unittest discover -s tests -v`、相关 `node --test`；检验Python3.9兼容、.mjs纯ESM/顶层function；修复真实回归后保存命令与结果。
- [x] 3.3 运行 `python3 scripts/test_runner.py site-samples --domain growagarden.fandom.com`、`--domain neonabyss.fandom.com` 及模板影响域名的样本回归；缺fixture/失败明确记录，不能把skipped当通过，不抓历史批次。
- [x] 3.4 按C11更新 `configs/capability-registry.yaml` 对新增实现/共享consumer的已有能力声明，避免重复注册镜像，运行 `doctor --check capabilities` 并保存证据。
- [x] 3.5 按C10/全局安装Case6同步runtime→全局launcher、skill→全局skill，installed-hash刷新当前git HEAD；CLI仅为同步触发器，不复制成runtime；记录全局一致性与doctor结果。
- [x] 3.6 列出进入verification的requirement→实现→测试证据及writeback差异清单；确认没有实施历史manifest/Misc批量迁移或my-wiki回灌。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实施结果生成verification.md，覆盖全部scenario和task证据，不把规划校验当实现完成。
- [x] 4.2 按binding读取治理标准，基于verification生成writeback.md，列出原合并spec精确回填映射及架构/CLI/策略/能力文档同步目标。
- [x] 4.3 执行writeback并记录证据：回填delta到指定原文件，纠正pipeline discover旧表述及bootstrap继承规范；同步涉及的architecture/AGENTS/CONTEXT，执行OpenSpec严格校验与归档前capabilities检查。
