"""Run only against docker-compose.factoryops.yml on a real Docker daemon."""
import json, os, subprocess, time, urllib.request, uuid

COMPOSE=["docker","compose","-f","docker/docker-compose.factoryops.yml"]
def compose(*args): return subprocess.check_output([*COMPOSE,*args],text=True).strip()
def request(url,method="GET",payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,method=method,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as response: return json.load(response)
def sql(statement): return compose("exec","-T","mysql","mysql","-N","-uroot","-proot","factoryops","-e",statement)
def wait_for(check,description,seconds=120):
    deadline=time.time()+seconds; error=None
    while time.time()<deadline:
        try:
            value=check()
            if value: return value
        except Exception as exc: error=exc
        time.sleep(2)
    raise AssertionError(f"timed out waiting for {description}: {error}")

def main():
    for port,path in [(8081,"/actuator/health"),(8082,"/health"),(3000,"/")]:
        wait_for(lambda p=port,x=path: urllib.request.urlopen(f"http://127.0.0.1:{p}{x}",timeout=3).status==200,f"http://127.0.0.1:{port}{path}")
    assert request("http://127.0.0.1:8081/api/v1/suppliers/SUP-001")["supplierCode"]=="SUP-001"
    assert len(request("http://127.0.0.1:8081/api/v1/parts/PART-001/impact"))==2
    assert request("http://127.0.0.1:8081/api/v1/batches/BATCH-001/context")["batch"]["batchNumber"]=="BATCH-001"
    assert request("http://127.0.0.1:8081/api/v1/quality-cases/CASE-001")["caseNumber"]=="CASE-001"
    nodes=int(compose("exec","-T","neo4j","cypher-shell","-u","neo4j","-p","factoryops","MATCH (n) RETURN count(n);" ).splitlines()[-1])
    rels=int(compose("exec","-T","neo4j","cypher-shell","-u","neo4j","-p","factoryops","MATCH ()-[r]->() RETURN count(r);" ).splitlines()[-1])
    assert nodes>=6 and rels>=5
    collection=request("http://127.0.0.1:6333/collections/factoryops_documents")["result"]
    assert collection["points_count"]>=4
    before=int(sql("SELECT COUNT(*) FROM corrective_actions;"))
    question="BATCH-001 出现尺寸异常，会影响哪些车型？相关 FMEA/SOP 有哪些风险和处置要求？如果需要，请提出整改任务。"
    first=request("http://127.0.0.1:8082/api/v1/agent/runs","POST",{"question":question,"thread_id":"live-approve","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"})
    kinds={item["source_type"] for item in first["evidence"]}; assert kinds=={"STRUCTURED","GRAPH","DOCUMENT"}
    graph=next(item for item in first["evidence"] if item["source_type"]=="GRAPH")["payload"]
    assert graph["part_vehicle_impact"] and graph["batch_impact"] and graph["supplier_dependency"]
    documents=next(item for item in first["evidence"] if item["source_type"]=="DOCUMENT")["payload"]["matches"]
    assert documents and int(sql("SELECT COUNT(*) FROM corrective_actions;"))==before
    pending=request("http://127.0.0.1:8082/api/v1/agent/runs/live-approve"); assert "approval" in pending["next"]
    compose("restart","agent-service")
    wait_for(lambda: urllib.request.urlopen("http://127.0.0.1:8082/health",timeout=3).status==200,"agent restart")
    approved=request("http://127.0.0.1:8082/api/v1/agent/resume","POST",{"thread_id":"live-approve","approved":True,"actor":"quality.lead","reason":"live verified"})
    assert "action_result" in approved, approved
    action_id=approved["action_result"]["id"]
    assert int(sql("SELECT COUNT(*) FROM corrective_actions;"))==before+1
    assert int(sql("SELECT COUNT(*) FROM audit_events WHERE action='CORRECTIVE_ACTION_CREATED';"))>=1
    assert int(sql("SELECT COUNT(*) FROM outbox_events WHERE event_type='corrective-action.created';"))>=1
    wait_for(lambda: compose("exec","-T","redis","redis-cli","EXISTS",f"factoryops:consumer:{action_id}")=="1","RabbitMQ consumer receipt")
    consumed=compose("exec","-T","redis","redis-cli","GET",f"factoryops:consumer:{action_id}")
    duplicate=("import json,pika; c=pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@rabbitmq:5672/%2F')); "
               f"c.channel().basic_publish(exchange='factoryops.events',routing_key='corrective-action.created',body=json.dumps({{'actionId':'{action_id}','correlationId':'duplicate'}})); c.close()")
    compose("exec","-T","agent-service","python","-c",duplicate)
    time.sleep(2)
    assert compose("exec","-T","redis","redis-cli","GET",f"factoryops:consumer:{action_id}")==consumed
    reject_before=int(sql("SELECT COUNT(*) FROM corrective_actions;"))
    request("http://127.0.0.1:8082/api/v1/agent/runs","POST",{"question":question,"thread_id":"live-reject","case_number":"CASE-001","part_number":"PART-001","batch_number":"BATCH-001"})
    rejected=request("http://127.0.0.1:8082/api/v1/agent/resume","POST",{"thread_id":"live-reject","approved":False,"actor":"quality.lead","reason":"not approved"})
    assert "action_result" in rejected, rejected
    assert rejected["action_result"]["status"]=="REJECTED"
    assert int(sql("SELECT COUNT(*) FROM corrective_actions;"))==reject_before
    risk=live_supplier_risk()
    dimensions=collection["config"]["params"]["vectors"]["size"]
    print(json.dumps({"status":"PASS","neo4j_nodes":nodes,"neo4j_relationships":rels,"qdrant_vectors":collection["points_count"],"embedding_dimension":dimensions,"action_id":action_id,"evidence":sorted(kinds),"supplier_risk":risk},ensure_ascii=False))

def live_supplier_risk():
    """Supplier-risk flow on live MySQL, Neo4j and Qdrant: assess, persist, approve once, deliver the event."""
    base="http://127.0.0.1:8082/api/v1/supplier-risk"
    body={"part_number":"PART-001","current_supplier":"SUP-001","case_number":"CASE-001"}
    assessed=request(f"{base}/assess","POST",body)
    status={e["source_type"]:e["status"] for e in assessed["evidence"]}
    assert status=={"STRUCTURED":"AVAILABLE","GRAPH":"AVAILABLE","DOCUMENT":"AVAILABLE"},(status,assessed["warnings"])
    assert assessed["analysis_status"]=="READY_FOR_REVIEW",assessed["warnings"]
    assert [r["supplierCode"] for r in assessed["recommendations"]]==["SUP-002"]
    sup2=next(r for r in assessed["assessments"] if r["supplierCode"]=="SUP-002")
    assert sup2["graph_penalty"]==15 and sup2["risk_score"]==29.69, sup2
    assert assessed["narrative"]["summary"]
    key=f"live-{uuid.uuid4().hex[:12]}"
    review=request(f"{base}/reviews","POST",{"request_key":key,"request":body})
    assert review["status"]=="PENDING_REVIEW", review["status"]
    assert request(f"{base}/reviews","POST",{"request_key":key,"request":body})["id"]==review["id"]
    decision={"version":review["version"],"approved":True,"supplier_code":"SUP-002","actor":"procurement.lead","reason":"live verification"}
    approved=request(f"{base}/reviews/{review['id']}/decision","POST",decision)
    assert approved["status"]=="APPROVED" and approved["action_id"], approved
    assert request(f"{base}/reviews/{review['id']}/decision","POST",decision)["action_id"]==approved["action_id"]
    correlation=f"risk-review-{review['id']}"
    assert int(sql(f"SELECT COUNT(*) FROM corrective_actions WHERE correlation_id='{correlation}';"))==1
    assert int(sql(f"SELECT COUNT(*) FROM outbox_events WHERE correlation_id='{correlation}';"))==1
    wait_for(lambda: compose("exec","-T","redis","redis-cli","EXISTS",f"factoryops:consumer:{approved['action_id']}")=="1","risk review event consumed")
    return {"review_id":review["id"],"action_id":approved["action_id"],"recommendations":["SUP-002"],"narrative_source":assessed["narrative"]["source"],
            "document_matches":[m["id"] for e in assessed["evidence"] if e["source_type"]=="DOCUMENT" for m in e["payload"]["matches"]]}
if __name__=="__main__": main()
