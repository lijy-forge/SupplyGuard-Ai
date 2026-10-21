# Data, graph, vector and events

MySQL is authoritative for suppliers, parts, BOMs, batches, inspections, issues, cases, actions, documents, audit events and outbox events. Flyway owns schema and deterministic seed data.

Neo4j is a read model for Supplier–Part–Batch–VehicleModel–Issue relationships. Qdrant stores document chunks embedded locally with `BAAI/bge-small-en-v1.5` through FastEmbed. RabbitMQ queue `factoryops.agent.events` receives topic events from the Spring transactional outbox. Consumers are idempotent by event/aggregate identity.
