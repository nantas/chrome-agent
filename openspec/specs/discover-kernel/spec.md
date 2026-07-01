# discover-kernel

## Overview

Defines the separation of concerns for page discovery: explore owns discovery logic and generates page manifests; pipeline consumes manifests exclusively via `--from-manifest`.

## Requirements

### Requirement: pipeline-manifest-source

Pipeline SHALL obtain page manifest exclusively from `--from-manifest <path>` or from an existing `page_manifest.json` in the output directory. Pipeline SHALL NOT generate manifests internally.

#### Scenario: pipeline-requires-manifest
- **WHEN** pipeline is invoked without `--from-manifest`
- **AND** no `page_manifest.json` exists in the output directory
- **THEN** pipeline SHALL exit with an error indicating the manifest is required

#### Scenario: pipeline-accepts-from-manifest
- **WHEN** pipeline is invoked with `--from-manifest path/to/page_manifest.json`
- **THEN** pipeline SHALL load and use that manifest for fetch/convert/assemble phases

### Requirement: explore-discovery-modules

Explore SHALL contain all discovery-related modules for generating page manifests: `discovery_homepage.py`, `discovery_allpages.py`, `discovery.py` (strategy interface), `homepage_parser.py`, and `page_assigner.py`.

#### Scenario: explore-can-discover
- **WHEN** explore workflow runs discovery
- **THEN** it SHALL use the modules in `scripts/explore/` without importing from `scripts/pipeline/` for discovery logic
- **AND** cross-module imports (e.g., `scripts.pipeline.client.ApiClient`) SHALL use absolute import paths

#### Scenario: tests-still-pass
- **WHEN** existing tests that reference moved modules are updated with new import paths
- **THEN** all tests SHALL pass with identical behavior to pre-move

---

_Synced from change: migrate-discovery-to-explore (2026-07-01)_
