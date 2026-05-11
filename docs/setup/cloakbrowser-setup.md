# CloakBrowser 安装与配置

CloakBrowser 是 chrome-agent 的高保护页面引擎（rank 4, `playwright_stealth` 类型），提供 57 个 C++ 源码级 Chromium patch，用于处理 Cloudflare Turnstile、reCAPTCHA v3、TLS 指纹检测等高级反爬场景。

## 安装

```bash
pip install cloakbrowser
```

首次使用时 CloakBrowser 会自动下载 ~200MB 的 patched Chromium binary 到 `~/.cloakbrowser/chromium-{version}/`。

## 验证安装

```bash
# 方法 1: 使用 preflight 脚本
bash scripts/cloakbrowser-preflight.sh

# 方法 2: 直接检查模块
python3 -c "from cloakbrowser import launch; print('OK')"
```

## macOS 首次使用

如果 macOS Gatekeeper 阻止 Chromium 运行：

```bash
xattr -cr ~/.cloakbrowser/chromium-*/Chromium.app
```

## 版本说明

| 平台 | Chromium 版本 | 备注 |
|------|--------------|------|
| macOS (darwin-arm64/x64) | 145.0.7632.109 | 落后于 Linux/Windows |
| Linux (linux-x64) | 146+ | 推荐，指纹更新 |
| Windows (win-x64) | 146+ | 与 Linux 同版本 |

**建议**：生产环境优先使用 Linux 平台，Chromium 版本更新，指纹特征更接近主流。

## 资源需求

| 指标 | 值 |
|------|------|
| Binary 大小 | ~200MB |
| 内存占用 (RSS) | ~443 MB（含 Playwright node 进程） |
| 冷启动时间 | 4-8 秒 |
| 典型页面加载 | 1-5 秒 |

## 在 chrome-agent 中使用

CloakBrowser 自动集成在引擎 escalation chain 中：

```
scrapling-get → obscura-fetch → scrapling-fetch → cloakbrowser-fetch → chrome-devtools-mcp
```

当站点策略标记为 `protection_level: high` 或包含 `cloudflare-turnstile` 反爬引用时，系统自动选择 CloakBrowser。

也可通过 CLI 手动指定：

```bash
chrome-agent fetch <url> --fetcher cloakbrowser
```

## 许可证

- CloakBrowser Python wrapper: MIT
- Patched Chromium binary: **专有许可证**，不可重新分发
- 用户需自行通过 `pip install` 获取

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError: No module named 'cloakbrowser'` | 运行 `pip install cloakbrowser` |
| Gatekeeper 阻止 Chromium | `xattr -cr ~/.cloakbrowser/chromium-*/Chromium.app` |
| Binary 未下载 | 手动运行 `python3 -c "from cloakbrowser import launch; b = launch(); b.close()"` 触发下载 |
| 内存不足 | CloakBrowser 需要 ~443MB，确保系统有足够可用内存 |
| Turnstile 未解析 | 部分站点可能需要 headed 模式：`--no-headless` |
