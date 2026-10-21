from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    source_type: Literal["STRUCTURED","GRAPH","DOCUMENT"]
    source_id: str
    claim: str
    payload: dict[str, Any] = Field(default_factory=dict)

class AgentState(TypedDict, total=False):
    question: str; intent: str; case_number: str; part_number: str; batch_number: str
    evidence: list[dict[str, Any]]; answer: str; proposed_action: dict[str, Any]
    approval: dict[str, Any]; action_result: dict[str, Any]; correlation_id: str

class RunRequest(BaseModel):
    question: str
    thread_id: str
    case_number: str = "CASE-001"
    part_number: str = "PART-001"
    batch_number: str = "BATCH-001"

class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool
    actor: str = "quality.lead"
    reason: str = ""
