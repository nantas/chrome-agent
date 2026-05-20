# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-tech-stack-dependency-graph`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 为技术栈文档增加组件依赖关系图和安装脚本链流程图

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: component-dependency-graph

The document `docs/architecture/08-tech-stack.md` SHALL include an ASCII diagram showing the dependency relationships between all system components.

The diagram SHALL illustrate:
- Node.js CLI layer → Python pipeline layer → Engine layer → Output layer
- The shared `lib/` layer providing strategy loading and extraction to both pipeline and explore
- External dependencies (Scrapling venv, Obscura binary, CloakBrowser pip)
- Data flow direction (one-way arrows)
- Each component labeled with its primary file path or install location

#### Scenario: dependency-graph-readability

- **WHEN** a new developer reads `08-tech-stack.md`
- **THEN** they SHALL understand which components depend on which within the first section
- **AND** the diagram SHALL appear near the "Runtime Dependencies" or new "System Architecture" section

### Requirement: install-script-chain-diagram

The document `docs/architecture/08-tech-stack.md` SHALL include an ASCII flowchart showing the execution order of installation and preflight scripts.

The flowchart SHALL illustrate:
- `install-chrome-agent-cli.sh` → registers CLI
- `scrapling-cli.sh preflight` → provisions Scrapling venv
- `obscura-cli-preflight.sh` → downloads Obscura binary
- `cloakbrowser-preflight.sh` → installs CloakBrowser pip package
- `engine-version-check.sh` → validates all engine versions
- Each script's managed path (where it installs artifacts)

#### Scenario: install-chain-readability

- **WHEN** setting up a new environment
- **THEN** the developer SHALL understand the correct execution order of all preflight scripts
- **AND** the diagram SHALL appear in the "External Engine Dependencies" section
