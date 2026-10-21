# Golden Path demo

1. Build the business runtime: `cd services/business-service && mvn -DskipTests package`.
2. Start `docker compose -f docker/docker-compose.factoryops.yml up --build` from the repository root.
3. Open http://localhost:3000 and submit the prefilled BATCH-001 investigation.
4. Inspect the three evidence classes and VM-A/VM-B impact.
5. Review the proposed supplier containment action.
6. Approve as `quality.lead`.
7. Verify the corrective action, audit row and outbox event through the Spring endpoints.

Service endpoints: business http://localhost:8081, agent http://localhost:8082, RabbitMQ http://localhost:15672, Neo4j http://localhost:7474, Qdrant http://localhost:6333.
