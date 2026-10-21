# Agent workflow and safety

The graph nodes are `plan → structured → graph → vector → answer → approval → execute|reject`. Approval uses LangGraph's native `interrupt()` and resumes with `Command(resume=...)`; a stable `thread_id` selects the persisted checkpoint. Production requires `RedisSaver` on Redis Stack (RedisJSON/RediSearch), with AOF and a Compose data volume; isolated tests use `InMemorySaver`.

All factual claims use an evidence contract: `STRUCTURED`, `GRAPH`, or `DOCUMENT`. Neo4j and Qdrant failures degrade to empty evidence payloads rather than fabricated results. The only write tool calls the Spring API after approval. A rejection performs no side effect.
