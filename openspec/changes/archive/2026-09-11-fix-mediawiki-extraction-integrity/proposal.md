# Proposal

## 问题定义

Grow a Garden 交接暴露了生产抽取的数据完整性缺口。HEAD `d10858d` 已修复旧报告 D1–D7，本 change 不重复恢复 discovery 或改回 pipeline discover。

1. CV4 的 `_process_html_page()` 在提取 infobox 前调用清理，容器被删除，字段静默丢失。同一合成 HTML 经 `convert_single_page()` 后缺失 `Seed Chance` 和 `## Infobox`，共享内核保留两者。
2. fetch 只检查标题是否缓存，convert 优先使用缓存 acquisition，resume 又可按完成状态和文件存在性跳过。切换策略为 `html_rendered` 仍会使用旧内容。诊断时 1,602 份缓存中 1,601 份是 hybrid 且无有效 HTML，不能仅重跑 convert/assemble 修复。
3. 工作区缓存标题补丁解决了斜杠写入失败，但多种标题仍碰撞且文件名反推标题不可靠；wikitable 守卫解决文首单表死循环，但文首表后还有第二表时会漏转第一表。
4. CLI 固定 600 秒子进程超时限制大站；freeze 的两空格序列化造成现有四空格 registry 全文件格式噪音。

## 范围边界

本次实现完整共享 HTML 编排、缓存身份/内容准入、转换恢复有效性、有限 wikitable 扫描修复、可配置 MediaWiki 子进程超时，以及稳定 registry 发布格式。测试采用自包含离线 fixture，实际站点样本作为补充。

不恢复已删除的 pipeline discover；不改变确认门、排除类别或旧 manifest 路径；不重写通用 wikitext 语法解析器；不修改 Obsidian 输出文件名规则。缓存键是内部存储协议，不等于输出路径。

不在创建/实施 change 时自动执行全站重抓、修改历史产物或 my-wiki ingest。交付恢复操作手册，说明新 manifest 审核、重新获取 HTML、新输出目录和质量验收。1,596 与 1,602 是两批历史观察值，不是固定验收页数。

## Capabilities

### New Capabilities

- `mediawiki-cache-integrity`: 规定缓存身份、无碰撞键、内容模式准入及保守兼容读取旧缓存。

### Modified Capabilities

- `convert`: 完整全页入口接受状态化 converter 上下文，保持 infobox、正文、链接和后处理等价。
- `extract-kernel`: 提取与拼回 infobox 始终经共享全页编排执行。
- `fetch-phase-cache-fastpath`: 快速路径和预过滤只跳过当前采集模式可用的缓存。
- `pipeline-convert-phase`: 拒绝不兼容缓存，并将 resume 绑定到有效输入和转换契约。
- `pipeline-converters`: wikitable 从文首开始按顺序扫描，终止且不漏掉后续表格或尾文。
- `cli`: 为 MediaWiki crawl 增加有界、可配置的子进程超时并保持结构化失败。
- `strategy`: freeze 保持 registry 的既有缩进、顺序及无关条目，维持验证与原子发布契约。

## Capabilities 待确认项

- [x] 用户已通过“按照你建议的方案创建 change”确认修复范围；以上 ID 是对现有 capability 的映射及缓存完整性新增契约。无阻塞项。

## Impact

- 代码：`scripts/lib/extraction/converter.py`、`infobox.py`、`scripts/pipeline/pipeline/cache.py`、`phases/fetch.py`、`phases/convert.py`、状态持久化、`scripts/pipeline/converters/wikitext_to_md.py`、`scripts/chrome-agent-cli.mjs`、`scripts/lib/mediawiki-crawl.mjs`、`scripts/explore/freeze.py`。
- 兼容性：保留 `convert_page_full(html, rules)` 调用方式；缓存读旧写新，无法证明身份/模式的旧数据视为 miss；旧 completed 状态不再独立证明输出可复用。
- 测试：在 `tests/` 扩展共享入口等价、缓存、fetch/convert 恢复、表格、CLI 和 freeze 行为测试；保持 Python 3.9+、stdlib unittest、Node ESM/node:test。
- 集成：保留已有未提交补丁的修复意图，补齐遗漏；不覆盖其他工作区改动。注意与 `obsidian-safe-filenames` 同文件修改的合并边界。
- 文档、全局同步与能力注册检查按 binding；本轮不触发全局部署。

## 关联绑定

- 关联 binding: [binding.md](binding.md)。
- 标准页：`docs/GOVERNANCE.md`；项目页：目标架构、pipeline flow、converter architecture。
- 回写目标与同步协议统一由 binding 定义；后续行为规范以本 change 的 `specs/` 为准。
