"""Per-node tracing: one structured log line per node, mirrored to Langfuse when configured.

Tracing must never change workflow behaviour, so every exporter failure is swallowed and
node exceptions (including LangGraph interrupts) are re-raised untouched.
"""
import json
import logging
import os
import time
from contextlib import nullcontext
from langgraph.errors import GraphInterrupt
try:
    from langfuse import get_client
except ImportError:
    get_client=None

log=logging.getLogger("supplyguard.trace")
PREVIEW_CHARS=2000

def configure_logging(level=logging.INFO):
    """Uvicorn configures only its own loggers; without this, INFO trace lines are silently dropped."""
    root=logging.getLogger("supplyguard")
    if not root.handlers:
        handler=logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root.addHandler(handler)
    root.setLevel(level)

def langfuse_client():
    if get_client is None or not os.getenv("LANGFUSE_PUBLIC_KEY"): return None
    try: return get_client()
    except Exception: return None

def preview(value):
    text=json.dumps(value,default=str,ensure_ascii=False)
    return text if len(text)<=PREVIEW_CHARS else text[:PREVIEW_CHARS]+f"...(+{len(text)-PREVIEW_CHARS} chars)"

def trace(name:str, metadata:dict):
    client=langfuse_client()
    if client is None: return nullcontext()
    try: return client.start_as_current_observation(name=name,as_type="span",metadata=metadata)
    except Exception: return nullcontext()

def export(record):
    client=langfuse_client()
    if client is None: return
    try:
        span=client.start_observation(name=record["span"],as_type="span",input=record["input"],metadata={k:record[k] for k in ("thread_id","status","duration_ms","error")})
        span.update(output=record["output"]); span.end()
    except Exception:
        log.debug("langfuse export failed",exc_info=True)

def traced(workflow:str, node:str, fn):
    """Wrap a LangGraph node so its input, output, status and duration are recorded."""
    def wrapper(state, config=None):
        start=time.perf_counter(); status="ok"; output=None; error=None
        try:
            output=fn(state); return output
        except GraphInterrupt:
            status="interrupted"; raise
        except Exception as exc:
            status="error"; error=f"{type(exc).__name__}: {exc}"; raise
        finally:
            record={"span":f"{workflow}.{node}","thread_id":((config or {}).get("configurable") or {}).get("thread_id"),
                    "status":status,"duration_ms":round((time.perf_counter()-start)*1000,2),"error":error,
                    "input":preview(state),"output":preview(output) if output is not None else None}
            try: log.info(json.dumps(record,ensure_ascii=False))
            except Exception: pass
            export(record)
    wrapper.__name__=f"{workflow}_{node}"
    return wrapper
