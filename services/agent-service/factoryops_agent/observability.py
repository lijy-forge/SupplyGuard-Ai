from contextlib import nullcontext
try:
    from langfuse import get_client
except ImportError:
    get_client=None

def trace(name:str, metadata:dict):
    if get_client is None: return nullcontext()
    try: return get_client().start_as_current_observation(name=name,as_type="span",metadata=metadata)
    except Exception: return nullcontext()
