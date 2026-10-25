"""LLM access for narrative generation only.

The model never decides whether a write happens or which supplier is recommended:
its output is schema-validated, checked against the evidence it was given, and any
failure falls back to deterministic templates.
"""
import json
import logging
import re
from typing import Protocol, TypeVar
import httpx
from pydantic import BaseModel, Field, ValidationError
from .config import settings

log=logging.getLogger("supplyguard.llm")
T=TypeVar("T",bound=BaseModel)

class LlmProvider(Protocol):
    def complete(self,prompt:str)->str: ...

class OpenAICompatibleProvider:
    def __init__(self,client:httpx.Client|None=None):
        self.client=client or httpx.Client(timeout=settings.llm_timeout_seconds)
    def complete(self,prompt:str)->str:
        body={"model":settings.openai_model,"temperature":0,
              "messages":[{"role":"system","content":"You are a manufacturing quality analyst. Reply with one JSON object only, no prose, no code fences."},{"role":"user","content":prompt}]}
        if settings.llm_json_mode: body["response_format"]={"type":"json_object"}
        response=self.client.post(f"{settings.openai_base_url.rstrip('/')}/chat/completions",headers={"Authorization":f"Bearer {settings.openai_api_key}"},json=body)
        response.raise_for_status(); return response.json()["choices"][0]["message"]["content"]

def provider()->LlmProvider|None:
    """Return the configured provider, or None so callers use their deterministic template."""
    if settings.llm_provider!="openai-compatible": return None
    if not settings.openai_base_url or not settings.openai_api_key:
        log.warning("llm_provider=openai-compatible but base URL or API key is missing; using templates")
        return None
    return OpenAICompatibleProvider()

class ContainmentRecommendation(BaseModel):
    conclusion: str = Field(min_length=1,max_length=1000)
    evidence_ids: list[str] = Field(min_length=1,max_length=20)
    actions: list[str] = Field(min_length=1,max_length=8)
    confidence: float = Field(ge=0,le=1)

class RiskNarrative(BaseModel):
    summary: str = Field(min_length=1,max_length=1500)
    key_risks: list[str] = Field(default_factory=list,max_length=8)
    evidence_ids: list[str] = Field(default_factory=list,max_length=20)

def _json_object(text:str)->str:
    # Some OpenAI-compatible servers wrap JSON in ``` fences despite the instruction.
    fenced=re.search(r"```(?:json)?\s*(\{.*\})\s*```",text,re.S)
    return fenced.group(1) if fenced else text.strip()

def generate(llm:LlmProvider|None,prompt:str,schema:type[T],allowed_evidence:set[str])->tuple[T|None,str|None]:
    """Call the model and validate its output. Returns (result, None) or (None, failure reason)."""
    if llm is None: return None,"llm_not_configured"
    try: raw=llm.complete(prompt)
    except Exception as exc:
        log.warning("llm call failed: %s",exc); return None,"llm_call_failed"
    try: result=schema.model_validate(json.loads(_json_object(raw)))
    except (json.JSONDecodeError,ValidationError) as exc:
        log.warning("llm output rejected by schema: %s",exc); return None,"llm_output_invalid"
    unknown=set(result.evidence_ids)-allowed_evidence
    if unknown:
        log.warning("llm cited unknown evidence %s",sorted(unknown)); return None,"llm_cited_unknown_evidence"
    return result,None
