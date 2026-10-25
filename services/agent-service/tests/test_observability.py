import json, logging
import pytest
from langgraph.types import Command
from factoryops_agent import observability
from factoryops_agent.graph import build_graph
from factoryops_agent import supplier_risk as risk
from test_graph import Business, Graph, Docs
from test_supplier_risk import candidate
from test_risk_upgrade import request, evidence

def records(caplog): return [json.loads(r.getMessage()) for r in caplog.records if r.name=="supplyguard.trace"]

def test_quality_nodes_are_traced_with_thread_status_and_duration(caplog):
    caplog.set_level(logging.INFO,logger="supplyguard.trace")
    g=build_graph(business=Business(),graph=Graph(),documents=Docs(),llm=None); cfg={"configurable":{"thread_id":"trace-1"}}
    g.invoke({"question":"Assess","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"},cfg)
    first=records(caplog)
    assert [r["span"] for r in first]==["quality.plan","quality.structured","quality.graph","quality.vector","quality.answer","quality.approval"]
    assert first[-1]["status"]=="interrupted" and first[-1]["output"] is None
    assert all(r["thread_id"]=="trace-1" and r["duration_ms"]>=0 for r in first)
    assert '"answer_source": "template"' in first[4]["output"] and '"batch_number": "BATCH-001"' in first[0]["input"]
    caplog.clear()
    g.invoke(Command(resume={"approved":True,"actor":"quality.lead"}),cfg)
    assert [(r["span"],r["status"]) for r in records(caplog)]==[("quality.approval","ok"),("quality.execute","ok")]

def test_risk_nodes_are_traced(caplog):
    caplog.set_level(logging.INFO,logger="supplyguard.trace")
    risk.build_risk_graph(lambda _:[candidate(),candidate("SUP-002")],lambda _:evidence(),llm=None).invoke({"request":request()})
    assert [r["span"] for r in records(caplog)]==["supplier_risk."+n for n in ("collect","assess","enrich","recommend","ready","explain")]

def test_errors_are_recorded_and_reraised(caplog):
    caplog.set_level(logging.INFO,logger="supplyguard.trace")
    def boom(state): raise ValueError("bad input")
    with pytest.raises(ValueError): observability.traced("t","boom",boom)({"x":1})
    (r,)=records(caplog)
    assert r["status"]=="error" and r["error"]=="ValueError: bad input"

def test_large_payloads_are_truncated():
    text=observability.preview({"blob":"x"*5000})
    assert len(text)<observability.PREVIEW_CHARS+40 and text.endswith("chars)")

class FakeSpan:
    def __init__(self,sink,**kw): self.sink=sink; self.data=dict(kw)
    def update(self,**kw): self.data.update(kw)
    def end(self): self.sink.append(self.data)
class FakeLangfuse:
    def __init__(self): self.spans=[]
    def start_observation(self,**kw): return FakeSpan(self.spans,**kw)

def test_langfuse_receives_input_output_and_timing(monkeypatch):
    client=FakeLangfuse(); monkeypatch.setattr(observability,"langfuse_client",lambda:client)
    observability.traced("t","node",lambda s:{"y":2})({"x":1},{"configurable":{"thread_id":"lf"}})
    (span,)=client.spans
    assert span["name"]=="t.node" and span["input"]=='{"x": 1}' and span["output"]=='{"y": 2}'
    assert span["metadata"]["thread_id"]=="lf" and span["metadata"]["status"]=="ok" and "duration_ms" in span["metadata"]

def test_exporter_failure_never_breaks_the_node(monkeypatch):
    class Broken:
        def start_observation(self,**kw): raise RuntimeError("langfuse down")
    monkeypatch.setattr(observability,"langfuse_client",lambda:Broken())
    assert observability.traced("t","node",lambda s:{"ok":True})({})=={"ok":True}

def test_langfuse_disabled_without_credentials(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY",raising=False)
    assert observability.langfuse_client() is None
