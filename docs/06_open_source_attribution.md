# Open Source Attribution and Provenance

## Upstream record

| Field | Value |
|---|---|
| Project | SupplyChainAgent |
| Upstream repository | `https://github.com/HIT-ICES/SupplyChainAgent.git` |
| Baseline commit | `3993cf08e197164885cbc8c2a2195f4442c3470c` |
| Local baseline tag | `upstream-baseline` |
| Package lineage declared in metadata | AgentSociety (`https://github.com/tsinghua-fib-lab/agentsociety`) |
| License | Apache License 2.0 |
| Copyright notice in LICENSE | Copyright 2025 FIB LAB, Tsinghua University |
| NOTICE file | None found at baseline |

## Upstream-derived code

At Phase 0, all tracked code and assets present at baseline commit `3993cf0` are treated as upstream-derived unless a later commit explicitly records a new origin. This includes:

- `agentsociety/` runtime, agents, memory, simulation, web API and storage;
- `SupplyChainAgent/enterprise/` custom enterprise simulation and APIs;
- `firmagentsql/` persistence and analytics;
- `neo4j/` generation/import scripts and sample datasets;
- `frontend/` React application and public assets;
- root packaging, Docker, scripts, documentation and images.

FactoryOps additions and modifications must remain distinguishable through Git history and, where distributed, appropriate notices in modified files or accompanying documentation.

## Apache-2.0 obligations for redistribution

The practical obligations recorded here are:

1. provide recipients a copy of the Apache-2.0 license;
2. add prominent notices to modified files stating that changes were made;
3. retain relevant copyright, patent, trademark and attribution notices from upstream source;
4. if an upstream NOTICE file is later introduced, reproduce its relevant notices in the permitted locations;
5. do not imply trademark rights or endorsement;
6. any additional terms for FactoryOps modifications must remain compatible with the upstream license.

This document is an engineering record, not legal advice.

## Phase 0 modifications

The Windows baseline commit changes packaging, dependency declarations and repository-relative path resolution, and removes one unused Windows-incompatible import. Separate architecture documents are original Phase 0 work. Original LICENSE and attribution material were not removed.

## Required future practice

- Keep `LICENSE` in source and distributions.
- Keep this provenance document current with baseline and imported modules.
- Mark materially modified upstream files and describe modifications in release notes.
- Inventory third-party Python/npm/container/model/document licenses independently.
- Do not assume generated output, pretrained models or enterprise documents inherit this repository's Apache-2.0 license.
- Before public release, run license/SBOM and secret-scanning checks.

## Publication status

GitHub Push Protection initially rejected the upstream history due to a Mapbox secret classification in historical commit `e8da7282b5fc22fb4b19ded01b6070a05d033c45`, file `frontend/src/pages/Replay/Deck.tsx`. A read-only Mapbox validation confirmed that the value is a valid `pk` public access token rather than an `sk` secret token. With explicit repository-owner approval, the finding was marked as a false positive. Branch `feat/factoryops-rearchitecture` and tag `upstream-baseline` are now published to `origin`; the upstream commit graph remains unchanged and this attribution record remains intact.
