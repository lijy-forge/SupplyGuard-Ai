"""Read-only risk assessment: rules decide scores and recommendations; an optional LLM only words the narrative."""
import json
import os
from datetime import datetime, timezone, timedelta
from .risk_evidence import collect_evidence, business_base
from typing import TypedDict
import httpx
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, START, END
from .llm import RiskNarrative, generate, provider
from .observability import traced, configure_logging

CONFIGURED=object()  # sentinel: use the LLM provider selected by settings

class AssessmentRequest(BaseModel):
    part_number: str = Field(min_length=1,max_length=80,pattern=r"^[A-Za-z0-9_-]+$")
    current_supplier: str = Field(min_length=1,max_length=50,pattern=r"^[A-Za-z0-9_-]+$")
    case_number: str = Field(default="CASE-001",min_length=1,max_length=80,pattern=r"^[A-Za-z0-9_-]+$")
    required_units: int = Field(default=4000,gt=0,le=10000000)
    max_lead_days: int = Field(default=21,gt=0,le=365)

class Candidate(BaseModel):
    supplierCode: str
    name: str
    leadTimeDays: int = Field(ge=0)
    onTimeRate: float = Field(ge=0,le=100)
    defectPpm: int = Field(ge=0,le=1000000)
    capacityUnits: int = Field(ge=0)
    qualified: bool
    observedAt: datetime

class State(TypedDict, total=False):
    request: dict
    candidates: list
    assessments: list
    recommendations: list
    warnings: list
    evidence: list
    analysis_status: str
    scenario: dict
    explanation: str
    narrative: dict

def fetch_candidates(part):
    base=os.getenv("FACTORYOPS_BUSINESS_URL","http://localhost:8081/api/v1").rstrip("/")
    try:
        response=httpx.get(f"{base}/supplier-risk/candidates",params={"partNumber":part},timeout=10,trust_env=False)
        if response.status_code==404: raise HTTPException(404,"part not found")
        response.raise_for_status()
        data=response.json()
        if not isinstance(data,list): raise ValueError("invalid candidate response")
        return data
    except (httpx.HTTPError,ValueError) as exc:
        raise HTTPException(503,"business service unavailable or invalid response") from exc

def narrative_prompt(state):
    rows=[{k:r[k] for k in ("supplierCode","base_score","graph_penalty","risk_score","risk_level","exclusions")} for r in state["assessments"]]
    evidence=[{"id":e["id"],"source_type":e["source_type"],"status":e["status"],"payload":json.dumps(e["payload"],default=str)[:1000]} for e in state["evidence"]]
    return ("Explain this supplier risk assessment for a procurement reviewer. The scores, exclusions and recommendation order were computed by fixed rules; "
            "describe them faithfully and do not propose a different supplier or ranking.\n"
            f"Status: {state['analysis_status']}\nCurrent supplier: {state['request']['current_supplier']}\n"
            f"Assessments: {json.dumps(rows)}\nRecommended order: {[r['supplierCode'] for r in state['recommendations']]}\n"
            f"Warnings: {json.dumps(state['warnings'])}\nEvidence: {json.dumps(evidence)}\n"
            "Return JSON with keys: summary (at most 5 sentences and under 900 characters), key_risks (at most 5 short strings), evidence_ids (ids from Evidence that you relied on).")

