# Synthetic Demonstration Dataset

The Phase 1 seed is deterministic and wholly fictional. It does not contain or imply data from NIO or any other real manufacturer. Stable UUIDs are derived from fixed names, timestamps start from 2026-01-05 UTC, and repeated execution does not insert duplicates.

## Scale

| Data | Count |
|---|---:|
| Suppliers | 10 |
| Parts | 30 |
| Vehicle models | 4 |
| BOM items | 61 |
| Supplier-part links | 45 |
| Plants / processes | 3 / 9 |
| Batches | 36 |
| Inspection records | 108 |
| Quality issues | 16 |
| Quality cases | 10 |
| Corrective actions | 12 |
| Document metadata | 16 |
| Users | 3 |

The data includes parts with two suppliers, parts used by multiple fictional models, normal and failed inspections, open and historical cases, and many-to-many issue relationships. Documents contain only synthetic metadata and `synthetic://` URIs.

## Canonical cases

### CASE-001 — dimensional exceedance and vehicle impact

`BATCH-001` from `SUP-001` contains `PART-001`. Its Width result exceeds the upper limit. `ISSUE-001` and `CASE-001` record the investigation. `PART-001` is used by at least `VM-A` and `VM-B`, making this the SQL impact-query baseline.

### CASE-002 — repeated supplier history

The first three historical batches belong to `SUP-001` and contain comparable Width failures. `ISSUE-002` links those batches, providing a repeat-failure pattern for later quality analytics and evaluation.

### CASE-003 — one issue across multiple batches

`ISSUE-003` affects both `BATCH-003` and `BATCH-004`. This verifies that issues are not modeled as belonging to one batch and provides a future graph traversal fixture.

## Generation and validation

`factoryops-seed` seeds the database selected by `FACTORYOPS_DATABASE_URL`. It expects an Alembic-migrated schema. The generator returns exact counts and reports `already_seeded` on subsequent runs. Automated tests verify count, idempotency, inspection failures, multi-supplier sourcing, multi-batch issues, and vehicle impact.
