from datetime import datetime, timezone

from fastapi.testclient import TestClient

from factoryops.bootstrap.app import create_app


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["data"]["database"] == "reachable"


def test_supplier_and_part_reads(client):
    assert len(client.get("/api/v1/suppliers").json()["data"]) == 10
    supplier = client.get("/api/v1/suppliers/SUP-001")
    assert supplier.status_code == 200
    assert supplier.json()["data"]["parts"]
    part = client.get("/api/v1/parts/PART-001")
    assert part.status_code == 200
    assert len(part.json()["data"]["suppliers"]) == 2


def test_batch_context(client):
    response = client.get("/api/v1/batches/BATCH-001/context")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["inspection_summary"]["failed"] >= 1
    assert data["related_quality_issues"]


def test_part_vehicle_impact(client):
    response = client.get("/api/v1/parts/PART-001/vehicle-impact")
    codes = {
        item["vehicle_model"]["model_code"]
        for item in response.json()["data"]["vehicle_models"]
    }
    assert {"VM-A", "VM-B"}.issubset(codes)


def test_create_case_and_action(client):
    case_payload = {
        "case_number": "CASE-API",
        "title": "Synthetic API case",
        "description": "No real manufacturer data",
        "priority": "HIGH",
        "status": "OPEN",
        "owner": "quality.engineer1",
        "opened_at": datetime(2026, 7, 1, tzinfo=timezone.utc).isoformat(),
    }
    created = client.post("/api/v1/quality-cases", json=case_payload)
    assert created.status_code == 201
    action = client.post(
        "/api/v1/quality-cases/CASE-API/actions",
        json={
            "action_number": "ACTION-API",
            "title": "Contain synthetic lot",
            "description": "Test action",
            "action_type": "CONTAINMENT",
            "status": "OPEN",
            "assignee": "quality.engineer1",
            "due_date": "2026-07-15",
        },
    )
    assert action.status_code == 201
    assert action.json()["data"]["action_number"] == "ACTION-API"


def test_create_inspection_derives_fail(client):
    response = client.post(
        "/api/v1/batches/BATCH-004/inspections",
        json={
            "inspection_number": "INSP-API",
            "inspection_type": "DIMENSIONAL",
            "metric_name": "Width",
            "measured_value": "12.0",
            "lower_limit": "9.5",
            "upper_limit": "10.5",
            "inspected_at": "2026-08-01T08:00:00Z",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["result"] == "FAIL"


def test_not_found_error_contract(client):
    response = client.get("/api/v1/batches/DOES-NOT-EXIST")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_contract(client):
    response = client.post(
        "/api/v1/quality-cases",
        json={"case_number": "", "priority": "INVALID"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_openapi_contains_versioned_routes(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/batches/{batch_number}/context" in schema["paths"]
    assert schema["info"]["title"] == "SupplyGuard AI Business API"


def test_internal_error_contract(tmp_path):
    app = create_app(f"sqlite:///{(tmp_path / 'error.db').as_posix()}", initialize_schema=True)

    @app.get("/test-only/boom")
    def boom():
        raise RuntimeError("must not leak")

    with TestClient(app, raise_server_exceptions=False) as local_client:
        response = local_client.get("/test-only/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected internal error occurred",
            "details": {},
        }
    }
