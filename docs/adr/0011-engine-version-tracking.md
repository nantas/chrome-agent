# 0011 — 2026-05-15-engine-version-tracking

## 状态

已接受（历史决策，从 docs/decisions/ 迁移至 docs/adr/）

chrome-agent 依赖多个外部引擎 CLI（Scrapling、Obscura、CloakBrowser），各引擎独立安装和版本管理。在 Obscura 从 v0.1.0 升级到 v0.1.2 时暴露以下问题：

1. **无集中式版本清单** — 各引擎的期望版本散落在不同脚本的硬编码值和 prose 文本中
2. **无安装后版本校验** — preflight 脚本只检查二进制是否存在，不比对版本号或文件哈希
3. **无版本驱动的更新触发** — 即使有新版，旧版仍通过存在性检查
4. **Doctor 不报告版本** — 无法通过一条命令看到所有引擎的版本状态
5. **Obscura 无 `--version`** — 二进制不支持版本参数，无法用常规方式检测

## Decision

建立集中式版本清单和自动检测/更新机制：

1. **`configs/engine-versions.json`** 作为唯一的版本真源，记录每个引擎的期望版本、检测方法和更新方式
2. **`scripts/engine-version-check.sh`** 统一检测脚本，支持：
   - 逐引擎检测（Scrapling 用 importlib、Obscura 用文件哈希/大小、CloakBrowser 用 Python 属性）
   - `--update` 触发自动更新
   - `--json` 机器可读输出
   - `--engine <name>` 单引擎过滤
3. **Obscura 版本检测策略**：文件哈希 + 文件大小双校验，在清单中记录每个二进制的 expected_md5 和 expected_size
4. **Doctor 集成**：`runDoctor()` 调用 `engine-version-check.sh --json`，在 checks 中增加 `version_<engine>` 条目
5. **Preflight 改造**：`obscura-cli-preflight.sh` 从清单读取版本号，已安装时做哈希比对

## Consequences

### 正面

- 版本升级时只需修改 `configs/engine-versions.json` 一个文件
- Doctor 一条命令即可看到所有引擎版本状态
- Obscura 升级只需更新清单中的哈希值，无需修改脚本逻辑
- 为未来 CI 自动化版本检查奠定基础

### 注意

- Obscura 版本更新时必须同步更新清单中的 `expected_size` 和 `expected_md5`
- 清单中 `expected_version` 字段目前仅用于日志和 doctor 显示，Obscura 的实际匹配依赖哈希
- CloakBrowser 暂未安装，其版本检查结果为 `missing`/`needs_update`
- Scrapling 版本更新依赖 uv 重装 venv，不可精确锁定子版本
