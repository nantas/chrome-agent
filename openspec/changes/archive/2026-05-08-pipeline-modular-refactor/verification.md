# Verification

## 验证结论

状态：**实施完成** — 全量管线 smoke test 通过，CLI 子命令端到端验证通过。

## Spec-to-Implementation Coverage

| Capability | Requirement | 对应 Task | 验证方式 |
| --- | --- | --- | --- |
| `standalone-extraction` | `single-page-fetch-and-convert` | 2.22, 2.23, 2.29 | 对 slaythespire.wiki.gg 单页面执行 `fetch_and_convert`，验证输出 .md 文件包含 Card Stats + frontmatter |
| `standalone-extraction` | `reconvert-existing-file` | 2.22 | 对已有 HTML 文件执行 `reconvert_file`，验证覆盖后内容一致 |
| `standalone-extraction` | `cli-fetch-subcommand` | 2.25, 2.26, 2.29 | CLI `fetch` 子命令退出码 0，输出文件存在 |
| `incremental-reprocess` | `reprocess-specified-pages` | 2.22, 2.24, 2.30 | 对 3 个指定页面执行 reprocess，验证只处理指定页面 |
| `incremental-reprocess` | `reprocess-preserves-successful` | 2.24 | reprocess 前后对比非指定页面文件，验证未变更 |
| `incremental-reprocess` | `cli-reprocess-subcommand` | 2.25, 2.26, 2.30 | CLI `reprocess` 子命令退出码正确 |
| `unified-link-fixer` | `fix-links-in-directory` | 2.27, 2.28 | 构造测试 .md 文件包含各类问题链接，执行后验证修复统计 |
| `unified-link-fixer` | `preserve-fragment-anchors` | 2.28 | 测试 `#Section` 锚点保留 |
| `unified-link-fixer` | `strip-query-params` | 2.28 | 测试 `?action=edit` 剥离 |
| `unified-link-fixer` | `fix-double-md-suffix` | 2.28 | 测试 `.md.md` → `.md` |
| `unified-link-fixer` | `cli-fix-links-subcommand` | 2.25, 2.31 | CLI `fix-links` 子命令端到端 |
| `pipeline-converters` | `converters-as-independent-package` | 2.3-2.6 | 外部脚本直接 import 转换器，无 `ApiClient` 依赖 |
| `pipeline-converters` | `strategies-split-by-role` | 2.7-2.11 | 按角色从子模块 import 成功 |
| `pipeline-converters` | `backward-compatible-reexports` | 2.12, 2.13 | `from .strategies import HtmlToMarkdownConverter` 仍然可用 |
| `pipeline-converters` | `pipeline-orchestration-extracted` | 2.14-2.19 | `from .pipeline import run_pipeline` 成功 |
| `pipeline-converters` | `no-behavior-change` | 2.20, 2.21 | 全量管线 5 页面输出与重构前一致 |
| `pipeline-cli-entry` | `main-runnable-as-script` | 2.1 | `python3 scripts/mediawiki-api-extract --help` 成功 |
| `pipeline-cli-entry` | `cli-subcommand-routing` | 2.25, 2.26 | 5 个子命令路由正确 |
| `pipeline-cli-entry` | `chrome-agent-cli-fix` | 2.2, 2.32 | CLI crawl 触发 MediaWiki API 路径无 `ImportError` |

## Task-to-Evidence Coverage

| Task | 预期证据 | 收集方式 |
| --- | --- | --- |
| 2.1 | `--help` 输出截图 | bash 执行记录 |
| 2.2 | `spawnSync` 参数变更 diff | git diff |
| 2.3-2.6 | import 测试通过 | bash `-c` 输出 `OK` |
| 2.7-2.13 | import 测试通过 | bash `-c` 输出 `OK` |
| 2.14-2.19 | import 测试通过 | bash `-c` 输出 `OK` |
| 2.20 | 管线退出码 0，输出目录有 .md 文件 | bash 退出码 + `ls` 输出 |
| 2.21 | 5 个页面输出 diff（frontmatter + card stats 一致） | `diff` 或 `git diff` 对比 |
| 2.22 | import 测试通过 | bash `-c` 输出 `OK` |
| 2.23 | 单页面 .md 文件内容检查 | `head -20` 输出 |
| 2.24 | 指定页面文件时间戳更新、其他文件不变 | `stat` 时间戳对比 |
| 2.25-2.26 | 子命令帮助文本 | `--help` 输出 |
| 2.27-2.28 | 修复统计 + 修复前后 diff | bash 输出 |
| 2.29-2.31 | CLI 退出码 0 + 输出文件存在 | bash 退出码 + `ls` |
| 2.32 | chrome-agent crawl 成功运行 | CLI 输出日志 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| 管线输出目录 | `/tmp/smoke-test/` | 2.20, 2.21 (`no-behavior-change`) |
| 单页面输出 | `/tmp/strike-test.md` | 2.23, 2.29 (`single-page-fetch-and-convert`) |
| reprocess 输出 | `/tmp/reprocess-test/` | 2.24, 2.30 (`reprocess-specified-pages`) |
| import 测试 | bash 执行记录 | 2.3-2.19 (`converters-as-independent-package`) |

## 缺口与阻塞项

- 无自动化测试框架覆盖 — 依赖 smoke test 手动验证（已完成）
- slaythespire.wiki.gg rate limit 导致 7 页面失败（与重构前一致，非回归问题）
