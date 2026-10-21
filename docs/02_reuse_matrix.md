# Baseline Reuse Matrix

The ratings apply to building SupplyGuard AI, not to preserving the research demo unchanged.

| Module / capability | Decision | Why and intended treatment |
|---|---|---|
| FastAPI foundation (`agentsociety/webapi`, enterprise API concept) | REFACTOR | Async endpoints, lifespan and Pydantic are valuable. Consolidate the two APIs, introduce services/repositories, dependency-aware health, consistent response contracts and generated OpenAPI clients. |
| SQLAlchemy models/session pattern | REFACTOR | Useful foundation, but current enterprise tables bypass it and domain entities do not exist. Add migrations and a FactoryOps domain model; avoid direct SQL spread across endpoints. |
| PostgreSQL infrastructure | KEEP | Already central and sufficient for Phase 1 structured data. Prefer it over immediately introducing MySQL; JSONB and mature tooling reduce migration cost. |
| Neo4j integration | REFACTOR | Graph traversal matches BOM/impact analysis, but current scripts use hard-coded credentials, destructive clear-all import and are disconnected from APIs. Introduce it in Phase 3 behind a graph repository. |
| React/Vite application shell | REFACTOR | Routing, Ant Design and visualization experience are useful. Current model/API inconsistency, huge components, hard-coded endpoints and build failures require a new feature structure and typed client. |
| Supply-chain visualization | REFACTOR | Graph/replay interaction patterns can support BOM, lineage and impact views. Remove map/city assumptions and duplicated 2,000-line graph components. |
| Docker/Compose | REFACTOR | Keep local composition as the developer entry point. Add health checks, env files, secrets handling, profiles and later Neo4j; do not preserve `CHANGE_ME` defaults as production config. |
| Agent base/block abstractions | REFACTOR | The separation into blocks and provider wrapper contains ideas worth reusing. Replace tick-driven actor assumptions with explicit workflow state, typed tools and auditable transitions. |
| LLM provider wrapper | REFACTOR | Retry, concurrency and token accounting are useful. Add provider-neutral structured output, timeouts, redaction, test doubles and trace metadata; remove intelligence-level indexing as routing logic. |
| Prompt utilities/prompts | REFACTOR | Template mechanics are reusable, but supply simulation prompts are bound to pricing and negotiation. Version prompts by task and test them against evidence requirements. |
| Simple embedding / FAISS memory | REPLACE | Useful as a test-only fallback, not a durable enterprise knowledge store. Adopt a document retrieval interface; choose Qdrant only after corpus/scale evidence. |
| `NewFirmAgent` / Enterprise Agent | REPLACE | It mixes DB connections, MLflow, pricing, production, negotiation, persistence and debugging in one actor. Extract only domain terminology and sample scenarios. |
| Production / stock blocks | REMOVE | They simulate inventory creation in a research economy and do not model factory inspections, batches, work orders or traceability with enterprise correctness. |
| Sales / price decision | REMOVE | Dynamic price simulation is outside the quality and traceability core. It adds LLM side effects unrelated to Phase 1 goals. |
| Negotiation / collaboration | REMOVE | Autonomous inter-firm bargaining is not part of the target quality workflow. Do not map it to human approval; build explicit action proposals instead. |
| Order / transaction simulation | REPLACE | Transaction events may inspire audit records, but simulated deals/payment installments are the wrong domain. Replace with corrective-action/task and immutable audit entities. |
| Ray-based simulation orchestration | REMOVE | High operational cost and no value for request-driven enterprise workflows. Keep only in an archived optional legacy area until deletion is approved in Phase 1. |
| Native city/economy simulator and map | REMOVE | Unsupported on Windows and unrelated to FactoryOps quality workflows. It must not remain a runtime dependency. |
| Redis messaging | REPLACE | Required by legacy actors, but not justified for Phase 1. Reintroduce only for demonstrated caching, distributed locks or short-lived workflow state. |
| MLflow experiment tracking | REFACTOR | Metric/run ideas are useful for evals, but application code queries MLflow internal tables. Later choose a supported API or purpose-built trace/eval store. |
| `firmagentsql` query/insert layer | REPLACE | It contains useful query examples but mixes schema creation, persistence, reporting and MLflow internals. Replace with migrations, repositories and typed DTOs. |
| Enterprise FastAPI endpoints | REFACTOR | Endpoint coverage shows UI needs, but naming bugs, duplicated code and inconsistent error handling are extensive. Define FactoryOps use-case APIs rather than porting endpoints one-for-one. |
| AgentSociety WebUI endpoints | REFACTOR | Experiment/survey patterns may support eval runs, but simulation-centric resources should not lead the product model. |
| Frontend local replay/store | REPLACE | The giant MobX store blends remote and synthetic local data and causes type errors. Use feature-scoped query/cache state and typed domain models. |
| Neo4j/industry JSON generator | REFACTOR | Valuable as demo-data inspiration. Make generation deterministic, schema-validated and separate from production ingestion. |
| Analytics/clustering scripts | REMOVE | Large ad hoc scripts are coupled to legacy MLflow/SQL schemas and are not service-quality modules. Preserve externally useful findings before removal. |
| Configuration system | REFACTOR | Pydantic config is a strong base. Split profiles, use environment-backed secrets, validate required services and remove absolute/hard-coded paths. |
| Logging | REPLACE | Scattered `print` statements and sensitive/debug payloads are unsuitable. Add structured correlation IDs, tool/audit events and redaction. |
| Tests | REPLACE | No test suite exists. Establish a new test pyramid starting with domain and API contracts. |

## Five highest-value assets

1. FastAPI/Pydantic patterns and existing endpoint discovery.
2. PostgreSQL/async persistence experience and experiment schemas.
3. React/Ant Design shell plus graph visualization concepts.
4. Neo4j supply-topology modeling concepts and sample graph data.
5. LLM provider/retry/token accounting concepts.

## Five highest-priority removals or replacements

1. Ray/native city simulation runtime.
2. `NewFirmAgent` god object and direct database writes.
3. Production/sales/negotiation/order simulation blocks.
4. Duplicate, inconsistent backend APIs and `firmagentsql` direct-query layer.
5. Giant duplicated frontend graph/replay components and mixed local/API state store.
