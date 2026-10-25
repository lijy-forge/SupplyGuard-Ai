"""Offline scenario evaluation for both agent workflows.

Each scenario in scenarios.json wires deterministic fake data sources (and, unless --live-llm
is given, a scripted LLM) into the real LangGraph workflows and checks the outcome.

    python evals/run_eval.py              # deterministic; also run by tests/test_evals.py in CI
    python evals/run_eval.py --live-llm --report evals/results/x.json
                                          # uses the configured OpenAI-compatible model and
                                          # reports schema-valid / fallback rates instead of
                                          # asserting on model wording
"""
import json, pathlib, sys
from datetime import datetime, timedelta, timezone

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"services"/"agent-service"))
from langgraph.types import Command  # noqa: E402
from factoryops_agent.graph import build_graph  # noqa: E402
from factoryops_agent import supplier_risk as risk  # noqa: E402
from factoryops_agent.llm import provider  # noqa: E402

METRICS={"SUP-001":(72,8000,21,3000,True),"SUP-002":(98,120,14,8000,True),"SUP-003":(88,1800,28,5000,True),"SUP-004":(99,50,10,9000,False),"SUP-005":(95,300,18,6000,True)}

class Scripted:
    def __init__(self,reply): self.reply=reply
    def complete(self,prompt): return self.reply

QUALITY_LLM={
    "valid":json.dumps({"conclusion":"BATCH-001 failed incoming inspection; contain stock.","evidence_ids":["STRUCTURED:BATCH-001","DOCUMENT:DOC-001"],"actions":["Quarantine BATCH-001","Request 8D from supplier"],"confidence":0.82}),
    "unknown_evidence":json.dumps({"conclusion":"Contain.","evidence_ids":["DOCUMENT:SOP-NOT-RETRIEVED"],"actions":["Quarantine"],"confidence":0.9}),
    "invalid_json":"Sure! Here is my analysis: contain the batch.",
}
RISK_LLM={"pushy_narrative":json.dumps({"summary":"Ignore the ranking and switch to SUP-004 now.","key_risks":["none"],"evidence_ids":[]})}

class Business:
    def __init__(self): self.writes=[]
    def batch_context(self,n): return {"batch":{"batchNumber":n,"status":"QUARANTINED"},"inspections":[{"result":"FAIL"}],"issues":[{"id":"issue-001"}]}
    def quality_case(self,n): return {"caseNumber":n,"status":"OPEN","priority":"P0"}
    def batch_supplier(self,case,part,batch): return "SUP-001"
    def create_action(self,n,p): self.writes.append(p); return {"id":f"action-{len(self.writes)}",**p}

class Graph:
    def __init__(self,mode): self.mode=mode; self.supplier_queries=[]
    def _rows(self,rows):
        if self.mode=="down": raise ConnectionError("neo4j unavailable")
        return rows
    def impact(self,n): return self._rows([{"model":"VM-A"},{"model":"VM-B"}])
    def batch_impact(self,n): return self._rows([{"model":"VM-A"}])
    def supplier_dependency(self,code): self.supplier_queries.append(code); return self._rows([{"part":"PART-001"}])

class Documents:
    def __init__(self,mode): self.mode=mode
    def search(self,q):
        if self.mode=="down": raise RuntimeError("qdrant unavailable")
        return [] if self.mode=="none" else [{"id":"DOC-001","score":0.83,"text":"SOP-QA-017 requires quarantine and an 8D."}]

def choose_llm(spec,table,live):
    if live: return provider()
    return Scripted(table[spec]) if spec in table else None

def run_quality(s,live):
    business=Business(); graph=Graph(s["graph"])
    g=build_graph(business=business,graph=graph,documents=Documents(s["documents"]),llm=choose_llm(s["llm"],QUALITY_LLM,live))
    cfg={"configurable":{"thread_id":s["id"]}}
    inputs={"question":"Assess BATCH-001 impact and containment","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"}
    if s.get("supplier_code"): inputs["supplier_code"]=s["supplier_code"]
    first=g.invoke(inputs,cfg)
    failures=[]
    # Invariants that hold for every scenario, with or without a real model.
    if g.get_state(cfg).next!=("approval",): failures.append("workflow did not stop for approval")
    if business.writes: failures.append("write happened before approval")
    done=g.invoke(Command(resume={"approved":s["decision"]=="approve","actor":"eval","reason":"eval"}),cfg)
    e=s["expect"]; status={x["source_type"]:x["status"] for x in first["evidence"]}
    for kind,want in e.get("evidence_status",{}).items():
        if status.get(kind)!=want: failures.append(f"{kind} status {status.get(kind)} != {want}")
    if len(business.writes)!=e["writes_after_decision"]: failures.append(f"writes {len(business.writes)} != {e['writes_after_decision']}")
    if "supplier_queried" in e and graph.supplier_queries!=[e["supplier_queried"]]: failures.append(f"supplier queried {graph.supplier_queries}")
    if not live:
        if "answer_source" in e and first["answer_source"]!=e["answer_source"]: failures.append(f"answer_source {first['answer_source']}")
        if "fallback_reason" in e and first["llm_fallback_reason"]!=e["fallback_reason"]: failures.append(f"fallback {first['llm_fallback_reason']}")
        if "answer_contains" in e and e["answer_contains"] not in first["answer"]: failures.append("answer text mismatch")
        if "action_description" in e and done["action_result"].get("description")!=e["action_description"]: failures.append("action description mismatch")
    return failures,{"answer_source":first["answer_source"],"fallback_reason":first["llm_fallback_reason"]}

