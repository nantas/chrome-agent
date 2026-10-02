# Design

## Context

前轮内容准入已阻止将 Cloudflare 验证页视作正文，但真实 Explore 暴露其后的适配器和健康报告缺陷。设计以本 change 的 `engine-execution-contracts` 与 `engine-health-reporting` 为行为真源；保留既有准入、安装机制与 workflow Gate。

## Goals / Non-Goals

目标是让每个 fallback 使用真实 CLI 契约、在执行前完成所需预检，并让 doctor 和 Explore 忠实保留失败证据。可选引擎未安装与检查器自身故障必须可区分。

不升级引擎、不改站点策略、不增加 API 恢复通道、不自动连接用户 Chrome，也不承诺原站点一定返回正文。

## Decisions

### 1. Obscura 以 stdout 为 HTML 来源

修改 Explore 适配器，移除不支持的 `--output`。成功进程的 stdout 写入本次 attempt 独有的 HTML 文件，stderr 单独保存，不拼接进 HTML。非零退出、空 stdout 均为获取失败；成功获得 HTML 后仍调用既有正文准入。禁止读取旧 attempt 的文件来补本次失败。

优先修正薄适配层，不为不存在的参数增加通用兼容重试。具体超时沿用现有预算；超时保留阶段与有限长度的诊断摘要。

### 2. CloakBrowser 共用 shell preflight 契约

Explore 在选中 CloakBrowser 后调用既有 `scripts/cloakbrowser-cli.sh preflight`，复用其安装和路径解析机制。执行使用其 `RESOLVED_CLI_PATH`，不硬编码托管 Python；遵守 `CLOAKBROWSER_MANAGED_ROOT`。

Python 与 Node 分别保留薄调用适配，但共同以 shell preflight 输出为唯一安装/路径契约，避免跨语言重复实现安装器。对退出码、STATUS、路径存在及可执行性进行一致校验；预检失败或输出无效即记录 preflight 故障，不继续启动引擎。已安装路径不重复安装，缺失路径仅在实际选择 fallback 时按既有机制安装。doctor 的版本检查只观察，不触发 CloakBrowser 安装。实施时确认既有安装器未固定版本，因此让安装器读取 engine-versions.json 的 expected_version，以满足不升级引擎的边界；版本清单本身不变。

### 3. 版本报告完整，doctor 校验执行与数据

版本检查器隔离逐引擎异常，始终尽可能输出所有选中引擎记录。缺失可执行文件为 `not_installed`；启动异常、超时、版本解析失败分别记录，不以缺失替代未知。存在非健康结果时 `all_ok=false`，退出码遵守非健康报告约定。

Node 消费端同时检查进程结果、JSON 字段类型、引擎标识唯一性及选中引擎覆盖率。检查器路径缺失、启动失败、无效 JSON、遗漏记录或退出码与汇总矛盾，输出阻塞的 `version_check_failed`。完整且一致的非健康 JSON 即使伴随非零退出，也保留逐引擎诊断。错误摘要限长，完整可用证据链接到诊断文件。

检查范围由配置和明确的选择条件决定，不能用报告自身的空 engines 列表反向证明覆盖完整；全量检查配置非空时空报告必为错误。

### 4. 可选引擎 readiness 与整体结果分离

仅明确支持懒安装的可选 fallback 的已观察缺失可标记 `blocking=false`、`readiness=needs_preflight`，并给出安装预检指引；不能把任意版本不匹配、未知异常或必需引擎故障降为非阻塞。此时 doctor 返回 `partial_success`，版本报告仍然非健康。

仅当所有失败检查均显式非阻塞，工作流才可继续；既有 freshness/reload 和授权 Gate 保持有效。检查器自身故障默认阻塞。沿用现有结果 envelope，并给新增字段建立消费端测试，避免仅改变文字提示。

### 5. Explore 保留可复核尝试链

无论最终成功与否，输出实际尝试顺序、各 attempt 的阶段（preflight / process / admission）、退出码或不可用原因、HTML/诊断路径及 next_action。`engine_path` 不再因整体失败丢失已有尝试；`artifacts` 至少指向已落盘的诊断证据。

未执行的 devtools 标记 pending，与已执行失败区分，不计为成功引擎。内部适配器异常和内容不可用分别记录；继续遵循现有 handoff Gate，不为获得后续证据绕过已触发的停止条件。

## Validation Design

按 vertical slice TDD 先增加会暴露现有缺陷的测试，再修改对应实现：严格 argv/stdout 的可执行 fixture 验证 Obscura；临时 managed root 与受控 preflight/installer 验证 CloakBrowser；版本检查器和 Node consumer 各自覆盖缺失、异常、空/坏 JSON、覆盖不足及非零但合法报告。

补充真实已安装 Obscura 的 `fetch --help` 契约核对；可用时使用本地受控 HTTP 页面验证 stdout 获取。测试 fixture 不能替代这项真实接口证据。网络相关原站点复验单独记录，不作为稳定单元测试。

回归要求既有 challenge fixture 仍被拒绝，正常 HTML 可通过；随后按标准 doctor→explore 复验原 URL。若仍被挑战阻断，验收以适配器正确执行、状态准确、证据完整为准，不强求站点通关。

## Risks / Migration

- 首次选中缺失 CloakBrowser 可能下载依赖；沿用既有预检预算和失败报告，不加无限重试。
- doctor 从假 success 变为 partial_success/failure，可能暴露调用者忽略阻塞字段的问题；测试工作流消费契约并同步说明文档。
- 真实引擎或网络不可用时记录未完成的验证与原因，不能用模拟通过冒充线上复验。
- 保留既有 CLI envelope，新增诊断字段；无数据迁移。新增共享实现文件时按 C11 更新能力注册；未新增则不制造注册项。
- CLI/runtime/skill tracked files 若变更，按 C10 同步全局副本和 installed hash。引擎版本不变，不改版本哈希。
- 实施后补 verification/writeback，检查 capabilities，再按治理流程归档。工作区已有 package-lock 和站点目录不纳入本 change。
