# Phase 0 Baseline Runtime Report

Date: 2026-09-19 (Asia/Shanghai)

## Scope and truth criteria

This report records only behavior observed on the current Windows workstation. A process starting is not treated as a full pass unless its required dependency chain and a representative endpoint or page also worked. No API key, benchmark result, or successful service state has been fabricated.

## Git baseline

| Item | Value |
|---|---|
| Upstream | `https://github.com/HIT-ICES/SupplyChainAgent.git` |
| Origin | Previous development fork (history not migrated to the current repository) |
| Branch | `feat/factoryops-rearchitecture` |
| Upstream baseline commit | `3993cf08e197164885cbc8c2a2195f4442c3470c` |
| Initial branch commit | `3993cf08e197164885cbc8c2a2195f4442c3470c` |
| Local tag | `upstream-baseline` -> `3993cf08e197164885cbc8c2a2195f4442c3470c` |
| Initial worktree | Clean |

The first push of the branch and tag to `origin` was rejected by GitHub Push Protection. Historical upstream commit `e8da7282b5fc22fb4b19ded01b6070a05d033c45` contains a value classified as a Mapbox Secret Access Token in `frontend/src/pages/Replay/Deck.tsx`. The value is not reproduced here. A read-only check against Mapbox's official token endpoint confirmed that it is a currently valid `pk` public access token, not an `sk` secret token. With the repository owner's explicit approval, the finding was marked as a false positive; the branch and baseline tag were then published to `origin`. Upstream history was not rewritten and no push was made to `upstream`.

## Host environment

| Capability | Observed value | Assessment |
|---|---|---|
| OS | Windows 11, `10.0.26200`, 64-bit | Supported for Python/UI work, not for the bundled simulator binary |
| Python | 3.12.10 | Meets `>=3.11` |
| pip | 26.2.1 globally; isolated `.venv` created | PASS |
| Node.js | 24.19.0 | Newer than Dockerfile Node 20; dev server works |
| npm | 11.17.0 | Dependency install works |
| Docker CLI | 29.6.2 | Installed |
| Docker Compose | 5.3.1 | Installed; compose file parses |
| Docker engine | Desktop processes start, Linux engine does not answer | BLOCKED |
| Git | 2.55.0.windows.3 | PASS |
| Java | OpenJDK 21.0.9 LTS | Present; not used by baseline |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU, 8151 MiB | Present; baseline does not require it by default |
| RAM at Agent test | 24.9 GB total, about 3.6 GB available | Below runtime's hard-coded 12 GB available threshold |

Ports 5432, 6379, 59000, 7687, 7474, 8000, 8080, 5173 and 8265 were free after test processes were stopped. No baseline server was left running.

## Isolated environments and dependency installation

- Python environment: repository-local `.venv` (ignored by Git).
- Frontend environment: `frontend/node_modules` from `npm ci` (ignored by Git).
- Original editable Python install initially failed because `setup.py` always attempted to package an `agentsociety-sim` binary that exists only for Linux x86_64 and macOS arm64.
- After the minimal Windows packaging guard and dependency declarations, editable installation succeeded.
- `pip check`: PASS, no broken requirements.
- `python -m compileall`: PASS for `agentsociety`, `SupplyChainAgent`, `firmagentsql`, and `neo4j`.
- The environment used compatibility bounds matching the code and Compose era: MLflow 2.x, OpenAI Python 1.x, Transformers 4.x.
- `npm ci`: PASS, 596 packages installed. Audit reported 40 vulnerabilities: 1 low, 11 moderate, 27 high, 1 critical. They were not auto-fixed because a forced update could change behavior.

## Component matrix

