from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    id: str
    status: Literal["AVAILABLE","EMPTY","UNAVAILABLE"]
    source_type: Literal["STRUCTURED","GRAPH","DOCUMENT"]
    source_id: str
    claim: str
    payload: dict[str, Any] = Field(default_factory=dict)

class AgentState(TypedDict, total=False):
    question: str; intent: str; case_number: str; part_number: str; batch_number: str; supplier_code: str | None
    evidence: list[dict[str, Any]]; answer: str; proposed_action: dict[str, Any]
    approval: dict[str, Any]; action_result: dict[str, Any]; correlation_id: str
    recommendation: dict[str, Any]; answer_source: Literal["llm","template"]; llm_fallback_reason: str | None

class RunRequest(BaseModel):
    question: str
    thread_id: str
    case_number: str = "CASE-001"
    part_number: str = "PART-001"
    batch_number: str = "BATCH-001"
    supplier_code: str | None = Field(default=None,max_length=50,description="Defaults to the supplier linked to the batch")

class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool
    actor: str = "quality.lead"
    reason: str = ""
