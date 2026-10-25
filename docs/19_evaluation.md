# Evaluation and quality gates

`evals/scenarios.json` holds 18 distinct offline scenarios that run against the real LangGraph workflows with deterministic fake data sources:

- **Quality flow (Q-01…Q-08):** all sources available; valid LLM recommendation; LLM citing evidence it was never given; non-JSON LLM output; document store down; graph down; no document match; explicit supplier code. Every scenario also asserts the invariants *workflow stops for approval* and *no write before approval*.
- **Risk flow (R-01…R-10):** several candidates with exclusions; missing document evidence; graph/BOM vehicle conflict; case not implicating the current supplier; no eligible alternate; shared upstream reordering the ranking; relaxed-deadline scenario not applied; stale metrics; an LLM narrative arguing for an excluded supplier; demo evidence. Every scenario also asserts that the LLM narrative leaves the rule-based outcome unchanged.

`python evals/run_eval.py` runs them offline with a scripted LLM; `tests/test_evals.py` runs the same harness in CI and checks that wrong expectations are detected.

`python evals/run_eval.py --live-llm` swaps in the configured OpenAI-compatible model. It still enforces the invariants above but, instead of asserting on model wording, reports how many outputs passed schema and evidence-ID validation and why the rest fell back to templates. 
## Recorded live-LLM run

| Date | Model | JSON mode | Scenarios passed | LLM outputs accepted | Fallbacks | Wall time |
|---|---|---|---|---|---|---|
| 2026-10-25 | DeepSeek `deepseek-chat` | on | 18 / 18 | 18 / 18 | 0 | ~50 s |

Full report: [`evals/results/live-deepseek-chat-2026-10-25.json`](../evals/results/live-deepseek-chat-2026-10-25.json).

Manual review of that run's outputs: when document evidence was unavailable or empty (Q-05, Q-07) the model cited only available evidence and stated that documentation was incomplete; in R-09 the narrative reported the excluded supplier as excluded rather than recommending it.

A first live run showed the quality prompt did not tell the model each evidence item's status, and that citations of unavailable evidence were still accepted. Both were fixed (status is now in the prompt; containment recommendations may cite only `AVAILABLE` evidence) before the recorded run.

Limits: this is a single run of 18 calls on fictional data, so it shows the guardrails hold with a real model, not statistical answer quality.

## Full-stack verification (2026-10-26)

`tests/live_infra.py` was run locally against the complete Compose stack with DeepSeek enabled and passed: SQL + Neo4j + Qdrant evidence, approval interrupt surviving an `agent-service` restart, corrective action + audit + outbox, RabbitMQ delivery with idempotent consumption, the rejection branch, and (newly added) the supplier-risk flow on live data (READY_FOR_REVIEW, SUP-002 recommended, one review task and one event despite repeated create/approve calls). Both LLM steps produced accepted output with zero fallbacks.

Defects this run found and fixed:

| Symptom | Cause | Fix |
|---|---|---|
| Business service failed to start on MySQL | `V4` used `TIMESTAMP(6) ... DEFAULT CURRENT_TIMESTAMP`; MySQL requires matching precision, H2 (used by tests) does not | `DEFAULT CURRENT_TIMESTAMP(6)` |
| Agent service started against a crashed business service | business healthcheck was `java -version` | healthcheck now probes port 8081 |
| Worker exited on first boot | RabbitMQ not yet accepting connections, no restart policy | `restart: on-failure` |
| No node traces in container logs | uvicorn does not configure application loggers, so INFO traces were dropped | `configure_logging()` at app start-up |
| Risk narrative fell back to template on real data | summary exceeded the 1500-char schema limit | length limits stated in both prompts |
| Graph evidence occasionally UNAVAILABLE, cause invisible | 5 s Neo4j query timeout under CPU contention; exception not logged | evidence failures logged; timeouts 5 s connect / 10 s query |
| First LLM call took ~60 s from Docker | one of DeepSeek's addresses unreachable from the Docker VM; connect timeout equalled the 60 s read timeout | separate 5 s connect timeout (next address is tried) and a shared client with keep-alive |
