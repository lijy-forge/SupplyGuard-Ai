from datetime import datetime, timezone
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from factoryops_agent import supplier_risk as risk

def candidate(code="SUP-001", **kw):
    return dict(supplierCode=code,name="Fictional supplier",leadTimeDays=14,onTimeRate=98,defectPpm=120,capacityUnits=8000,qualified=True,observedAt=datetime.now(timezone.utc).isoformat(),**kw)

def run(rows, **kw):
    req=risk.AssessmentRequest(part_number="PART-001",current_supplier="SUP-001",**kw)
    return risk.build_risk_graph(lambda _:rows, evidence_provider=lambda _ :[]).invoke({"request":req.model_dump()})

def test_ranking_and_current_supplier_excluded():
    rows=[candidate(),candidate("SUP-003"),candidate("SUP-002")]
    result=run(rows)
    assert [c["supplierCode"] for c in result["recommendations"]]==["SUP-002","SUP-003"]
    assert result["assessments"][0]["risk_score"]==14.69

@pytest.mark.parametrize("field,value,reason",[("qualified",False,"qualification"),("capacityUnits",1,"capacity"),("leadTimeDays",30,"lead time")])
def test_hard_constraints(field,value,reason):
    alt=candidate("SUP-002");alt[field]=value
    result=run([candidate(),alt])
    assert not result["recommendations"]
    assert reason in result["assessments"][1]["exclusions"][0]
    assert result["warnings"]

def test_missing_metrics_are_not_invented():
    alt=candidate("SUP-002");alt["onTimeRate"]=None
    result=run([candidate(),alt])
    assert len(result["assessments"])==1 and result["warnings"]

def test_unknown_current_supplier():
    with pytest.raises(HTTPException) as exc: run([])
    assert exc.value.status_code==422

@pytest.mark.parametrize("body",[{}, {"part_number":"PART-001","current_supplier":"SUP-001","required_units":0}, {"part_number":"../bad","current_supplier":"SUP-001"}])
def test_invalid_api_input(body):
    assert TestClient(risk.app).post("/api/v1/supplier-risk/assess",json=body).status_code==422

def test_api_success(monkeypatch):
    monkeypatch.setattr(risk,"fetch_candidates",lambda _: [candidate(),candidate("SUP-002")])
    monkeypatch.setattr(risk,"collect_evidence",lambda _:[])
    response=TestClient(risk.app).post("/api/v1/supplier-risk/assess",json={"part_number":"PART-001","current_supplier":"SUP-001"})
    assert response.status_code==200
    assert response.json()["requires_human_approval"] is True
    assert len(response.json()["recommendations"])==1

@pytest.mark.parametrize("status,expected",[(404,404),(500,503)])
def test_business_error_mapping(monkeypatch,status,expected):
    monkeypatch.setattr(risk.httpx,"get",lambda *a,**k:httpx.Response(status,request=httpx.Request("GET","http://business")))
    with pytest.raises(HTTPException) as exc:risk.fetch_candidates("PART-001")
    assert exc.value.status_code==expected

def test_business_timeout(monkeypatch):
    def timeout(*a,**k):raise httpx.ReadTimeout("timeout")
    monkeypatch.setattr(risk.httpx,"get",timeout)
    with pytest.raises(HTTPException) as exc:risk.fetch_candidates("PART-001")
    assert exc.value.status_code==503
