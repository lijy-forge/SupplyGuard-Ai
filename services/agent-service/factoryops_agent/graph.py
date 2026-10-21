from uuid import uuid4
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from .models import AgentState
from .tools import BusinessTools, GraphTools, DocumentTools

def build_graph(checkpointer=None,business=None,graph=None,documents=None):
    business=business or BusinessTools(); graph=graph or GraphTools(); documents=documents or DocumentTools()
    def plan(s): return {"intent":"quality_impact_and_containment","correlation_id":s.get("correlation_id",str(uuid4())),"evidence":[]}
    def structured(s):
        ctx=business.batch_context(s["batch_number"]); case=business.quality_case(s["case_number"])
        return {"evidence":s["evidence"]+[{"source_type":"STRUCTURED","source_id":s["batch_number"],"claim":"Batch is quarantined and linked to a failed inspection.","payload":ctx},{"source_type":"STRUCTURED","source_id":s["case_number"],"claim":"An open P0 quality case governs containment.","payload":case}]}
    def knowledge(s):
        try: part_rows=graph.impact(s["part_number"])
        except Exception: part_rows=[]
        try: batch_rows=graph.batch_impact(s["batch_number"])
        except Exception: batch_rows=[]
        try: supplier_rows=graph.supplier_dependency("SUP-001")
        except Exception: supplier_rows=[]
        return {"evidence":s["evidence"]+[{"source_type":"GRAPH","source_id":s["part_number"],"claim":"Vehicle-model, batch, and supplier dependency impact is derived from the graph.","payload":{"part_vehicle_impact":part_rows,"batch_impact":batch_rows,"supplier_dependency":supplier_rows}}]}
    def vector(s):
        try: rows=documents.search(s["question"])
        except Exception: rows=[]
        return {"evidence":s["evidence"]+[{"source_type":"DOCUMENT","source_id":"SOP-QA-017","claim":"Containment SOP requires quarantine, supplier notification and 8D.","payload":{"matches":rows}}]}
    def answer(s): return {"answer":f"{s['batch_number']} has a failed safety inspection; {s['part_number']} affects the linked vehicle models. Recommend supplier containment under {s['case_number']}.","proposed_action":{"actionType":"SUPPLIER_CONTAINMENT","description":"Quarantine stock, notify supplier, and request an 8D within 24 hours."}}
    def approval(s):
        decision=interrupt({"kind":"approval_required","caseNumber":s["case_number"],"proposedAction":s["proposed_action"],"evidence":s["evidence"]})
        return {"approval":decision}
    def route(s): return "execute" if s["approval"].get("approved") else "reject"
    def execute(s):
        p={**s["proposed_action"],"actor":s["approval"].get("actor","quality.lead"),"correlationId":s["correlation_id"]}
        return {"action_result":business.create_action(s["case_number"],p)}
    def reject(s): return {"action_result":{"status":"REJECTED","reason":s["approval"].get("reason","")}}
    g=StateGraph(AgentState)
    for name,fn in [("plan",plan),("structured",structured),("graph",knowledge),("vector",vector),("answer",answer),("approval",approval),("execute",execute),("reject",reject)]: g.add_node(name,fn)
    g.add_edge(START,"plan"); g.add_edge("plan","structured"); g.add_edge("structured","graph"); g.add_edge("graph","vector"); g.add_edge("vector","answer"); g.add_edge("answer","approval")
    g.add_conditional_edges("approval",route,{"execute":"execute","reject":"reject"}); g.add_edge("execute",END); g.add_edge("reject",END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())

def redis_checkpointer():
    from langgraph.checkpoint.redis import RedisSaver
    saver=RedisSaver(redis_url=__import__("factoryops_agent.config",fromlist=["settings"]).settings.redis_url)
    saver.setup()
    return saver
