import pytest
from factoryops_agent.config import settings

@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    # A developer's .env may hold a real API key; unit tests must never call a paid model.
    monkeypatch.setattr(settings,"llm_provider","fake")
    monkeypatch.setattr(settings,"llm_json_mode",False)
