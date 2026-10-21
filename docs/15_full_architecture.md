# SupplyGuard AI full architecture

The accelerated architecture separates the system of record from probabilistic reasoning. React provides the operator workspace. Spring Boot owns MySQL business writes, validation, audit records and the transactional outbox. FastAPI hosts a real LangGraph workflow. Redis persists graph checkpoints, RabbitMQ propagates events, Neo4j answers multi-hop impact questions, Qdrant retrieves local FastEmbed-indexed documents, and Langfuse provides optional tracing when credentials are configured.

The Golden Path is: question → structured batch/case evidence → graph impact → document evidence → synthesized recommendation → mandatory human interrupt → approved Spring business command → audit + outbox.

Phase 1 remains available through `docker-compose.factoryops-phase1.yml`; the new stack does not erase its code or history.
