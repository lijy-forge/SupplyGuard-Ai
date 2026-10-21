"""Real Java/Python HTTP check; external graph/vector are not claimed as live."""
import subprocess,sys,time,os,json,socket,uuid
from pathlib import Path
import httpx
root=Path(__file__).resolve().parents[1]
(root/".tools").mkdir(exist_ok=True)
for port in (18081,18082):
    with socket.socket() as sock:sock.bind(("127.0.0.1",port))
processes=[]
token=uuid.uuid4().hex
db=root/".tools"/f"smoke-risk-{token}"
creation={"creationflags":getattr(subprocess,"CREATE_NO_WINDOW",0)}
log=open(root/".tools/smoke-java.log","w")
java_args=["java","-jar",str(root/"services/business-service/target/business-service-0.1.0.jar"),"--spring.profiles.active=risk-demo","--server.address=127.0.0.1","--server.port=18081",f"--spring.datasource.url=jdbc:h2:file:{db.as_posix()};MODE=MySQL;DATABASE_TO_LOWER=TRUE"]
def java():
    p=subprocess.Popen(java_args,stdout=log,stderr=log,**creation);processes.append(p);return p

def agent(mode):
    env={**os.environ,"FACTORYOPS_BUSINESS_URL":"http://127.0.0.1:18081/api/v1","FACTORYOPS_RISK_EVIDENCE_MODE":mode}
    p=subprocess.Popen([sys.executable,"-m","uvicorn","factoryops_agent.supplier_risk:app","--host","127.0.0.1","--port","18082"],cwd=root/"services/agent-service",env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**creation);processes.append(p);return p

def stop(p):
    p.terminate()
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:p.kill();p.wait()

def wait(client,port,path):
    for _ in range(120):
        try:
            if client.get(f"http://127.0.0.1:{port}{path}").status_code==200:return
        except httpx.HTTPError:pass
        time.sleep(.5)
    raise RuntimeError(f"service {port} did not start")

try:
    j=java();a=agent("structured")
    with httpx.Client(trust_env=False,timeout=15) as client:
        wait(client,18081,"/api/v1/health");wait(client,18082,"/openapi.json")
        business="http://127.0.0.1:18081/api/v1"
        api="http://127.0.0.1:18082/api/v1/supplier-risk"
        payload={"part_number":"PART-001","current_supplier":"SUP-001","case_number":"CASE-001"}
        candidates=client.get(business+"/supplier-risk/candidates",params={"partNumber":"PART-001"})
        assert candidates.status_code==200 and len(candidates.json())==4
        response=client.post(api+"/assess",json=payload);assert response.status_code==200,response.text
        data=response.json();assert [r["supplierCode"] for r in data["recommendations"]]==["SUP-002"]
        assert data["evidence"][0]["status"]=="AVAILABLE",data
        assert len(data["evidence"][0]["payload"]["vehicles"])==2
        assert data["analysis_status"]=="NEEDS_EVIDENCE"
        assert client.get(business+"/quality-cases/CASE-001").status_code==200
        assert client.post(api+"/assess",json={**payload,"part_number":"UNKNOWN"}).status_code==404
        body={"request_key":token,"request":payload}
        saved=client.post(api+"/reviews",json=body);assert saved.status_code==200,saved.text
        review=saved.json();review_id=review["id"]
        assert review["status"]=="NEEDS_EVIDENCE"
        repeated=client.post(api+"/reviews",json=body);assert repeated.json()["id"]==review_id
        decision={"version":0,"approved":True,"supplier_code":"SUP-002","actor":"smoke.reviewer","reason":"test"}
        assert client.post(api+f"/reviews/{review_id}/decision",json=decision).status_code==409
        decision["approved"]=False
        rejected=client.post(api+f"/reviews/{review_id}/decision",json=decision)
        assert rejected.status_code==200 and rejected.json()["status"]=="REJECTED",rejected.text
        assert client.post(api+f"/reviews/{review_id}/decision",json=decision).json()["version"]==1
        assert len(client.get(api+f"/reviews/{review_id}/audit").json())==2
        # Restart both processes; recover the same snapshot and decision from a file database.
        stop(a);stop(j);j=java();a=agent("demo")
        wait(client,18081,"/api/v1/health");wait(client,18082,"/openapi.json")
        restored=client.get(api+f"/reviews/{review_id}")
        assert restored.status_code==200 and restored.json()["status"]=="REJECTED"
        demo=client.post(api+"/assess",json=payload).json()
        assert demo["analysis_status"]=="NEEDS_EVIDENCE"
        assert demo["assessments"][1]["graph_penalty"]==15
        assert [e["status"] for e in demo["evidence"]]==["AVAILABLE","DEMO","DEMO"]
        print(json.dumps({"status":"PASS","candidates":4,"quality_case_read":200,"structured_evidence":"AVAILABLE","missing_live_evidence_approval":409,"review_retry":"idempotent","rejection":"persisted","restart_recovery":"PASS","demo_upstream_penalty":15,"live_neo4j_qdrant":"NOT_TESTED"}))
finally:
    for p in processes:
        if p.poll() is None:stop(p)
    log.close()
    # Delete only this invocation's uniquely named temporary DB files.
    for suffix in (".mv.db",".trace.db",".lock.db"):
        path=Path(str(db)+suffix)
        if path.exists():path.unlink()
