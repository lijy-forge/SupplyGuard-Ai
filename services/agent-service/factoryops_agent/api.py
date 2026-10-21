from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from langgraph.types import Command
from redis import Redis
from .graph import build_graph, redis_checkpointer
from .models import RunRequest, ResumeRequest
from .config import settings
import json

@asynccontextmanager
async def lifespan(app):
    # Redis is a required dependency in Compose: do not silently substitute an
    # in-memory saver, which would make an interrupted approval unrecoverable
    # after an agent-service restart.
    app.state.graph=build_graph(redis_checkpointer()); yield

app=FastAPI(title="FactoryOps Agent Service",version="0.1.0",lifespan=lifespan)
def config(thread_id): return {"configurable":{"thread_id":thread_id}}
def input_key(thread_id): return f"factoryops:run-input:{thread_id}"
def save_input(request:RunRequest):
    try: Redis.from_url(settings.redis_url,decode_responses=True).set(input_key(request.thread_id),request.model_dump_json())
    except Exception: pass
def load_input(thread_id):
    try:
        value=Redis.from_url(settings.redis_url,decode_responses=True).get(input_key(thread_id))
        return json.loads(value) if value else None
    except Exception: return None
@app.get("/health")
def health(): return {"status":"UP","service":"agent-service"}
@app.post("/api/v1/agent/runs")
def run(r:RunRequest):
    save_input(r)
    return app.state.graph.invoke(r.model_dump(),config(r.thread_id))
@app.post("/api/v1/agent/resume")
def resume(r:ResumeRequest):
    return app.state.graph.invoke(Command(resume={"approved":r.approved,"actor":r.actor,"reason":r.reason}),config(r.thread_id))
@app.get("/api/v1/agent/runs/{thread_id}")
def state(thread_id:str):
    snapshot=app.state.graph.get_state(config(thread_id))
    if not snapshot.values: raise HTTPException(404,"thread not found")
    return {"values":snapshot.values,"next":snapshot.next,"interrupts":[i.value for task in snapshot.tasks for i in task.interrupts]}

from .supplier_risk import router as supplier_risk_router
app.include_router(supplier_risk_router)
