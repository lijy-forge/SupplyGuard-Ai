from factoryops_agent.graph import build_graph
from langgraph.types import Command

class Business:
    def batch_context(self,n): return {"batch":{"batchNumber":n,"status":"QUARANTINED"},"inspections":[{"result":"FAIL"}],"issues":[{"id":"issue-001"}]}
    def quality_case(self,n): return {"caseNumber":n,"status":"OPEN","priority":"P0"}
    def create_action(self,n,p): return {"id":"action-001","caseNumber":n,**p}
class Graph:
    def impact(self,n): return [{"model":"VM-A"},{"model":"VM-B"}]
class Docs:
    def search(self,q): return [{"id":"SOP-QA-017","score":0.91,"text":"quarantine and 8D"}]

def test_real_langgraph_interrupt_resume_and_evidence_contract():
    g=build_graph(business=Business(),graph=Graph(),documents=Docs()); cfg={"configurable":{"thread_id":"golden-1"}}
    first=g.invoke({"question":"Assess impact and contain", "case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"},cfg)
    assert len(first["evidence"])==4; assert {e["source_type"] for e in first["evidence"]}=={"STRUCTURED","GRAPH","DOCUMENT"}
    snapshot=g.get_state(cfg); assert snapshot.next==("approval",); assert snapshot.tasks[0].interrupts
    done=g.invoke(Command(resume={"approved":True,"actor":"quality.lead"}),cfg)
    assert done["action_result"]["id"]=="action-001"

def test_rejection_never_calls_side_effect():
    g=build_graph(business=Business(),graph=Graph(),documents=Docs()); cfg={"configurable":{"thread_id":"golden-2"}}
    g.invoke({"question":"Assess", "case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"},cfg)
    done=g.invoke(Command(resume={"approved":False,"reason":"need more evidence"}),cfg)
    assert done["action_result"]["status"]=="REJECTED"
