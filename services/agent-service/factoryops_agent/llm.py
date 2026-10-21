from typing import Protocol
import httpx
from .config import settings
class LlmProvider(Protocol):
    def complete(self,prompt:str)->str: ...
class DeterministicProvider:
    def complete(self,prompt:str)->str: return "Evidence supports immediate containment; human approval is required before execution."
class OpenAICompatibleProvider:
    def complete(self,prompt:str)->str:
        response=httpx.post(f"{settings.openai_base_url.rstrip('/')}/chat/completions",headers={"Authorization":f"Bearer {settings.openai_api_key}"},json={"model":settings.openai_model,"messages":[{"role":"user","content":prompt}]},timeout=30)
        response.raise_for_status(); return response.json()["choices"][0]["message"]["content"]
def provider()->LlmProvider: return OpenAICompatibleProvider() if settings.llm_provider=="openai-compatible" else DeterministicProvider()
