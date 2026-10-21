# FactoryOps API v1 Contract

Base path: `/api/v1`. Successful responses use `{ "data": ... }`; errors use `{ "error": { "code", "message", "details" } }`. API schemas are Pydantic models and never expose ORM objects.

## Endpoints

| Method | Path | Result |
|---|---|---|
| GET | `/health` | service version and real database reachability |
| GET | `/suppliers` | suppliers |
| GET | `/suppliers/{supplier_code}` | supplier and supplied parts |
| GET | `/parts` | parts |
| GET | `/parts/{part_number}` | part, suppliers, and vehicle usage |
| GET | `/parts/{part_number}/vehicle-impact` | SQL impact baseline with models and BOM versions |
| GET | `/batches/{batch_number}` | batch |
| GET | `/batches/{batch_number}/context` | batch, part, supplier, inspection summary, issues |
| GET | `/batches/{batch_number}/inspections` | inspection records |
| POST | `/batches/{batch_number}/inspections` | derived PASS/FAIL inspection; returns 201 |
| GET | `/quality-cases` | quality cases |
| GET | `/quality-cases/{case_number}` | case, issues, actions |
| POST | `/quality-cases` | create a traditional case; returns 201 |
| POST | `/quality-cases/{case_number}/issues/{issue_number}` | associate an existing issue |
| POST | `/quality-cases/{case_number}/actions` | create a traditional corrective action; returns 201 |

The generated OpenAPI document is available at `/openapi.json` and interactive documentation at `/docs`.

## Request examples

Create case:

```json
{
  "case_number": "CASE-011",
  "title": "Synthetic dimensional investigation",
  "description": "Demonstration data only",
  "priority": "HIGH",
  "status": "OPEN",
  "owner": "quality.engineer1",
  "opened_at": "2026-09-19T08:00:00Z"
}
```

Create inspection (the server derives `result`):

```json
{
  "inspection_number": "INSP-NEW-001",
  "process_id": null,
  "inspection_type": "DIMENSIONAL",
  "metric_name": "Width",
  "measured_value": 10.8,
  "lower_limit": 9.5,
  "upper_limit": 10.5,
  "inspected_at": "2026-09-19T08:00:00Z"
}
```

## Error codes

| Code | HTTP | Meaning |
|---|---:|---|
| `NOT_FOUND` | 404 | Requested business entity is absent |
| `VALIDATION_ERROR` | 422 | Request shape or enum is invalid |
| `CONFLICT` | 409 | Unique business key or relationship already exists |
| `DOMAIN_RULE_VIOLATION` | 422 | A business invariant is violated |
| `INTERNAL_ERROR` | 500 | Unexpected server failure; reserved for production middleware |

Errors are designed to be machine-stable for future tool adapters; callers must not branch on human-readable messages.
