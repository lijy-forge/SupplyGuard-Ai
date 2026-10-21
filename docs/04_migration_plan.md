# SupplyGuard AI Migration Plan

The plan is evolutionary. Each phase must leave a deployable, tested increment. Phase 0 does not implement any of these items.

## Phase 1 — Domain Model + Simulation Isolation

- **Goal:** create a reliable FactoryOps domain core without deleting upstream history.
- **Scope:** module boundaries, core entities, migrations, seed fixtures, legacy isolation, test harness.
- **Files:** new `factoryops/domain`, `factoryops/application`, `factoryops/infrastructure`, `tests`; existing entrypoints/config; archival boundary around simulation modules.
- **New modules:** supplier, part, BOM, vehicle, batch, plant, process, inspection, issue, case, corrective action, document, user/audit primitives.
- **Removed modules:** none physically; remove legacy simulation from the default startup path.
- **API changes:** versioned `/api/v1/health`, suppliers, parts, batches and quality cases; consistent error envelope.
- **Data changes:** Alembic baseline and normalized PostgreSQL schema with IDs, revisions, timestamps and tenant/site scope.
- **Tests:** domain invariants, migration up/down in disposable DB, repository contract, API smoke and authorization placeholders.
- **Acceptance criteria:** clean install; one command starts API + PostgreSQL; migrations succeed; CRUD/query slices pass; no LLM/Docker-native simulator required.
- **Risks:** accidental coupling to old models; premature schema breadth; unclear tenant/site rules.

## Phase 2 — Business Data Service

- **Goal:** support reliable structured queries and controlled writes.
- **Scope:** repositories, use cases, validation, pagination, import/export and audit events.
- **Files:** `factoryops/application/*`, `factoryops/api/v1/*`, `factoryops/infrastructure/db/*`.
- **New modules:** query services, command handlers, transactional outbox, idempotency.
- **Removed modules:** retire `firmagentsql` from the active path after parity is tested.
- **API changes:** supplier/part/BOM/batch/inspection/issue/case/action endpoints.
- **Data changes:** constraints, indexes, audit/outbox tables and reference-data loaders.
- **Tests:** API contracts, repository integration, concurrency/idempotency and CSV/fixture ingestion.
- **Acceptance criteria:** trace a batch to supplier/part/process using SQL; all writes emit audit events; OpenAPI client generation succeeds.
- **Risks:** data quality and identity matching; importing inconsistent legacy examples.

## Phase 3 — Knowledge Graph

- **Goal:** deliver BOM, lineage and impact traversal with explainable paths.
- **Scope:** Neo4j Compose profile, graph projection, sync, Cypher repository and read APIs.
- **Files:** `factoryops/graph`, migration/config, Compose Neo4j profile.
- **New modules:** projection mapper, outbox consumer, graph query service.
- **Removed modules:** replace hard-coded `neo4j/*.py` active usage; retain samples as fixtures.
- **API changes:** impact analysis, upstream/downstream lineage and related-entity endpoints.
- **Data changes:** stable graph IDs, constraints and projection version metadata.
- **Tests:** idempotent projection, known path fixtures, SQL/graph consistency and authorization filters.
- **Acceptance criteria:** deterministic affected-batch/model results with returned graph paths and source IDs.
- **Risks:** graph drift, duplicate identities, unbounded traversals.

## Phase 4 — Vector Knowledge Base

- **Goal:** retrieve governed SOP/FMEA/8D/specification evidence.
- **Scope:** document metadata, ingestion, parsing/chunking, embeddings, access filtering and retrieval benchmark.
- **Files:** `factoryops/documents`, `factoryops/retrieval`, worker jobs and storage config.
- **New modules:** parser adapters, chunk/version model, embedding gateway and vector repository interface.
- **Removed modules:** replace FAISS/simple memory in production path; retain simple embedding for unit tests.
- **API changes:** document upload/registration, ingestion status and search endpoints.
- **Data changes:** document/chunk metadata, checksum, source version and ACL scope; optional Qdrant collection only after benchmark.
- **Tests:** parser fixtures, permission leakage, retrieval relevance and re-ingestion idempotency.
- **Acceptance criteria:** cited passages are reproducible by document/version/page or section; baseline Recall@K recorded.
- **Risks:** copyrighted/confidential data, OCR quality, stale embeddings and access leakage.

## Phase 5 — Agent Workflow + Tools

