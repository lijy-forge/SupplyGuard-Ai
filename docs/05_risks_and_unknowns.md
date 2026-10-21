# Risks and Unknowns

## Top risks

1. **A valid upstream Mapbox public token remains in history.** Mapbox confirmed that the `pk` token is currently valid. GitHub Push Protection was explicitly bypassed as a false positive so the exact upstream baseline could be published. Even though this is a client-side public token, its ownership, URL restrictions and quota exposure should be reviewed before a public release.
2. **There is no reliable executable or tested baseline.** Windows lacks the native simulator binary; Docker services did not start; map/key/service dependencies are missing; frontend production build fails; no automated tests exist.
3. **Domain and evidence correctness are undefined.** Real schemas, sample enterprise documents, identity/effectivity rules, permissions and benchmark truth sets have not been supplied.

## Technical risks

- Duplicate FastAPI applications expose inconsistent contracts and ports.
- Agent, storage, metrics and business logic are tightly coupled.
- SQL field naming and frontend types diverge.
- Large duplicated frontend components are difficult to test or safely change.
- The legacy runtime assumes high memory, Ray, Redis and a native simulator.
- Health checks do not reflect dependency health.

Mitigation: Phase 1 modular boundaries, typed contracts, migrations and tests before feature growth.

## Migration risks

- Removing simulation too early could discard useful fixtures or visualization concepts.
- Keeping it in the active path would keep FactoryOps hostage to unrelated runtime requirements.
- Dual writes between PostgreSQL and Neo4j/vector stores can drift.

Mitigation: isolate rather than immediately delete; document extracted concepts; use PostgreSQL as source of truth and outbox-driven projections.

## Dependency risks

- Broad lower-bound-only dependencies resolve to incompatible future major versions.
- npm reports 40 vulnerabilities, including one critical finding.
- Neo4j and `json-repair` were imported without declaration.
- MLflow internal database tables are queried directly.

Mitigation: lock reproducible versions, update in small tested batches, use supported APIs and generate SBOM/audit reports in CI.

## LLM risks

- Placeholder credentials and provider URLs are checked into config.
- No deterministic mock path exists for the enterprise workflow.
- Retry count and long timeouts can amplify cost/latency.
- Prompts may receive untrusted content and produce ungrounded actions.

Mitigation: provider gateway, environment secrets, test doubles, structured outputs, prompt-injection boundaries, evidence-required answers and HITL for side effects.

## Windows environment risks

- Upstream native simulator is not published for Windows.
- Standard Windows Python lacks `_curses`; an unused import caused startup failure.
- psycopg async rejected the default Proactor event loop in the tested Uvicorn launch.
- Docker Desktop's Linux engine did not become responsive.
- Available RAM fell below the code's 12 GB threshold.

Mitigation: make the new application platform-neutral, validate on Windows and Linux CI, and keep the legacy simulator optional/Linux-only.

## Data risks

- Current data is synthetic simulation data, not automotive quality master data.
- Entity IDs, part revisions, BOM effectivity, batch genealogy and plant scope are unspecified.
- Documents may contain confidential, personal or export-controlled information.
- Graph/vector projections can become stale.

Mitigation: data contracts, version/effectivity model, provenance, ACL filtering, retention policy, synthetic fixtures and projection reconciliation.

## License risks

- Repository license is Apache-2.0 with FIB LAB, Tsinghua University copyright notice.
- The repository also identifies HIT-ICES/SupplyChainAgent as upstream while package metadata points to the original AgentSociety project; provenance should remain explicit.
- No `NOTICE` file was found, but existing copyright/license/attribution notices must be retained.
- Modified distributed files need prominent modification notices under Apache-2.0 section 4.
- Third-party npm/Python/model/document licenses require separate inventory; Apache-2.0 at repository root does not automatically cover them.

Mitigation: retain LICENSE and attribution document, add SPDX/SBOM review, record modified upstream files and review document/model licenses before distribution.

## Over-engineering risk

Introducing Spring Boot, Redis, RabbitMQ, Qdrant, Neo4j and LangGraph simultaneously would multiply operations and transactional boundaries before core domain correctness is known.

Mitigation: modular Python monolith + PostgreSQL first; introduce each store/runtime only against a measured use case and acceptance test.

## Security risks

- A valid historical Mapbox public token remains exposed in Git history; the approved GitHub bypass does not address ownership, URL restrictions or quota exposure.
- Checked-in config includes placeholder or suspicious provider-key-looking strings and default passwords.
- CORS allows all origins while allowing credentials in the enterprise API.
- Neo4j credentials are hard-coded.
- Logs print raw transactions, prompts and agent state.

Mitigation: revoke/verify exposed credentials, remediate history with an explicit strategy, move secrets to environment/secret store, restrict CORS, redact logs and add secret scanning.

## Open questions before or during Phase 1

- What is the authoritative tenant/plant/user authorization model?
- Which real or synthetic automotive dataset defines required fields and relations?
- Is PostgreSQL acceptable instead of candidate MySQL?
- Which document formats/languages and confidentiality classes are required?
- Which actions are allowed in the first demo, and who can approve them?
- What evidence citation granularity is required (row, document page, graph path)?
- What deployment target is authoritative (Windows workstation, Linux server, cloud)?
- Should the inherited Mapbox public token be replaced for the maintained frontend, and which project-owned URL-restricted token should replace it?