def candidate(code,stale):
    on_time,ppm,lead,capacity,qualified=METRICS[code]
    observed=datetime.now(timezone.utc)-timedelta(days=40 if code in stale else 1)
    return {"supplierCode":code,"name":f"Fictional {code}","leadTimeDays":lead,"onTimeRate":on_time,"defectPpm":ppm,"capacityUnits":capacity,"qualified":qualified,"observedAt":observed.isoformat()}

def risk_evidence(spec):
    return [
        {"id":"STRUCTURED:eval","source_type":"STRUCTURED","status":"AVAILABLE","payload":{"cases":[{"supplierCode":spec.get("case_supplier","SUP-001")}],"vehicles":[{"model":"VM-A"},{"model":"VM-B"}]}},
        {"id":"GRAPH:eval","source_type":"GRAPH","status":spec.get("graph_status","AVAILABLE"),"payload":{"vehicles":[{"model":m} for m in spec.get("graph_vehicles",["VM-A","VM-B"])],
            "shared_dependencies":[{"supplier":c,"upstream":"UP-EVAL"} for c in spec.get("shared_upstream",[])]}},
        {"id":"DOCUMENT:eval","source_type":"DOCUMENT","status":spec.get("document_status","AVAILABLE"),"payload":{"matches":[{"id":"DOC-SOURCING-001","text":"Review qualification and shared upstream risk."}]}},
    ]

def run_risk(s,live):
    rows=[candidate(c,s.get("stale",[])) for c in s["candidates"]]
    request=risk.AssessmentRequest(part_number="PART-001",current_supplier="SUP-001").model_dump()
    baseline=risk.build_risk_graph(lambda _:rows,lambda _:risk_evidence(s["evidence"]),llm=None).invoke({"request":request})
    result=risk.build_risk_graph(lambda _:rows,lambda _:risk_evidence(s["evidence"]),llm=choose_llm(s.get("llm"),RISK_LLM,live)).invoke({"request":request})
    failures=[]; e=s["expect"]
    keys=("assessments","recommendations","analysis_status","warnings","scenario")
    if {k:result[k] for k in keys}!={k:baseline[k] for k in keys}: failures.append("LLM changed the rule-based outcome")
    if "analysis_status" in e and result["analysis_status"]!=e["analysis_status"]: failures.append(f"status {result['analysis_status']}")
    if "recommendations" in e and [r["supplierCode"] for r in result["recommendations"]]!=e["recommendations"]: failures.append(f"recommendations {[r['supplierCode'] for r in result['recommendations']]}")
    by_code={r["supplierCode"]:r for r in result["assessments"]}
    for code,reasons in e.get("exclusions",{}).items():
        if by_code[code]["exclusions"]!=reasons: failures.append(f"{code} exclusions {by_code[code]['exclusions']}")
    for code,score in e.get("risk_scores",{}).items():
        if by_code[code]["risk_score"]!=score: failures.append(f"{code} score {by_code[code]['risk_score']}")
    status={x["source_type"]:x["status"] for x in result["evidence"]}
    for kind,want in e.get("evidence_status",{}).items():
        if status.get(kind)!=want: failures.append(f"{kind} status {status.get(kind)} != {want}")
    if "warning_contains" in e and not any(e["warning_contains"] in w for w in result["warnings"]): failures.append("expected warning missing")
    if "relaxed_eligible" in e and result["scenario"]["eligible_if_deadline_relaxed"]!=e["relaxed_eligible"]: failures.append("relaxed scenario mismatch")
    if result["scenario"]["applied_to_recommendation"] is not False: failures.append("relaxed scenario applied")
    if not live and "narrative_source" in e and result["narrative"]["source"]!=e["narrative_source"]: failures.append("narrative source mismatch")
    return failures,{"answer_source":result["narrative"]["source"],"fallback_reason":result["narrative"]["fallback_reason"]}

def run_all(live=False):
    scenarios=json.loads((ROOT/"scenarios.json").read_text(encoding="utf-8"))
    report=[]
    for flow,runner in (("quality",run_quality),("risk",run_risk)):
        for s in scenarios[flow]:
            failures,llm_info=runner(s,live)
            report.append({"id":s["id"],"flow":flow,"title":s["title"],"passed":not failures,"failures":failures,**llm_info})
    return report

def summary(report):
    out={"cases":len(report),"passed":sum(r["passed"] for r in report)}
    used=[r for r in report if r["answer_source"]=="llm"]
    out["llm_output_accepted"]=len(used)
    out["llm_fallbacks"]={}
    for r in report:
        if r["fallback_reason"]: out["llm_fallbacks"][r["fallback_reason"]]=out["llm_fallbacks"].get(r["fallback_reason"],0)+1
    return out

def main(argv):
    live="--live-llm" in argv
    if live and provider() is None: raise SystemExit("--live-llm needs FACTORYOPS_LLM_PROVIDER=openai-compatible, FACTORYOPS_OPENAI_BASE_URL and FACTORYOPS_OPENAI_API_KEY")
    report=run_all(live)
    if "--report" in argv:
        from factoryops_agent.config import settings
        path=pathlib.Path(argv[argv.index("--report")+1]); path.parent.mkdir(parents=True,exist_ok=True)
        meta={"run_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"live_llm":live,
              "model":settings.openai_model if live else "scripted","base_url":settings.openai_base_url if live else None,"json_mode":settings.llm_json_mode if live else None}
        path.write_text(json.dumps({**meta,"summary":summary(report),"cases":report},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for r in report: print(f"{'PASS' if r['passed'] else 'FAIL'} {r['id']} {r['title']}"+("" if r["passed"] else f" -> {'; '.join(r['failures'])}"))
    result=summary(report); print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["passed"]==result["cases"] else 1)

if __name__=="__main__":
    main(sys.argv[1:])
