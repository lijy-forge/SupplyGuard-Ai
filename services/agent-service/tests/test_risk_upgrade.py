from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from factoryops_agent import supplier_risk as risk
from factoryops_agent.risk_evidence import collect_evidence
from test_supplier_risk import candidate

def request():
    return risk.AssessmentRequest(part_number="PART-001",current_supplier="SUP-001").model_dump()

def evidence(shared=True):
    return [
      {"id":"case-1","source_type":"STRUCTURED","status":"AVAILABLE","payload":{"cases":[{"supplierCode":"SUP-001"}],"vehicles":[{"model":"VM-A"}]}},
      {"id":"graph-1","source_type":"GRAPH","status":"AVAILABLE","payload":{"vehicles":[{"model":"VM-A"}],"shared_dependencies":[{"supplier":"SUP-002","upstream":"UP-1"}] if shared else []}},
      {"id":"doc-1","source_type":"DOCUMENT","status":"AVAILABLE","payload":{"matches":[{"id":"SOP-1","text":"Review qualification"}]}}
    ]

def assess(rows=None,ev=None):
    return risk.build_risk_graph(lambda _ :rows or [candidate(),candidate("SUP-002")],lambda _:evidence() if ev is None else ev).invoke({"request":request()})

def test_shared_upstream_penalty_changes_ranking_and_cites_evidence():
    result=assess([candidate(),candidate("SUP-002"),candidate("SUP-003")])
    assert result["analysis_status"]=="READY_FOR_REVIEW"
    assert result["assessments"][1]["graph_penalty"]==15
    assert result["assessments"][1]["risk_score"]==29.69
    assert [r["supplierCode"] for r in result["recommendations"]]==["SUP-003","SUP-002"]
    assert "graph-1" in result["explanation"]

@pytest.mark.parametrize("status",["UNAVAILABLE","EMPTY","DEMO","NOT_CONFIGURED"])
def test_incomplete_evidence_blocks_review(status):
    ev=evidence();ev[2]["status"]=status
    result=assess(ev=ev)
    assert result["analysis_status"]=="NEEDS_EVIDENCE"
    assert result["recommendations"] # advisory still available

def test_bom_graph_disagreement_and_case_mismatch_block_review():
    ev=evidence();ev[1]["payload"]["vehicles"]=[{"model":"VM-B"}]
    result=assess(ev=ev)
    assert result["analysis_status"]=="NEEDS_EVIDENCE"
    assert result["evidence"][1]["status"]=="CONFLICT"
    ev=evidence();ev[0]["payload"]["cases"][0]["supplierCode"]="SUP-999"
    assert assess(ev=ev)["analysis_status"]=="NEEDS_EVIDENCE"

def test_scenario_does_not_relax_actual_recommendations():
    alt=candidate("SUP-002");alt["leadTimeDays"]=28
    result=assess([candidate(),alt])
    assert result["recommendations"]==[]
    assert result["scenario"]["eligible_if_deadline_relaxed"]==["SUP-002"]
    assert result["scenario"]["applied_to_recommendation"] is False

@pytest.mark.parametrize("offset",[-31,1])
def test_stale_or_future_metrics_not_recommended(offset):
    alt=candidate("SUP-002");alt["observedAt"]=(datetime.now(timezone.utc)+timedelta(days=offset)).isoformat()
    result=assess([candidate(),alt])
    assert not result["recommendations"]
    assert "timestamp" in result["assessments"][1]["exclusions"][0]

def test_adapter_failures_are_explicit_not_fake_success():
    def fail(_):raise RuntimeError("offline")
    ev=collect_evidence(request(),structured=fail,graph=fail,documents=fail,mode="live")
    assert {e["status"] for e in ev}=={"UNAVAILABLE"}
    assert all(e["payload"]=={} for e in ev)

def test_demo_mode_is_labeled_and_cannot_enable_review():
    ev=collect_evidence(request(),structured=lambda _ :{"cases":[{"supplierCode":"SUP-001"}],"vehicles":[{"model":"VM-A"}]},mode="demo")
    assert [e["status"] for e in ev]==["AVAILABLE","DEMO","DEMO"]
    assert assess(ev=ev)["analysis_status"]=="NEEDS_EVIDENCE"

def test_idempotent_review_retry_uses_stored_snapshot(monkeypatch):
    calls=[]
    def business(method,path,payload=None):
        calls.append(path)
        if "review-keys" in path:return {"id":"stored-id","snapshot":{"request":request()}}
        return {"id":"stored-id","status":"PENDING_REVIEW"}
    monkeypatch.setattr(risk,"business_request",business)
    monkeypatch.setattr(risk,"assess",lambda _:pytest.fail("retry must not regenerate evidence"))
    result=risk.create_review(risk.ReviewRequest(request_key="key-1",request=risk.AssessmentRequest(**request())))
    assert result["status"]=="PENDING_REVIEW" and len(calls)==2

def test_idempotency_key_conflict(monkeypatch):
    monkeypatch.setattr(risk,"business_request",lambda *a,**k:{"id":"stored","snapshot":{"request":{}}})
    with pytest.raises(HTTPException) as exc:risk.create_review(risk.ReviewRequest(request_key="key-1",request=risk.AssessmentRequest(**request())))
    assert exc.value.status_code==409


def test_native_document_worker_failure_does_not_crash_api(monkeypatch):
    import subprocess
    from factoryops_agent import risk_evidence
    monkeypatch.setattr(risk_evidence.subprocess,"run",lambda *a,**k:subprocess.CompletedProcess(a,1,stdout="",stderr="native failure"))
    ev=collect_evidence(request(),structured=lambda _ :{"cases":[{}]},graph=lambda _: {"vehicles":[{}]},documents=risk_evidence.document_evidence,mode="live")
    assert ev[2]["status"]=="UNAVAILABLE"
    assert assess(ev=ev)["analysis_status"]=="NEEDS_EVIDENCE"


def test_low_similarity_document_hits_do_not_enable_approval(monkeypatch):
    import subprocess,json
    from factoryops_agent import risk_evidence
    matches=[{"id":"unrelated","text":"irrelevant","score":0.2}]
    monkeypatch.setattr(risk_evidence.subprocess,"run",lambda *a,**k:subprocess.CompletedProcess(a,0,stdout=json.dumps(matches),stderr=""))
    ev=collect_evidence(request(),structured=lambda _ :{"cases":[{}]},graph=lambda _: {"vehicles":[{}]},documents=risk_evidence.document_evidence,mode="live")
    assert ev[2]["status"]=="EMPTY"
    assert ev[2]["payload"]["matches"]==[]


def test_concurrent_create_conflict_recovers_winning_snapshot(monkeypatch):
    lookups=[]
    def business(method,path,payload=None):
        if method=="POST":raise HTTPException(409,"duplicate")
        if "review-keys" in path:
            lookups.append(path)
            return {} if len(lookups)==1 else {"id":"winner","snapshot":{"request":request()}}
        return {"id":"winner","status":"PENDING_REVIEW"}
    monkeypatch.setattr(risk,"business_request",business)
    monkeypatch.setattr(risk,"assess",lambda _: {})
    result=risk.create_review(risk.ReviewRequest(request_key="race",request=risk.AssessmentRequest(**request())))
    assert result["id"]=="winner"
