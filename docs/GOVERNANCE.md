# GOVERNANCE.md — chrome-agent 治理工作流

> 本文档解释 chrome-agent 仓库的文档体系设计、各文档类型的职责与生命周期，以及如何维护治理纪律。
> 如果你不确定该创建哪个文档、更新哪些文件、或者为什么有两种决策记录格式——读这份文件。

## 1. 文档体系全景

```
                    ┌──────────────────────────────┐
                    │         AGENTS.md             │
                    │  (入口：SSOT Map + 必读)       │
                    └──────────┬───────────────────┘
                               │ 指向
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   CONTEXT.md    │  │  docs/adr/      │  │ openspec/specs/ │
│  (领域语言)      │  │  (架构决策)      │  │  (能力行为规范)   │
│  CONTEXT-MAP.md │  │  NNNN-slug.md   │  │  <cap>/spec.md  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │          ┌─────────┴─────────┐          │
         │          ▼                   ▼          ▼
         │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
         │  │ architecture/│   │  playbooks/  │   │   setup/     │
         │  │ 01-08.md     │   │  (操作手册)   │   │  (环境配置)   │
         │  └──────────────┘   └──────────────┘   └──────────────┘
         │
         └─────── 术语一致性 ──────▶ 所有其他文档
```

**依赖方向**：
- `AGENTS.md` 引用所有文档，是入口
- `openspec/specs/` 是行为规范真源——冲突时以它为准
- `CONTEXT.md` 定义领域语言——术语必须在所有文档中一致
- `docs/adr/` 记录 hard-to-reverse 的决策——回答"为什么这样做"
- `docs/architecture/` 是派生/教学文档——解释系统如何工作，不是规范真源
- `docs/playbooks/` / `docs/setup/` 是操作指南——告诉你怎么做

## 2. 各文档类型的职责与生命周期

| 文档类型 | 位置 | 职责 | 创建时机 | 更新时机 | 删除时机 |
|---------|------|------|---------|---------|---------|
| **入口** | `AGENTS.md` | SSOT Map + 必读索引 | 项目初始化 | 新增/删除文档类型、新增 Hard Constraint | 不删 |
| **领域语言** | `CONTEXT.md` | 术语定义 | `grill-with-docs` session 产出 | 新概念引入时 | 术语废弃后 |
| **架构决策** | `docs/adr/NNNN-slug.md` | hard-to-reverse 的设计决策 | 决策满足 ADR 三条件时 | 被新 ADR 取代时（标注 `superseded by ADR-NNNN`） | 被取代后保留 |
| **行为规范** | `openspec/specs/<cap>/spec.md` | 能力的 MUST/SHALL 行为契约 | openspec change 归档时，从 delta spec 回填 | 后续 change 修改该 capability 时 | capability 被废弃时 |
| **系统架构** | `docs/architecture/01-08.md` | 教学/解释文档 | 系统稳定后 | 架构变更后同步（否则文档撒谎） | 被更准确文档取代后 |
| **操作手册** | `docs/playbooks/*.md` | 操作步骤指南 | 出现新的标准操作流程时 | 流程变更后 | 流程废弃后 |
| **环境配置** | `docs/setup/*.md` | 引擎/工具安装指南 | 新引擎引入时 | 安装方式变更后 | 引擎废弃后 |
| **治理工作流** | `docs/GOVERNANCE.md` | 本文档 | 治理体系需要解释时 | 文档体系变更后 | 治理体系重构后 |

## 3. Change 工作流完整链路

每个 openspec change 的生命周期：

```
proposal → specs → design → tasks → implement → verify → writeback → archive
                                                                         │
                                                                   ┌─────┴─────┐
                                                                   ▼           ▼
                                                            spec backfill   文档同步
```

### 各阶段产物与检查清单

| 阶段 | 产物 | 检查清单 |
|------|------|---------|
| **proposal** | `binding.md` + `proposal.md` | 能力清单已确认、范围明确、关联绑定就位 |
| **specs** | `specs/<cap>/spec.md`（delta） | 每个 capability 有 spec、requirement 使用 SHALL/MUST、scenario 覆盖 |
| **design** | `design.md` | 实现决策有依据、风险已识别 |
| **tasks** | `tasks.md` | TDD vertical slice、每个 task 可验证 |
| **implement** | 代码变更 | 每个 vertical slice 测试先于实现、测试通过 |
| **verify** | `verification.md` | 全量测试绿、doctor 绿、spec→code 映射完整 |
| **writeback** | `writeback.md` | 项目页面（architecture/setup/playbooks）同步更新 |
| **archive** | `openspec/changes/archive/` | **必须** 回填 delta spec 到 `openspec/specs/` |

### 归档时必须做的事（治理纪律核心）

1. **Delta spec → 永久 spec 回填**：`openspec/changes/<name>/specs/<cap>/spec.md` → `openspec/specs/<cap>/spec.md`
   - NEW capability：完整复制
   - MODIFIED capability：合并到现有 spec（追加 MODIFIED requirements）
   - ⚠️ **这是防止 73 个空壳 spec 目录再次出现的唯一屏障**
