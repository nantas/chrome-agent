# Specification: fetch

## Capability 对齐

- Capability: `fetch`
- 4 维坐标: `(capability=fetch, execution_path=mirrors, strategy_variant=none, input_format=api|html|browser)`
- 镜像模型: 同一语义（获取内容），不同引擎/协议，分别实现
- 合并: `.mjs` mediawiki-api fetch → pipeline F1 统一

## 架构声明

```
Fetch 能力
├── kernel
│   ├── pipeline MediaWiki API: scripts/pipeline/pipeline/phases/fetch.py
│   ├── pipeline CDP: scripts/pipeline/pipeline/phases/fetch_cdp.py
│   └── explore probe: scripts/explore/probe_chain.py (多引擎探测)
├── 基础设施 (不注册为能力):
│   ├── chrome-agent-cli.mjs runEngineFetch() — 引擎路由
│   └── 各引擎适配器 (runScraplingFetch, runCloakbrowserFetch, etc.)
└── 引擎注册: configs/engine-registry.json + configs/engine-versions.json
```

## 已有行为规范

| 规范 | 内容 |
|------|------|
| `openspec/specs/pipeline-fetch-phase/spec.md` | Pipeline fetch 阶段流程 |
| `openspec/specs/mediawiki-api-contract/spec.md` | MediaWiki API 调用契约 |

## ADDED Requirements

### Requirement: unified-mediawiki-fetch-kernel

All MediaWiki API fetch operations SHALL route through `scripts/pipeline/pipeline/phases/fetch.py` as the single kernel. The `.mjs` Node.js layer SHALL delegate via subprocess rather than implementing its own API client.

#### Scenario: mjs-delegates-to-fetch-kernel
- **WHEN** `.mjs` needs to fetch a MediaWiki page
- **THEN** it SHALL call the pipeline fetch kernel (via subprocess or import)
- **AND** SHALL NOT spawn `standalone.py` for page fetching

### Requirement: probe-chain-as-explore-fetch

`scripts/explore/probe_chain.py` SHALL remain the explore path's fetch implementation, probing multiple engines in serial order to discover which engine can successfully fetch this site.

#### Scenario: probe-chain-discovers-viable-engine
- **WHEN** an explore operation needs to fetch a page
- **THEN** probe_chain SHALL try engines in order until one succeeds
- **AND** return the successful engine name and fetched HTML
