import json
from uuid import uuid4
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from .models import AgentState
from .tools import BusinessTools, GraphTools, DocumentTools
from .llm import ContainmentRecommendation, generate, provider
from .observability import traced

CONFIGURED=object()  # sentinel: use the LLM provider selected by settings

def evidence_item(source_type,source_id,claim,payload,status="AVAILABLE"):
    return {"id":f"{source_type}:{source_id}","source_type":source_type,"source_id":source_id,"status":status,"claim":claim,"payload":payload}

def models_of(rows): return sorted({r["model"] for r in rows if r.get("model")})

def containment_prompt(s):
    lines=[f"- id={e['id']} type={e['source_type']} status={e['status']} claim={e['claim']} payload={json.dumps(e['payload'],default=str,ensure_ascii=False)[:1500]}" for e in s["evidence"]]
    return (f"Quality case {s['case_number']}, part {s['part_number']}, batch {s['batch_number']}.\nQuestion: {s['question']}\nEvidence:\n"+"\n".join(lines)+
            "\nUsing only this evidence, return JSON with keys: conclusion (at most 4 sentences and under 600 characters), evidence_ids (ids of AVAILABLE evidence above that support the conclusion), "
            "actions (at most 6 concrete containment steps), confidence (0 to 1). Do not invent evidence ids.")

def build_graph(checkpointer=None,business=None,graph=None,documents=None,llm=CONFIGURED):
    business=business or BusinessTools(); graph=graph or GraphTools(); documents=documents or DocumentTools()
    llm=provider() if llm is CONFIGURED else llm
    def plan(s): return {"intent":"quality_impact_and_containment","correlation_id":s.get("correlation_id",str(uuid4())),"evidence":[]}
    def structured(s):
        ctx=business.batch_context(s["batch_number"]); case=business.quality_case(s["case_number"])
        supplier=s.get("supplier_code")
        if not supplier:
            try: supplier=business.batch_supplier(s["case_number"],s["part_number"],s["batch_number"])
            except Exception: supplier=None
        failed=sum(1 for i in ctx.get("inspections",[]) if i.get("result")=="FAIL")
        batch_claim=f"Batch {s['batch_number']} status {ctx.get('batch',{}).get('status','UNKNOWN')}; {failed} failed inspection(s); {len(ctx.get('issues',[]))} linked issue(s)."
        case_claim=f"Quality case {s['case_number']} is {case.get('status','UNKNOWN')} with priority {case.get('priority','UNKNOWN')}."
        return {"supplier_code":supplier,"evidence":s["evidence"]+[evidence_item("STRUCTURED",s["batch_number"],batch_claim,ctx),evidence_item("STRUCTURED",s["case_number"],case_claim,case)]}
    def knowledge(s):
        failures=[]
        def query(name,*args):
            try: return getattr(graph,name)(*args)
            except Exception: failures.append(name); return []
        part_rows=query("impact",s["part_number"])
        batch_rows=query("batch_impact",s["batch_number"])
        supplier=s.get("supplier_code")
        supplier_rows=query("supplier_dependency",supplier) if supplier else []
        payload={"part_vehicle_impact":part_rows,"batch_impact":batch_rows,"supplier_dependency":supplier_rows,"supplier_code":supplier,"failed_queries":failures}
        models=models_of(part_rows+batch_rows)
        status="AVAILABLE" if models else "UNAVAILABLE" if failures else "EMPTY"
        claim=f"{s['part_number']} affects vehicle models {', '.join(models)}." if models else f"No vehicle impact found in the graph for {s['part_number']}."
        return {"evidence":s["evidence"]+[evidence_item("GRAPH",s["part_number"],claim,payload,status)]}
    def vector(s):
        try: rows=documents.search(s["question"])
        except Exception:
            return {"evidence":s["evidence"]+[evidence_item("DOCUMENT","unavailable","Document search failed.",{"matches":[]},"UNAVAILABLE")]}
        if not rows: return {"evidence":s["evidence"]+[evidence_item("DOCUMENT","no-match","No quality document matched the question.",{"matches":[]},"EMPTY")]}
        # One evidence item per retrieved document so each can be cited by its own id.
        return {"evidence":s["evidence"]+[evidence_item("DOCUMENT",str(m["id"]),str(m.get("text",""))[:300],{"matches":[m]}) for m in rows]}
    def template_answer(s):
        description="Quarantine stock, notify supplier, and request an 8D within 24 hours."
        models=models_of([r for e in s["evidence"] if e["source_type"]=="GRAPH" for r in e["payload"]["part_vehicle_impact"]+e["payload"]["batch_impact"]])
        docs=[e["source_id"] for e in s["evidence"] if e["source_type"]=="DOCUMENT" and e["status"]=="AVAILABLE"]
        conclusion=(f"{s['batch_number']} is under investigation; {s['part_number']} affects {', '.join(models) or 'no vehicle models found in the graph'}. "
                    f"Recommend supplier containment under {s['case_number']}"+(f" per {', '.join(docs)}." if docs else "; no matching quality document was retrieved."))
        return {"answer":conclusion,"proposed_action":{"actionType":"SUPPLIER_CONTAINMENT","description":description},
                "recommendation":{"conclusion":conclusion,"evidence_ids":[e["id"] for e in s["evidence"] if e["status"]=="AVAILABLE"],"actions":[description],"confidence":None}}
    def answer(s):
        # Only evidence that was actually retrieved may be cited as support.
        result,failure=generate(llm,containment_prompt(s),ContainmentRecommendation,{e["id"] for e in s["evidence"] if e["status"]=="AVAILABLE"})
        if result is None: return {**template_answer(s),"answer_source":"template","llm_fallback_reason":failure}
        # The action type stays fixed: the model only words the containment plan a human then approves.
        return {"answer":result.conclusion,"recommendation":result.model_dump(),"answer_source":"llm","llm_fallback_reason":None,
                "proposed_action":{"actionType":"SUPPLIER_CONTAINMENT","description":"; ".join(result.actions)[:2000]}}
    def approval(s):
        decision=interrupt({"kind":"approval_required","caseNumber":s["case_number"],"proposedAction":s["proposed_action"],"evidence":s["evidence"]})
        return {"approval":decision}
    def route(s): return "execute" if s["approval"].get("approved") else "reject"
    def execute(s):
        p={**s["proposed_action"],"actor":s["approval"].get("actor","quality.lead"),"correlationId":s["correlation_id"]}
        return {"action_result":business.create_action(s["case_number"],p)}
    def reject(s): return {"action_result":{"status":"REJECTED","reason":s["approval"].get("reason","")}}
    g=StateGraph(AgentState)
    for name,fn in [("plan",plan),("structured",structured),("graph",knowledge),("vector",vector),("answer",answer),("approval",approval),("execute",execute),("reject",reject)]: g.add_node(name,traced("quality",name,fn))
    g.add_edge(START,"plan"); g.add_edge("plan","structured"); g.add_edge("structured","graph"); g.add_edge("graph","vector"); g.add_edge("vector","answer"); g.add_edge("answer","approval")
    g.add_conditional_edges("approval",route,{"execute":"execute","reject":"reject"}); g.add_edge("execute",END); g.add_edge("reject",END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())

def redis_checkpointer():
    from langgraph.checkpoint.redis import RedisSaver
    saver=RedisSaver(redis_url=__import__("factoryops_agent.config",fromlist=["settings"]).settings.redis_url)
    saver.setup()
    return saver
