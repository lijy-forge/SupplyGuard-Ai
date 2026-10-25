# Agent workflow and safety

## Quality containment flow (`factoryops_agent/graph.py`)

The graph nodes are `plan → structured → graph → vector → answer → approval → execute|reject`. Approval uses LangGraph's native `interrupt()` and resumes with `Command(resume=...)`; a stable `thread_id` selects the persisted checkpoint. Production requires `RedisSaver` on Redis Stack (RedisJSON/RediSearch), with AOF and a Compose data volume; isolated tests use `InMemorySaver`.

All factual claims use an evidence contract: each item has an `id` (`<source_type>:<source_id>`), a `source_type` of `STRUCTURED`, `GRAPH`, or `DOCUMENT`, and a `status` of `AVAILABLE`, `EMPTY`, or `UNAVAILABLE`. Claims are derived from the returned data. The batch supplier comes from the request (`supplier_code`) or, if absent, from the quality-case linkage; each retrieved document becomes its own evidence item identified by the document id. Neo4j and Qdrant failures are marked `UNAVAILABLE` rather than fabricated.

The `answer` node calls the configured OpenAI-compatible model (`llm.py`) with the evidence list and validates the reply against `ContainmentRecommendation` (conclusion, evidence ids, actions, confidence 0–1). Any call failure, non-JSON reply, schema violation, or citation of an evidence id that was not retrieved falls back to the deterministic template; `answer_source` and `llm_fallback_reason` record which path was taken. The action type is fixed to `SUPPLIER_CONTAINMENT`; the model only words the plan that a human then approves. The only write tool calls the Spring API after approval. A rejection performs no side effect.

## Supplier risk flow (`factoryops_agent/supplier_risk.py`)

`collect → assess → enrich → recommend → ready|needs_evidence → explain`. Scores, exclusions, ranking and the review gate are rule-based. The final `explain` node runs after that outcome is fixed and may only add a `narrative` (validated against `RiskNarrative`); on any LLM problem it falls back to the rule explanation.

## Tracing (`factoryops_agent/observability.py`)

Every node of both graphs is wrapped by `traced()`, which logs one JSON line to `supplyguard.trace` with the span name, `thread_id`, status (`ok`, `interrupted`, `error`), duration and truncated input/output, and mirrors it to Langfuse when `LANGFUSE_PUBLIC_KEY` is set. Exporter failures never affect the workflow.
