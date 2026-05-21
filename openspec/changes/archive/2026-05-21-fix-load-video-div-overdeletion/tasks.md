# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖范围：`specs/video-embed-cleanup.md` 覆盖了 video-embed-div-cleanup-scope 需求
- [x] 1.2 确认依赖前置条件：无外部依赖，仅需修改 `scripts/lib/extraction/converter.py` 一处

## 2. 核心实现任务

- [x] 2.1 替换 `clean_html()` 中 "Load video" div 文本匹配循环为精确 CSS 选择器
  - 文件：`scripts/lib/extraction/converter.py` L260-270
  - 将 `parser.css("div")` + `text(deep=True)` 匹配替换为针对 `div.embedvideo-wrapper`、`div.embedvideo-consent`、`div.embedvideo-overlay`、`div.embedvideo-loader` 的精确选择器
  - 完成标准：编译通过，无语法错误

- [x] 2.2 本地验证：对 `Endings` 页面缓存执行转换并确认输出完整性
  - 从 `.cache/mediawiki/bindingofisaacrebirth.wiki.gg/Endings.json` 读取缓存
  - 调用 `convert_body()` 并确认输出 markdown 长度 > 5000 字符（原始页面 ~18K 文本）
  - 完成标准：输出包含 22 个结局的标题和描述

- [x] 2.3 全量验证：对全部 99 个缓存页面执行 clean_html 并确认无 output 为空
  - 遍历所有缓存文件，对每个执行 `merge_tooltip_links → clean_html → convert`
  - 确认 clean_html 输出长度 > 100（排除空页面）
  - 完成标准：0 个页面被清空（之前为 20 个）

## 3. 收敛与验证准备

- [x] 3.1 重跑 `boi-100-baseline.sh --output=outputs/test-100-extraction-v3` 到干净目录
  - 完成标准：pipeline 正常完成，无异常退出

- [x] 3.2 对比新旧输出的 validation_report.json
  - 确认 broken_links 未增加
  - 确认 empty_content ≤ 1（仅 modes/index.md）
  - 确认受影响的 20 个页面均有实质内容
  - 完成标准：无回归

- [x] 3.3 更新 `tests/fixtures/boi-crawl-100-validation-baseline.json`
  - 使用 `--update-baseline` 或手动更新基线为最新 validation report 的值
  - 完成标准：基线文件已更新，后续 `boi-100-baseline.sh` 运行无回归

## 4. 验证与回写收敛

- [x] 4.1 生成 verification.md：记录 spec → implementation 对应关系和测试证据
- [x] 4.2 确认无需 writeback（纯内部 bug fix）