- **Goal:** answer quality/supply questions using typed multi-source evidence.
- **Scope:** intent routing, planning, read-only tools, evidence aggregation, cited answer and provider gateway.
- **Files:** `factoryops/agent`, `factoryops/tools`, `factoryops/evidence`, prompt registry.
- **New modules:** workflow state, tool schemas, evidence envelope and model test double; optionally LangGraph after explicit-state prototype.
- **Removed modules:** old `NewFirmAgent` and simulation prompts from active runtime.
- **API changes:** agent session/query/stream endpoints and trace retrieval.
- **Data changes:** session, run, step, tool call, evidence and answer records.
- **Tests:** deterministic tool routing, invalid arguments, citation correctness, model timeout and no-evidence behavior.
- **Acceptance criteria:** benchmark questions combine SQL/vector/graph evidence without hallucinated entities and always return evidence IDs.
- **Risks:** tool overreach, prompt injection, non-determinism and excessive latency.

## Phase 6 — HITL + RBAC + Audit

- **Goal:** safely execute business actions with explicit human control.
- **Scope:** role/site permissions, risk classes, proposal/approval workflow, idempotent executor and immutable audit.
- **Files:** `factoryops/auth`, `factoryops/approval`, `factoryops/audit`, UI approval queue.
- **New modules:** policy engine, proposal signer/hash, approval service and action executor.
- **Removed modules:** any direct side-effect tool invocation from answer generation.
- **API changes:** proposals, approve/reject/expire and action-result endpoints.
- **Data changes:** roles, scopes, proposals, decisions, execution attempts and immutable audit events.
- **Tests:** privilege boundaries, tampered/expired proposals, double-submit, denial and replay.
- **Acceptance criteria:** every side effect has an authorized human decision and exactly-once result record.
- **Risks:** privilege escalation, TOCTOU changes and unclear operational ownership.

## Phase 7 — Trace + Observability

- **Goal:** make every answer/action diagnosable without leaking secrets.
- **Scope:** structured logging, traces, metrics, dashboards, redaction and retention.
- **Files:** observability package, deployment config and operational runbooks.
- **New modules:** telemetry adapters and trace export; optional Langfuse/OpenTelemetry integration.
- **Removed modules:** direct `print` diagnostics and raw sensitive payload logging.
- **API changes:** authorized trace/audit inspection endpoints.
- **Data changes:** retention indexes and optional external trace IDs.
- **Tests:** correlation propagation, redaction, exporter failure and retention jobs.
- **Acceptance criteria:** one correlation ID reconstructs retrieval, model, tools, approval and result.
- **Risks:** sensitive-data leakage, observability cost and audit/trace confusion.

## Phase 8 — Agent Eval Benchmark

- **Goal:** measure quality and safety across architecture variants.
- **Scope:** versioned dataset, runners, graders, regression gates and reports.
- **Files:** `evals/datasets`, `evals/runners`, `evals/graders`, CI jobs.
- **New modules:** configuration matrix runner and evidence/entity graders.
- **Removed modules:** anecdotal demo-only claims as acceptance evidence.
- **API changes:** optional internal eval-run/report endpoints; no production action execution.
- **Data changes:** benchmark cases, expected evidence/entities, scores and run metadata.
- **Tests:** grader calibration, reproducibility and leakage controls.
- **Acceptance criteria:** LLM-only, Vector, SQL+Vector and SQL+Vector+Graph results are comparable with confidence intervals and cost/latency.
- **Risks:** biased/easy datasets, judge-model instability and contamination.

## Phase 9 — Frontend + Demo + Career Packaging

- **Goal:** deliver a coherent enterprise demo backed by verified behavior.
- **Scope:** search/investigation workspace, evidence panel, graph impact view, approval queue, trace/eval pages and deployment docs.
- **Files:** feature-oriented frontend, demo fixtures, screenshots, architecture decision records and runbooks.
- **New modules:** typed API client, query cache, evidence viewer and approval UX.
- **Removed modules:** city map, replay-only screens and duplicated graph implementations unless a validated use remains.
- **API changes:** finalize UI-oriented pagination/filter/stream contracts.
- **Data changes:** curated synthetic automotive quality dataset with provenance.
- **Tests:** frontend unit/component, Playwright E2E, accessibility and demo smoke.
- **Acceptance criteria:** clean deployment reproduces a batch-quality investigation, evidence-backed impact analysis and approved corrective action end-to-end.
- **Risks:** demo polish outrunning correctness, confidential data and unstable deployment.
