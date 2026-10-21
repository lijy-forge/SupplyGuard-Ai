"""Adapters reuse existing graph/vector tools; synthetic evidence never enables approval."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import httpx

def business_base():
    return os.getenv("FACTORYOPS_BUSINESS_URL","http://localhost:8081/api/v1").rstrip("/")

def graph_evidence(request):
    from .tools import GraphTools
    return GraphTools().risk_context(request["part_number"],request["current_supplier"])

def document_evidence(request):
    # Isolate native embedding runtimes: a DLL crash must not kill the Agent API.
    question=f"Supplier switching qualification PPAP capacity common upstream risk for {request['part_number']}"
    code="import json,sys; from factoryops_agent.tools import DocumentTools; print(json.dumps(DocumentTools().search(json.load(sys.stdin)['query'])))"
    result=subprocess.run([sys.executable,"-c",code],input=json.dumps({"query":question}),text=True,capture_output=True,timeout=25)
    if result.returncode:raise RuntimeError("vector worker failed")
    matches=json.loads(result.stdout)
    if not isinstance(matches,list):raise ValueError("invalid document evidence")
    matches=[m for m in matches if isinstance(m,dict) and m.get("id") and m.get("text") and isinstance(m.get("score"),(int,float)) and m["score"]>=0.55]
    return {"matches":matches,"min_similarity":0.55,"query":question}

def structured_evidence(request):
    response=httpx.get(f"{business_base()}/supplier-risk/context",params={"partNumber":request["part_number"],"caseNumber":request["case_number"]},timeout=10,trust_env=False)
    response.raise_for_status()
    data=response.json()
    if not isinstance(data,dict) or not data.get("cases"):raise ValueError("case evidence missing")
    return data

def collect_evidence(request, structured=None, graph=None, documents=None, mode=None):
    mode=mode or os.getenv("FACTORYOPS_RISK_EVIDENCE_MODE","structured")
    if mode not in ("structured","live","demo"):raise ValueError("invalid risk evidence mode")
    adapters={"STRUCTURED":structured or structured_evidence,"GRAPH":graph or graph_evidence,"DOCUMENT":documents or document_evidence}
    def retrieve(kind):
        evidence={"id":f"{kind}:{request['part_number']}:{request['case_number']}","source_type":kind,"status":"NOT_CONFIGURED","retrieved_at":datetime.now(timezone.utc).isoformat(),"payload":{}}
        if kind!="STRUCTURED" and mode!="live":
            if mode=="demo" and request["part_number"]=="PART-001" and request["current_supplier"]=="SUP-001":
                evidence.update(status="DEMO",payload=({"part_number":"PART-001","vehicles":[{"model":"VM-A"},{"model":"VM-B"}],"shared_dependencies":[{"supplier":"SUP-002","upstream":"UP-DEMO-001"}]} if kind=="GRAPH" else {"matches":[{"id":"DOC-SOURCING-001","text":"Synthetic policy: validate qualification and review common upstream risk before supplier switching."}]}))
            return evidence
        try:
            payload=adapters[kind](request)
            if not isinstance(payload,dict):raise ValueError("invalid evidence")
            present=bool(payload.get("cases")) if kind=="STRUCTURED" else bool(payload.get("vehicles")) if kind=="GRAPH" else bool(payload.get("matches"))
            evidence.update(status="AVAILABLE" if present else "EMPTY",payload=payload)
        except Exception:
            evidence["status"]="UNAVAILABLE"
        return evidence
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(retrieve,adapters))