def build_risk_graph(fetch=None, evidence_provider=None, llm=CONFIGURED):
    fetch = fetch or fetch_candidates
    evidence_provider = evidence_provider or collect_evidence
    llm = provider() if llm is CONFIGURED else llm
    def collect(state):
        return {"candidates":fetch(state["request"]["part_number"])}
    def assess(state):
        rows=[]; warnings=[]; req=state["request"]
        for raw in state["candidates"]:
            try: c=Candidate.model_validate(raw)
            except ValidationError:
                warnings.append("Incomplete or invalid candidate metrics; candidate excluded")
                continue
            score=round(min(100, .5*(100-c.onTimeRate)+.3*min(100,c.defectPpm/100)+.2*min(100,c.leadTimeDays/req["max_lead_days"]*100)),2)
            reasons=[]
            observed=c.observedAt
            if observed.tzinfo is None or observed < datetime.now(timezone.utc)-timedelta(days=30) or observed > datetime.now(timezone.utc)+timedelta(minutes=5):
                reasons.append("metrics stale or timestamp invalid")
            if not c.qualified: reasons.append("qualification required")
            if c.capacityUnits<req["required_units"]: reasons.append("insufficient capacity")
            if c.leadTimeDays>req["max_lead_days"]: reasons.append("lead time exceeds limit")
            rows.append({**c.model_dump(mode="json"),"base_score":score,"graph_penalty":0,"risk_score":score,"risk_level":"HIGH" if score>=40 else "MEDIUM" if score>=20 else "LOW","exclusions":reasons})
        if not any(c["supplierCode"]==req["current_supplier"] for c in rows):
            raise HTTPException(422,"current supplier missing or has invalid metrics")
        return {"assessments":rows,"warnings":warnings}
    def enrich(state):
        evidence=evidence_provider(state["request"])
        rows=[dict(row) for row in state["assessments"]]
        warnings=list(state["warnings"])
        for item in evidence:
            if item["status"] not in ("AVAILABLE","DEMO"):
                warnings.append(f"{item['source_type']} evidence: {item['status']}; approval requires complete live evidence")
            if item["source_type"]=="STRUCTURED" and item["status"]=="AVAILABLE":
                cases=item["payload"].get("cases",[])
                if not any(c.get("supplierCode")==state["request"]["current_supplier"] for c in cases):
                    item["status"]="CONFLICT";warnings.append("Quality case does not implicate current supplier")
            if item["source_type"]=="GRAPH" and item["status"] in ("AVAILABLE","DEMO"):
                shared={d["supplier"] for d in item["payload"].get("shared_dependencies",[]) if d.get("supplier")}
                for row in rows:
                    if row["supplierCode"] in shared:
                        row["graph_penalty"]=15
                        row["risk_score"]=min(100,round(row["base_score"]+15,2))
                        row["risk_level"]="HIGH" if row["risk_score"]>=40 else "MEDIUM" if row["risk_score"]>=20 else "LOW"
                        row["risk_factors"]=["shares upstream dependency with current supplier"]
        sources={e["source_type"]:e for e in evidence}
        structured=sources.get("STRUCTURED",{});graph=sources.get("GRAPH",{})
        if structured.get("status")==graph.get("status")=="AVAILABLE":
            relational={r["model"] for r in structured["payload"].get("vehicles",[])}
            network={r["model"] for r in graph["payload"].get("vehicles",[])}
            if relational!=network:
                graph["status"]="CONFLICT";warnings.append("Graph and BOM vehicle impact disagree; reconcile before approval")
        return {"assessments":rows,"evidence":evidence,"warnings":warnings}
    def recommend(state):
        choices=[c for c in state["assessments"] if c["supplierCode"]!=state["request"]["current_supplier"] and not c["exclusions"]]
        choices.sort(key=lambda c:(c["risk_score"],c["supplierCode"]))
        req=state["request"]
        relaxed=[r["supplierCode"] for r in state["assessments"] if r["supplierCode"]!=req["current_supplier"] and r["qualified"] and r["capacityUnits"]>=req["required_units"] and r["leadTimeDays"]<=req["max_lead_days"]+14 and all(x=="lead time exceeds limit" for x in r["exclusions"])]
        return {"recommendations":choices,"scenario":{"baseline_max_lead_days":req["max_lead_days"],"relaxed_max_lead_days":req["max_lead_days"]+14,"eligible_if_deadline_relaxed":relaxed,"applied_to_recommendation":False},"warnings":state["warnings"]+([] if choices else ["No eligible alternate supplier; manual sourcing required"])}
    def route(state):
        sources={e["source_type"] for e in state["evidence"] if e["status"]=="AVAILABLE"}
        return "ready" if sources=={"STRUCTURED","GRAPH","DOCUMENT"} and state["recommendations"] else "needs_evidence"
    def finish(state, status):
        citations=", ".join(e["id"] for e in state["evidence"] if e["status"] in ("AVAILABLE","DEMO"))
        return {"analysis_status":status,"explanation":f"{len(state['recommendations'])} eligible alternate(s), constrained by qualification, capacity and lead time. Score includes 15-point common-upstream penalty where observed. Evidence: {citations or 'none'}. Human review required; no sourcing change executed."}

    def explain(state):
        # Runs after the rule-based outcome is final and may only add the narrative field.
        result,failure=generate(llm,narrative_prompt(state),RiskNarrative,{e["id"] for e in state["evidence"]})
        if result is None: return {"narrative":{"source":"template","summary":state["explanation"],"key_risks":state["warnings"],"evidence_ids":[],"fallback_reason":failure}}
        return {"narrative":{"source":"llm",**result.model_dump(),"fallback_reason":None}}

    graph=StateGraph(State)
    nodes={"collect":collect,"assess":assess,"enrich":enrich,"recommend":recommend,
           "ready":lambda s:finish(s,"READY_FOR_REVIEW"),"needs_evidence":lambda s:finish(s,"NEEDS_EVIDENCE"),"explain":explain}
    for name,fn in nodes.items(): graph.add_node(name,traced("supplier_risk",name,fn))
    graph.add_edge(START,"collect");graph.add_edge("collect","assess");graph.add_edge("assess","enrich");graph.add_edge("enrich","recommend");graph.add_conditional_edges("recommend",route,{"ready":"ready","needs_evidence":"needs_evidence"});graph.add_edge("ready","explain");graph.add_edge("needs_evidence","explain");graph.add_edge("explain",END)
    return graph.compile()

