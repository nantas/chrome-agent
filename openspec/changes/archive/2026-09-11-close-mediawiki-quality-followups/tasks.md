# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 核对 4 个 spec delta 与工作区现状的差距：`infobox.py` / `convert.py` 补丁已在（收编即 GREEN），缺测试；`strategies/__init__.py` 缺 `/revision/` 分支；策略资产缺提交。验证：`git diff --stat` + 逐 spec 对照。
- [x] 1.2 前置确认：`python3 scripts/test_runner.py unit` 与 `site-samples` 在收编前基线全绿（已复核：170 OK / 19 OK）。

## 2. 核心实现任务

### Slice A — infobox 单元格转义测试（spec: extract-kernel/infobox-table-cell-escaping）

- [x] 2.1 RED：`tests/test_convert_equivalence.py` 新增断言——含多段 value（`\n`）与裸 `|` 的 infobox HTML，经 `convert_page_full` 与 `convert_single_page` 输出均为单行表格行、含 `<br>`、无断行（先对补丁 revert 验证会失败，再恢复）。验证：`python3 -m unittest tests.test_convert_equivalence -v`。
- [x] 2.2 GREEN：确认工作区 `infobox.py` 补丁使断言通过（补丁已存在，本任务是测试落地）。

### Slice B — H1 判定与 hero URL 测试（spec: pipeline-convert-phase/conversion-output-format）

- [x] 2.3 RED：`tests/test_convert_equivalence.py` 新增断言——① 正文以 `## Infobox` 开头的页面输出首行为 `# {title}`、已有 `# Title` 时不重复；② infobox 含 CDN 图片的页面输出含该 CDN URL 且不含 `/images/` 或 `Special:Redirect` 构造路径；③ 无可用 http 图片时省略 hero 注入；④ wikitext 路径（raw 仅含 `rendered_html` + `images`）仍注入 hero。验证：`python3 -m unittest tests.test_convert_equivalence -v`。
- [x] 2.4 GREEN：确认 `convert.py` 补丁（含 `CONVERTER_CONTRACT_REVISION=4`）使断言①②③通过；补 wikitext 调用点回退（`html or raw.get("rendered_html")`）使断言④通过——业务消费方新版补丁存在此回归：wikitext 路径 raw 无 `html` 键，hero 被静默丢弃。

### Slice C — L6 `/revision/` 解析（spec: pipeline/l6-image-filename-parsing）

- [x] 2.5 RED：`scripts/pipeline/tests/` 新增 `validate_images` 文件名解析测试——CDN `/revision/.../scale-to-width-down/111?cb=` URL 解析为 `File:DivineIcon.png`；普通 URL 与 `Special:Redirect` URL 行为不变。验证：`python3 -m unittest scripts.pipeline.tests.<new> -v`。
- [x] 2.6 GREEN：`scripts/pipeline/strategies/__init__.py` else 分支加 `/revision/` 切分（`url.split("/revision/")[0].split("/")[-1]`），测试通过。

### Slice D — 策略资产收编（spec: strategy）

- [x] 2.7 核对 growagarden 冻结产物自洽：`validate_extraction` 返回空、`site-samples --domain growagarden.fandom.com` 通过、freeze-report 在场。验证：schema 校验 + 回归命令。
- [x] 2.8 核对 mobalytics 收编完整性：`strategy.md` + `freeze-report.json` 内容与冻结时一致、registry 条目 `file` 字段指向存在路径。验证：`git status` + 字节比对。

### 提交拆分（design 决策 4）

- [x] 2.9 Commit ①：`infobox.py` + `convert.py` + `strategies/__init__.py` + 两处测试文件（代码修复）。
- [x] 2.10 Commit ②：`sites/strategies/growagarden.fandom.com/*`（含 freeze-report.json）。
- [x] 2.11 Commit ③：`sites/strategies/mobalytics.gg/*` + registry.json 的 mobalytics hunk。

## 3. 收敛与验证准备

- [x] 3.1 全量回归证据：`unit`（170+ 新增）、`site-samples` 全域、`chrome-agent doctor`；C10 免除声明（无 `.mjs` 改动）。
- [x] 3.2 L6 行为变化记录：Fandom 域 unavailable 条目减少属预期，写入 verification。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）。
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）。
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）

## 5. 独立验证（opsx-verify subagent）修复

- [x] 5.1 W1：hero resolver 根相对 src 补全（`image_handling.base_url` 回退 domain）+ 双分支测试
- [x] 5.2 W2：selectolax 路径单元格转义直接断言（Node 输入 + inline renderer）
- [x] 5.3 W3：`_image_file_title` 补 `/thumb/` 分支 + spec 口径收窄 + 测试
- [x] 5.4 W4：`cmd_unit` 补 `scripts/pipeline/tests` 发现范围（golden 守护进默认套件）
- [x] 5.5 S1/S2/S3：防御注释、design 偏离记录、verification HEAD 修正；spec/design/verification 同步。
