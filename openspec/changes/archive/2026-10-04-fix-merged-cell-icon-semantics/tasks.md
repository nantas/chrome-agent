# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 阅读两份 delta、必读架构与测试约定；核对两个前置 change 的 active/archive/提交状态及合并格 requirement 真源，快照工作区，记录本次修改边界。
- [x] 1.2 从 Crypt Keeper 源表提取自包含 fixture，重现延续格缺图标名称与 S5 or or；保存源格、首槽、副本和审计证据，确认旧正式产物也有该问题。

## 2. 核心实现任务

- [x] 2.1 RED：针对 strategy-schema delta 测试精确映射、空/缺省、错误类型、空键值/边缘空白/换行、未知字段，以及匹配失败不降级契约。
- [x] 2.2 GREEN：接入 table_options.merged_cell_icon_labels 校验、配置传递和能力声明，确保现有 transpose 配置兼容、错误含字段路径。
- [x] 2.3 RED：通过 convert_page_full 验证 Crypt Keeper colspan fixture：源图各一次，副本四状态名/概率/顺序准确；映射、alt、title、占位优先级及文件名/URL/通用名排除分别覆盖。
- [x] 2.4 GREEN：共享内核延续格克隆用文本替换图标，复用转义与单元格渲染，添加有来源依据的 DD2 精确映射；无域名分支，原格不变，Crypt Keeper S5 通过。
- [x] 2.5 RED：覆盖 rowspan 与组合 span、不同源节点同 URL、链接图标与同名标签、特殊字符、过滤图片、纯文本与普通格、嵌套表/表头/转置；保留真正新增重复词仍 fail 的 S5 反例。
- [x] 2.6 GREEN：补齐上述边界，保证行列/邻格/链接目的和资产次数；不放宽 S5、不增加页面白名单，每个边界测试通过后再继续。
- [x] 2.7 RED：在既有 explore/pipeline/crawl 等价测试中加入合并格配置 fixture，并验证旧转换 fingerprint 必须失效、新指纹可复用。
- [x] 2.8 GREEN：仅补必要共享配置传递并递增当前 converter contract revision，使镜像字节等价与缓存测试通过，不复制转换逻辑。

## 3. 收敛与验证准备

- [x] 3.1 以确定的配置/缓存清单离线重放 209 页至独立目录，禁止网络与覆盖正式产物；执行来源感知 batch audit，单独报告 Crypt Keeper S5、其他 fail/skip 和缺输入。
- [x] 3.2 独立比对图片 multiset、标题、链接目标、逐表行列/数值/顺序；所有文本变化必须对应源合并格图标投影并逐项审查未知名称占位，不以转换器输出作自证；确认后才更新 golden。
- [x] 3.3 运行 `.venv/bin/python -m unittest discover -s tests -v`、`node --test tests/*.test.mjs`、`.venv/bin/python scripts/test_runner.py site-samples --domain darkestdungeon.wiki.gg`；验证 Python 3.9 兼容、capabilities doctor、git diff --check；如实际改到 C10 tracked files 则执行全局同步。

## 4. 验证与回写收敛

- [x] 4.1 基于真实结果生成 verification.md，逐 scenario 映射测试与证据，记录全量预期变化、残留缺口及 cache revision；不得预先宣称 209 页全绿。
- [x] 4.2 解析并读取 binding.spec_standard_ref，生成 writeback.md 的本地字段映射、前置条件与目标，列明前置 change 的规范同步顺序。
- [x] 4.3 执行两份架构文档和 handoff 的摘要回写，补充 Crypt Keeper 是既有副本语义缺失的准确归因，保留历史记录；记录时间/执行人/结果，归档另行执行。

## 实施中发现（已获确认）

用户确认扩展精确邻接去重；规范和 design 已同步。先补 adjacent-exact-label RED，再实现 GREEN，随后重跑全量与样本。保留初次 17 页失败证据，不改变 S5 检查规则。
