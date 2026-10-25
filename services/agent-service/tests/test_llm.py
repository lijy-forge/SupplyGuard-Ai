import json
import httpx
import pytest
from langgraph.types import Command
from factoryops_agent import llm as llm_module
from factoryops_agent.graph import build_graph
from test_graph import Business, Graph, Docs

class Scripted:
    def __init__(self,reply): self.reply=reply; self.prompts=[]
    def complete(self,prompt):
        self.prompts.append(prompt)
        if isinstance(self.reply,Exception): raise self.reply
        return self.reply

def run(llm):
    g=build_graph(business=Business(),graph=Graph(),documents=Docs(),llm=llm); cfg={"configurable":{"thread_id":"llm"}}
    return g,cfg,g.invoke({"question":"Assess impact","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"},cfg)

def reply(**overrides):
    body={"conclusion":"BATCH-001 failed pressure accuracy; contain stock.","evidence_ids":["STRUCTURED:BATCH-001","GRAPH:PART-001"],"actions":["Quarantine BATCH-001","Request 8D from supplier"],"confidence":0.8}
    return json.dumps({**body,**overrides})

def test_valid_llm_output_drives_answer_but_still_requires_approval():
    llm=Scripted(reply()); g,cfg,result=run(llm)
    assert result["answer_source"]=="llm" and result["llm_fallback_reason"] is None
    assert result["recommendation"]["confidence"]==0.8
    assert result["proposed_action"]=={"actionType":"SUPPLIER_CONTAINMENT","description":"Quarantine BATCH-001; Request 8D from supplier"}
    assert "id=GRAPH:PART-001" in llm.prompts[0]
    assert g.get_state(cfg).next==("approval",)
    done=g.invoke(Command(resume={"approved":True,"actor":"quality.lead"}),cfg)
    assert done["action_result"]["description"]=="Quarantine BATCH-001; Request 8D from supplier"

@pytest.mark.parametrize("bad,reason",[
    (RuntimeError("timeout"),"llm_call_failed"),
    ("not json","llm_output_invalid"),
    (reply(confidence=1.5),"llm_output_invalid"),
    (reply(evidence_ids=[]),"llm_output_invalid"),
    (reply(evidence_ids=["DOCUMENT:MADE-UP"]),"llm_cited_unknown_evidence"),
])
def test_llm_failures_fall_back_to_template(bad,reason):
    _,_,result=run(Scripted(bad))
    assert result["answer_source"]=="template" and result["llm_fallback_reason"]==reason
    assert result["proposed_action"]["description"].startswith("Quarantine stock")

def test_code_fenced_json_is_accepted():
    _,_,result=run(Scripted("```json\n"+reply()+"\n```"))
    assert result["answer_source"]=="llm"

def test_no_provider_uses_template():
    _,_,result=run(None)
    assert result["answer_source"]=="template" and result["llm_fallback_reason"]=="llm_not_configured"

def test_openai_compatible_request_shape(monkeypatch):
    monkeypatch.setattr(llm_module.settings,"openai_base_url","https://llm.example/v1/")
    monkeypatch.setattr(llm_module.settings,"openai_api_key","test-key")
    seen={}
    def handler(request):
        seen["url"]=str(request.url); seen["auth"]=request.headers["authorization"]; seen["body"]=json.loads(request.content)
        return httpx.Response(200,json={"choices":[{"message":{"content":reply()}}]})
    out=llm_module.OpenAICompatibleProvider(httpx.Client(transport=httpx.MockTransport(handler))).complete("p")
    assert json.loads(out)["confidence"]==0.8
    assert seen["url"]=="https://llm.example/v1/chat/completions" and seen["auth"]=="Bearer test-key"
    assert seen["body"]["temperature"]==0 and seen["body"]["messages"][-1]=={"role":"user","content":"p"}

def test_provider_requires_credentials(monkeypatch):
    monkeypatch.setattr(llm_module.settings,"llm_provider","openai-compatible")
    monkeypatch.setattr(llm_module.settings,"openai_api_key","")
    assert llm_module.provider() is None
    monkeypatch.setattr(llm_module.settings,"openai_base_url","https://llm.example/v1")
    monkeypatch.setattr(llm_module.settings,"openai_api_key","k")
    monkeypatch.setattr(llm_module,"_shared",None)
    first=llm_module.provider()
    assert isinstance(first,llm_module.OpenAICompatibleProvider) and llm_module.provider() is first

def test_json_mode_adds_response_format(monkeypatch):
    monkeypatch.setattr(llm_module.settings,"openai_base_url","https://api.deepseek.com")
    monkeypatch.setattr(llm_module.settings,"llm_json_mode",True)
    seen={}
    def handler(request):
        seen["url"]=str(request.url); seen["body"]=json.loads(request.content)
        return httpx.Response(200,json={"choices":[{"message":{"content":reply()}}]})
    llm_module.OpenAICompatibleProvider(httpx.Client(transport=httpx.MockTransport(handler))).complete("p")
    assert seen["url"]=="https://api.deepseek.com/chat/completions"
    assert seen["body"]["response_format"]=={"type":"json_object"}

def test_connect_timeout_is_short_and_separate(monkeypatch):
    monkeypatch.setattr(llm_module.settings,"llm_timeout_seconds",60)
    timeout=llm_module.OpenAICompatibleProvider().client.timeout
    assert timeout.connect==5 and timeout.read==60
