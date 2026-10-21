"""Run only against docker-compose.factoryops.yml on a real Docker daemon."""
import json, os, subprocess, time, urllib.request

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
    dimensions=collection["config"]["params"]["vectors"]["size"]
    print(json.dumps({"status":"PASS","neo4j_nodes":nodes,"neo4j_relationships":rels,"qdrant_vectors":collection["points_count"],"embedding_dimension":dimensions,"action_id":action_id,"evidence":sorted(kinds)},ensure_ascii=False))
if __name__=="__main__": main()
