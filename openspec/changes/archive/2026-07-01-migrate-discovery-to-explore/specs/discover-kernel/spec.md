# Specification Delta

## Capability 对齐（已确认）

- Capability: `discover-kernel`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: Stage 3 drift 7-9: 5 个发现模块移到 explore, pipeline 移除 discover 阶段

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件

## REMOVED Requirements

### Requirement: pipeline-discover-phase

**Reason**: Pipeline 不应自行发现页面。页面清单的唯一来源是 strategy 中 explore 冻结的 manifest。`--from-manifest` 成为 pipeline 获取 manifest 的唯一路径。

**Migration**: Pipeline 调用方必须使用 `--from-manifest <path>` 参数。Explore 工作流（`probe → discover → scaffold → freeze`）生成 manifest 后，pipeline 直接消费。

### Requirement: discovery-strategy-routing

**Reason**: `orchestrator.py` 中的 `_dispatch_discovery` 路由逻辑（homepage vs allpages vs auto）属于 explore 职责。探索由 explore CLI (`scripts/explore/main.py`) 驱动，pipeline 不参与发现策略选择。

**Migration**: 发现策略选择移至 explore 入口。Pipeline 接受已生成的 manifest 即可。

## MODIFIED Requirements

### Requirement: pipeline-manifest-source

Pipeline SHALL obtain page manifest exclusively from `--from-manifest <path>` or from an existing `page_manifest.json` in the output directory. Pipeline SHALL NOT generate manifests internally.

#### Scenario: pipeline-requires-manifest
- **WHEN** pipeline is invoked without `--from-manifest`
- **AND** no `page_manifest.json` exists in the output directory
- **THEN** pipeline SHALL exit with an error indicating the manifest is required

#### Scenario: pipeline-accepts-from-manifest
- **WHEN** pipeline is invoked with `--from-manifest path/to/page_manifest.json`
- **THEN** pipeline SHALL load and use that manifest for fetch/convert/assemble phases

## ADDED Requirements

### Requirement: explore-discovery-modules

Explore SHALL contain all discovery-related modules for generating page manifests: `discovery_homepage.py`, `discovery_allpages.py`, `discovery.py` (strategy interface), `homepage_parser.py`, and `page_assigner.py`.

#### Scenario: explore-can-discover
- **WHEN** explore workflow runs discovery
- **THEN** it SHALL use the modules in `scripts/explore/` without importing from `scripts/pipeline/` for discovery logic
- **AND** cross-module imports (e.g., `scripts.pipeline.client.ApiClient`) SHALL use absolute import paths

#### Scenario: tests-still-pass
- **WHEN** existing tests that reference moved modules are updated with new import paths
- **THEN** all tests SHALL pass with identical behavior to pre-move