2. **项目页面同步**：按 `writeback.md` 的 targets 更新 `docs/architecture/`、`docs/setup/` 等
3. **C10 全局同步**（若涉及 tracked files）：手动 `cp` runtime/skill → `~/.agents/`，刷新 `installed-hash`

## 4. SSOT 冲突仲裁规则

当同一知识领域的两份文档冲突时：

| 冲突 | 谁赢 | 理由 |
|------|------|------|
| `openspec/specs/` vs `docs/architecture/` | `specs/` | specs 是行为规范真源，architecture 是派生文档 |
| `configs/engine-versions.json` vs `docs/architecture/06-engine-selection.md` 的版本描述 | `configs/` | 代码 & 配置 SSOT > 架构文档摘要 |
| `sites/strategies/<domain>/strategy.md` frontmatter vs `registry.json` | frontmatter | frontmatter 是权威来源（AGENTS.md §7） |
| `docs/adr/NNNN` vs `docs/architecture/` | ADR | ADR 记录实际做出的决策；architecture doc 若未同步则过时 |
| `CONTEXT.md` 术语定义 vs 任意文档中的术语使用 | `CONTEXT.md` | 领域语言词汇表是术语意义的唯一 SSOT |

## 5. 维护检查清单

### 每次 commit 前
- [ ] 新增 Python 依赖？→ 更新 `requirements.txt`（根）
- [ ] 修改 `scripts/chrome-agent-cli.mjs` 或 `scripts/lib/python-resolver.mjs`？→ 记得到时跑 C10 全局同步
- [ ] 改了 `configs/engine-versions.json`？→ 确认 `expected_version` + `expected_md5` + `expected_size` 同步（C4）

### openspec change 归档前
- [ ] 全量测试绿（`node --test` + `.venv/bin/python -m unittest`）
- [ ] doctor 全绿（`chrome-agent doctor --format json`）
- [ ] Delta spec 已回填到 `openspec/specs/`（**不要留空壳目录！**）
- [ ] `docs/architecture/*.md` 已同步（若涉及）
- [ ] `docs/setup/*.md` 已同步（若涉及安装方式变更）
- [ ] `CONTEXT.md` 已更新（若有新术语）

### 发 PR 前
- [ ] `AGENTS.md` SSOT Map 覆盖所有新增文档类型
- [ ] Reference Index 的优先级（P0/P1/P2）是否准确
- [ ] 无 `docs/decisions/` 残留（已迁移到 `docs/adr/`）

## 6. 反模式与常见错误

| 反模式 | 为什么错 | 正确做法 |
|--------|---------|---------|
| **创建空 spec 目录** | 空壳给 agent 虚假信号（以为有能力规范，实际没有） | 只在 delta spec 归档回填时创建；不预建占位目录 |
| **决策散落两处** | `docs/decisions/`（已废弃）和 `docs/adr/` 并存 | 统一到 `docs/adr/`；不创建新的 `docs/decisions/` 文件 |
| **文档撒谎** | `08-tech-stack.md` 写 pipeline "(none declared)" 但 converter.py 实际 import selectolax | 变更后立即同步文档；不"先改代码后补文档" |
| **在 architecture doc 里写决策** | 混合教学内容和决策记录，未来找不到决策依据 | 决策写 ADR，architecture doc 只引用 ADR |
| **跳过 writeback** | change 归档后 architecture/setup doc 过时，agent 读到过期信息 | 归档前必须按 writeback.md targets 更新项目页面 |
| **硬编码 python3** | PEP 668 锁定系统 Python，干净环境不可用 | 使用 `resolveAppPython(repoRoot)` 通过 `scripts/lib/python-resolver.mjs` 解析 |
| **pip install --break-system-packages** | 污染系统 Python | repo venv 懒触发（`scripts/repo-venv.sh preflight`）或引擎 managed venv |

## 7. 派生文档同步原则

所有架构文档、AGENTS.md §2 能力表和 openspec specs 均派生自 SSOT（代码/配置）。SSOT 变更后必须检查以下派生文档一致性：

| SSOT 变更类型 | 需同步的派生文档 | 验证方法 |
|--------------|-----------------|---------|
| `configs/capability-registry.yaml` 增删 entry | `AGENTS.md` §2 能力表、`openspec/specs/<cap>/spec.md`（归档后） | `doctor --check capabilities` |
| `scripts/lib/extraction/preprocessor.py` 新增 cleanup op | `configs/capability-registry.yaml` convert.cleanup_ops | `doctor --check capabilities` |
| `scripts/lib/extraction/infobox.py` 新增 handler | `configs/capability-registry.yaml` extract.infobox_handlers | `doctor --check capabilities` |
| `configs/engine-registry.json` 新增/修改引擎 | `configs/capability-registry.yaml` fetch.engines | `doctor --check capabilities` |
| 新增特殊 capability（如 card_stats） | `configs/capability-registry.yaml` extract.special_capabilities | `doctor --check capabilities` |

**同步检查时机**：
- 每次 `doctor --check capabilities` 运行时交叉校验（registry ↔ code ↔ specs ↔ AGENTS.md）
- openspec change 归档前必须 `doctor --check capabilities` 通过
- CI 未集成（当前无 CI）；归档前手动运行为强制性步骤
