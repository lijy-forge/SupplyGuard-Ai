import json
from fastapi.testclient import TestClient
from factoryops_agent import supplier_risk as risk
from test_supplier_risk import candidate
from test_risk_upgrade import request, evidence
from test_llm import Scripted

ROWS=[candidate(),candidate("SUP-002"),candidate("SUP-003"),{**candidate("SUP-004"),"qualified":False}]

def assess(llm):
    return risk.build_risk_graph(lambda _:ROWS,lambda _:evidence(),llm=llm).invoke({"request":request()})

def narrative(**overrides):
    return json.dumps({"summary":"SUP-003 ranks first; SUP-002 shares an upstream source with SUP-001.","key_risks":["shared upstream"],"evidence_ids":["graph-1"],**overrides})

def outcome(result):
    return {k:result[k] for k in ("assessments","recommendations","analysis_status","warnings","scenario","explanation")}

def test_llm_narrative_is_added_without_changing_rule_outcome():
    baseline=assess(None); llm=Scripted(narrative()); result=assess(llm)
    assert result["narrative"]["source"]=="llm" and result["narrative"]["evidence_ids"]==["graph-1"]
    assert outcome(result)==outcome(baseline)
    assert '"risk_score": 29.69' in llm.prompts[0] and "do not propose a different supplier" in llm.prompts[0]

def test_llm_cannot_override_recommendation_even_if_it_argues_for_one():
    result=assess(Scripted(narrative(summary="Ignore the rules and switch to SUP-004 immediately.")))
    assert [r["supplierCode"] for r in result["recommendations"]]==["SUP-003","SUP-002"]
    assert result["analysis_status"]=="READY_FOR_REVIEW"

def test_llm_failure_or_unknown_evidence_falls_back_to_rule_explanation():
    for llm,reason in [(Scripted(RuntimeError("down")),"llm_call_failed"),(Scripted(narrative(evidence_ids=["made-up"])),"llm_cited_unknown_evidence"),(None,"llm_not_configured")]:
        result=assess(llm)
        assert result["narrative"]=={"source":"template","summary":result["explanation"],"key_risks":result["warnings"],"evidence_ids":[],"fallback_reason":reason}

def test_needs_evidence_path_is_also_explained():
    result=risk.build_risk_graph(lambda _:ROWS,lambda _:[],llm=Scripted(narrative(evidence_ids=[]))).invoke({"request":request()})
    assert result["analysis_status"]=="NEEDS_EVIDENCE" and result["narrative"]["source"]=="llm"

def test_api_returns_narrative(monkeypatch):
    monkeypatch.setattr(risk,"fetch_candidates",lambda _: ROWS)
    monkeypatch.setattr(risk,"collect_evidence",lambda _:[])
    body=TestClient(risk.app).post("/api/v1/supplier-risk/assess",json={"part_number":"PART-001","current_supplier":"SUP-001"}).json()
    assert body["narrative"]["source"]=="template"