router=APIRouter()
@router.post("/api/v1/supplier-risk/assess")
def assess(request:AssessmentRequest):
    result=build_risk_graph().invoke({"request":request.model_dump()})
    return {"part_number":request.part_number,"request":request.model_dump(),"method":"rules-v2: delivery 50%, quality 30%, lead time 20%; +15 shared upstream risk","requires_human_approval":True,**{k:result[k] for k in ("assessments","recommendations","warnings","evidence","analysis_status","scenario","explanation","narrative")}}

class ReviewRequest(BaseModel):
    request_key: str = Field(min_length=1,max_length=80,pattern=r"^[A-Za-z0-9_-]+$")
    request: AssessmentRequest

class ReviewDecision(BaseModel):
    version: int = Field(ge=0)
    approved: bool
    supplier_code: str = Field(max_length=50)
    actor: str = Field(min_length=1,max_length=100,pattern=r".*\S.*")
    reason: str = Field(min_length=1,max_length=2000,pattern=r".*\S.*")

def business_request(method,path,payload=None):
    try:
        response=httpx.request(method,f"{business_base()}{path}",json=payload,timeout=15,trust_env=False)
        if response.status_code in (400,404,409,422):raise HTTPException(response.status_code,"Review rejected by business rules; check evidence, current constraints and version")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError,ValueError) as exc:raise HTTPException(503,"review store unavailable") from exc

@router.post("/api/v1/supplier-risk/reviews")
def create_review(body:ReviewRequest):
    # The client submits inputs, never an arbitrary decision snapshot.
    # Fast retries with this key return the persisted snapshot, avoiding new evidence timestamps.
    existing=business_request("GET",f"/supplier-risk/review-keys/{body.request_key}")
    if existing.get("id"):
        if existing["snapshot"]["request"]!=body.request.model_dump():raise HTTPException(409,"request key reused with different assessment input")
        return business_request("GET",f"/supplier-risk/reviews/{existing['id']}")
    snapshot=assess(body.request)
    try:
        return business_request("POST","/supplier-risk/reviews",{"request_key":body.request_key,"case_number":body.request.case_number,"snapshot":snapshot})
    except HTTPException as exc:
        if exc.status_code!=409:raise
        # Another request may have committed the same key while evidence was collected.
        winner=business_request("GET",f"/supplier-risk/review-keys/{body.request_key}")
        if winner.get("id") and winner["snapshot"]["request"]==body.request.model_dump():
            return business_request("GET",f"/supplier-risk/reviews/{winner['id']}")
        raise

@router.get("/api/v1/supplier-risk/reviews/{review_id}")
def get_review(review_id:str):
    return business_request("GET",f"/supplier-risk/reviews/{review_id}")

@router.get("/api/v1/supplier-risk/reviews/{review_id}/audit")
def get_audit(review_id:str):
    return business_request("GET",f"/supplier-risk/reviews/{review_id}/audit")

@router.post("/api/v1/supplier-risk/reviews/{review_id}/decision")
def decide_review(review_id:str,body:ReviewDecision):
    return business_request("POST",f"/supplier-risk/reviews/{review_id}/decision",body.model_dump())
configure_logging()
app=FastAPI(title="Supplier Risk Agent")
app.include_router(router)
