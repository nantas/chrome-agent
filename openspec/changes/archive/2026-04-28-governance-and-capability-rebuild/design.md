# Design

## Context

本 change 的唯一交付物是"规划文档 + README 重写"，不涉及任何能力实现。规划文档作为后续 5 个 Phase 的引用锚点，README 立即对齐项目身份。

## Goals / Non-Goals

**Goals:**
1. 产出 `docs/governance-and-capability-plan.md` 总体规划文档
2. 重写 README.md 为服务全景说明

**Non-Goals:**
- 不做任何能力实现
- 不修改 AGENTS.md
- 不创建 outputs/ 目录
- 不修改 sites/ 文件

## Decisions

### Decision 1: 规划文档结构

```
docs/governance-and-capability-plan.md

1. 项目目标与服务身份
2. 当前状态
3. 能力全景图
   ├─ 对外能力（explore → fetch / crawl）
   ├─ 对内能力（site-strategy / anti-crawl-strategy / engine-registry / output-lifecycle）
   └─ 治理能力（binding / spec / writeback）
4. 阶段划分
   Phase 1 治理基础重建
   Phase 2 契约冻结
   Phase 3 策略库标准化
   Phase 4 引擎扩展治理
   Phase 5 安装链与清理闭环
5. 依赖关系图
6. 技术栈与工具链
7. 治理约束
```

每个阶段条目包含：名称、范围、交付物、需要的 specs/contracts、排他边界。

### Decision 2: README 定位

README.md 作为仓库的公开入口，聚焦于：
- 仓库身份（跨仓库网页抓取服务）
- 能力总览
- 目录结构说明
- Quick Start
- 链接到规划文档作为完整路线图

操作细节不放在 README 中（由 AGENTS.md + playbooks 承载）。

### Decision 3: 规划文档存放位置

放 `docs/` 根目录，不带日期版本号。作为项目长期引用锚点，不随时间轮转。

## Risks / Migration

- 规划文档发布后，如果后续 Phase 的 change 调整了阶段范围，需要更新规划文档
- 目前没有其他风险——本 change 不修改任何运行中的能力