| Component | Status | Command/port | Evidence and root cause | Migration impact |
|---|---|---|---|---|
| Docker engine | BLOCKED | Docker Desktop / named pipe | CLI installed; `dockerDesktopLinuxEngine` never became responsive | Establish a reproducible container host before integration testing |
| Compose definition | PARTIAL | `docker compose -f docker/docker-compose.yml config` | Parses successfully; services are PostgreSQL 17, Redis 7.2, MLflow 2.19 | Reuse concepts, harden configuration |
| PostgreSQL | BLOCKED | 5432 | Container could not start because Docker engine was unavailable | Required for WebUI and enterprise API integration |
| Redis | BLOCKED | 6379 | Same Docker blocker | Needed by legacy simulation messaging, not automatically required by FactoryOps Phase 1 |
| MLflow | BLOCKED | 59000 | Same Docker blocker | Legacy metrics dependency; evaluate replacement/retention later |
| Neo4j | BLOCKED | 7474/7687 | Python driver installed; no Neo4j service exists in Compose and no local listener | Add only in graph phase, with configuration externalized |
| Python package | PASS | `.venv\Scripts\python.exe -m pip install -e .` | Installs after minimal Windows fix; CLI reports 1.3.3 | Useful baseline infrastructure |
| Enterprise FastAPI | PARTIAL | port 8000 | Uvicorn starts; `/health` returns 200. Data endpoint returns 500 because DB is unavailable. Windows Proactor loop is incompatible with psycopg async in this launch mode | API surface is reusable only after repository/service boundaries are cleaned up |
| AgentSociety WebUI API | BLOCKED | port 8080 | Requires PostgreSQL at startup; bundled static frontend output is absent until a successful production build | Retain patterns, not the entire implementation |
| Agent main program | FAIL | `SupplyChainAgent\enterprise\main.py` | Ray starts after fixes; runtime stops because only ~3.6 GB was available and code requires 12 GB available. Further blockers are known: missing map `.pb`, no Windows simulator binary, unavailable Redis/PostgreSQL/MLflow, placeholder LLM credentials | Legacy simulation should not gate FactoryOps Phase 1 |
| LLM calls | BLOCKED_BY_API_KEY | external provider | Config contains placeholders/non-usable values; no fake key was created; no mock/no-LLM enterprise workflow exists | Introduce provider abstraction and deterministic test doubles before Agent workflow work |
| Vite dev server | PARTIAL | 5173 | Starts; browser verified `/`, `/console`, `/industry`. Console page renders empty data; graph page reports API load failure | React shell/visual ideas are reusable; data layer requires replacement |
| Frontend production build | FAIL | `npm run build` | Existing TypeScript failures: model naming mismatch, missing `map_data.json`, unknown types, missing store members and helpers | Must be stabilized before it becomes a release artifact |
| Frontend lint | FAIL | `npm run lint` | 371 findings: 352 errors, 19 warnings | Add a bounded quality baseline; do not fix wholesale in Phase 0 |
| Original API behavior | PARTIAL | `/health`, `/api/experiments` | Health PASS; experiment list FAIL (500) without DB | Health endpoint is currently shallow and does not prove dependencies |
| Supply-chain simulation | FAIL | Ray dashboard 8265 briefly | Cannot cross memory/map/native simulator/service/key boundary | Preserve only as an archived reference or optional research module |
| Tests | FAIL | test discovery | No test files exist | Phase 1 must start with contract and domain tests |

## Browser verification

The Vite UI was inspected in a real browser:

- Home page rendered navigation, product copy, feature cards and metrics.
- Experiment Console rendered controls and an empty table.
- Industry graph route rendered its toolbar but displayed `API数据加载失败，将使用本地数据`.
- Console errors included failed JSON parsing when proxied API responses were empty/unavailable and React/Ant Design deprecation warnings.

## Minimal baseline modifications

These are the only source changes made to improve baseline executability:

1. `setup.py`: skip the unavailable native simulator extension on unsupported Windows platforms.
2. `pyproject.toml`: declare imports that were missing (`json-repair`, `neo4j`) and bound major versions used by this codebase (`mlflow<3`, `openai<2`, `transformers<5`).
3. `utils/path_utils.py`: resolve paths from the actual repository root rather than its parent.
4. `firmagentsql/config.py`: remove the obsolete hard-coded checkout folder name.
5. `agentsociety/cityagent/memory_config.py`: resolve the checked-in industry JSON from the repository and remove unreachable duplicate lines.
6. `agentsociety/cityagent/firmblocks/firm_cognition_block.py`: remove an unused `curses` import unavailable in standard Windows Python.

No business schema, simulation behavior, prompt, frontend feature, or domain behavior was changed.

## Classified failures

| Classification | Findings |
|---|---|
| ENVIRONMENT | Docker Linux engine unavailable; low available RAM during simulation run; Windows lacks upstream native simulator binary |
| DEPENDENCY | Missing `json-repair` and `neo4j` declarations; unconstrained major upgrades; npm security findings |
| CONFIGURATION | Placeholder credentials; missing map path/asset; hard-coded checkout name; Neo4j credentials in source; `CHANGE_ME` service passwords |
| CODE | Frontend TypeScript/lint failures; Windows psycopg event-loop incompatibility; shallow health check; duplicate backend APIs |
| EXTERNAL_SERVICE | PostgreSQL, Redis, MLflow, and Neo4j unavailable |
| MODEL_API | BLOCKED_BY_API_KEY; no supported mock/no-LLM enterprise simulation path |

## Baseline conclusion

The repository is auditable and its Python package plus basic UI can run partially on Windows, but the original end-to-end simulation is not a reliable executable baseline on this host. This is acceptable for Phase 0 only if Phase 1 explicitly decouples the new domain from the legacy simulator and first establishes tests, configuration hygiene, and a deterministic local data path.
