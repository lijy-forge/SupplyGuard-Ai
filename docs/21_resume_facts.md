# Final P0 verification facts

## SAFE_TO_CLAIM

- Source-level Java, Agent, and UI tests have passed locally; the GitHub Actions architecture gate is green.
- The live infrastructure integration run passed in the previous development repository (commit `95c4ed7`, history not migrated; re-run the `SupplyGuard Live Infrastructure Integration` workflow on the current repository for a linkable result). It built the full Compose stack and health-checked MySQL, Redis Stack, RabbitMQ, Neo4j, Qdrant, the Spring service, FastAPI agent, and frontend; the worker's real RabbitMQ consumption was then exercised.
- The live run used Flyway-seeded MySQL business endpoints, then created one approved corrective action and verified its audit event and transactional-outbox event.
- A real LangGraph approval checkpoint survived an `agent-service` restart and resumed with the same thread ID. Redis Stack is configured with AOF and a named volume.
- RabbitMQ publication and worker consumption were verified by the Redis idempotency receipt for the created action; a duplicate event left that receipt unchanged.
- Live Neo4j data contained 6 nodes and 5 relationships; part-to-vehicle, batch-to-impact, and supplier-dependency Cypher queries all returned evidence.
- Live Qdrant held 12 FastEmbed vectors of dimension 384, and the Golden Path made a real document retrieval call.
- The SQL + graph + vector Golden Path produced `STRUCTURED`, `GRAPH`, and `DOCUMENT` evidence before HITL. Approval wrote the corrective action; rejection returned `REJECTED` without creating one.
- The original Phase 1 implementation and upstream attribution remain present.

## SAFE_WITH_QUALIFIER

- Langfuse SDK integration is present, but it requires real credentials to emit a trace.
- The local Docker client is installed, but the local Docker Engine is unavailable.

## NOT_SAFE_TO_CLAIM

- A Langfuse trace has not been emitted because no Langfuse credentials were supplied.
- A real-LLM smoke test has not been run because no LLM provider credentials were supplied; the verified Golden Path uses deterministic orchestration plus real SQL, graph, vector, messaging, and HITL infrastructure.
