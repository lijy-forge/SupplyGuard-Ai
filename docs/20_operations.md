# Operations

Required local runtime: Docker Compose. Health endpoints are `/actuator/health` for Spring and `/health` for the Agent service. Persistent volumes exist for MySQL, Neo4j and Qdrant. Secrets must be supplied as environment variables outside source control.

Langfuse is optional: set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL`. Without real credentials no trace claim is made. The deterministic fake provider is the demo default; an OpenAI-compatible provider can be selected through environment configuration.

Recovery: restart stateless services; MySQL outbox retains unpublished events, RabbitMQ uses a durable queue, and Redis checkpoints preserve resumable human approvals.
