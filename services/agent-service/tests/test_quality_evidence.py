import httpx
from factoryops_agent.graph import build_graph
from factoryops_agent.tools import BusinessTools
from test_graph import Business, Docs

class LinkedBusiness(Business):
    def __init__(self,supplier="SUP-777"): self.supplier=supplier; self.lookups=0
    def batch_supplier(self,case,part,batch): self.lookups+=1; return self.supplier

class FullGraph:
    def __init__(self): self.supplier_queries=[]
    def impact(self,n): return [{"model":"VM-A"},{"model":"VM-B"}]
    def batch_impact(self,n): return [{"model":"VM-A"}]
    def supplier_dependency(self,code): self.supplier_queries.append(code); return [{"part":"PART-001"}]

class DownGraph:
    def impact(self,n): raise ConnectionError("neo4j down")

class MultiDocs:
    def search(self,q): return [{"id":"DOC-002","score":0.8,"text":"FMEA brake sensor"},{"id":"DOC-004","score":0.7,"text":"QS-100 incoming"}]
class NoDocs:
    def search(self,q): return []
class BrokenDocs:
    def search(self,q): raise RuntimeError("qdrant down")

def run(business=None,graph=None,documents=None,**extra):
    g=build_graph(business=business or LinkedBusiness(),graph=graph or FullGraph(),documents=documents or Docs(),llm=None)
    return g.invoke({"question":"Assess","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001",**extra},{"configurable":{"thread_id":"evidence"}})

def by_type(result,kind): return [e for e in result["evidence"] if e["source_type"]==kind]

def test_supplier_comes_from_input_when_given():
    business=LinkedBusiness(); graph=FullGraph(); result=run(business,graph,supplier_code="SUP-123")
    assert graph.supplier_queries==["SUP-123"] and business.lookups==0
    assert by_type(result,"GRAPH")[0]["payload"]["supplier_code"]=="SUP-123"

def test_supplier_is_resolved_from_batch_linkage_otherwise():
    graph=FullGraph(); result=run(LinkedBusiness("SUP-042"),graph)
    assert graph.supplier_queries==["SUP-042"] and result["supplier_code"]=="SUP-042"

def test_unresolved_supplier_skips_dependency_query():
    graph=FullGraph(); result=run(LinkedBusiness(None),graph)
    assert graph.supplier_queries==[] and by_type(result,"GRAPH")[0]["payload"]["supplier_dependency"]==[]

def test_document_ids_come_from_retrieval():
    docs=by_type(run(documents=MultiDocs()),"DOCUMENT")
    assert [d["id"] for d in docs]==["DOCUMENT:DOC-002","DOCUMENT:DOC-004"]
    assert all(d["status"]=="AVAILABLE" and d["payload"]["matches"] for d in docs)

def test_missing_or_failed_sources_are_marked_not_faked():
    empty=run(documents=NoDocs()); broken=run(graph=DownGraph(),documents=BrokenDocs())
    assert by_type(empty,"DOCUMENT")[0]["status"]=="EMPTY"
    assert by_type(broken,"DOCUMENT")[0]["status"]=="UNAVAILABLE"
    graph=by_type(broken,"GRAPH")[0]
    assert graph["status"]=="UNAVAILABLE" and "impact" in graph["payload"]["failed_queries"]
    assert "no matching quality document" in empty["answer"]
    assert "DOCUMENT:no-match" not in empty["recommendation"]["evidence_ids"]

def test_claims_reflect_returned_data():
    result=run()
    assert by_type(result,"STRUCTURED")[0]["claim"]=="Batch BATCH-001 status QUARANTINED; 1 failed inspection(s); 1 linked issue(s)."
    assert by_type(result,"GRAPH")[0]["claim"]=="PART-001 affects vehicle models VM-A, VM-B."

def test_batch_supplier_lookup_uses_case_linkage():
    def handler(request):
        assert request.url.path.endswith("/supplier-risk/context") and request.url.params["caseNumber"]=="CASE-001"
        return httpx.Response(200,json={"cases":[{"batchNumber":"BATCH-009","supplierCode":"SUP-009"},{"batchNumber":"BATCH-001","supplierCode":"SUP-001"}]})
    tools=BusinessTools(httpx.Client(base_url="http://business/api/v1",transport=httpx.MockTransport(handler)))
    assert tools.batch_supplier("CASE-001","PART-001","BATCH-001")=="SUP-001"
    assert tools.batch_supplier("CASE-001","PART-001","BATCH-404") is None

def test_llm_may_not_cite_unavailable_evidence_as_support():
    import json
    from test_llm import Scripted
    llm=Scripted(json.dumps({"conclusion":"Contain.","evidence_ids":["STRUCTURED:BATCH-001","DOCUMENT:unavailable"],"actions":["Quarantine"],"confidence":0.7}))
    g=build_graph(business=LinkedBusiness(),graph=FullGraph(),documents=BrokenDocs(),llm=llm)
    result=g.invoke({"question":"Assess","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"},{"configurable":{"thread_id":"cite"}})
    assert result["answer_source"]=="template" and result["llm_fallback_reason"]=="llm_cited_unknown_evidence"
    assert "status=UNAVAILABLE" in llm.prompts[0]
