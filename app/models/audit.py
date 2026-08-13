"""BigQuery WORM Audit Event Models matching SDD Section 3.5.3."""

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class SafetyVerdict(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED_INJECTION = "BLOCKED_INJECTION"
    BLOCKED_SPII = "BLOCKED_SPII"
    BLOCKED_DOMAIN = "BLOCKED_DOMAIN"
    BLOCKED_UNAUTHORIZED_SCOPE = "BLOCKED_UNAUTHORIZED_SCOPE"


class ToolCallLog(BaseModel):
    tool_name: str
    target_endpoint: str
    execution_latency_ms: int
    http_status_code: int = 200
    parameters: dict | None = None
    response_summary: str | None = None


class AuditEventSchema(BaseModel):
    event_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    session_id: str
    user_id_hash: str
    prompt_safety_verdict: SafetyVerdict
    intent_category: str = "General"
    model_used: str = "gemini-2.5-flash"
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    grounding_attribution_score: float | None = None
    final_response_status: Literal["SUCCESS", "REFUSAL", "ERROR"] = "SUCCESS"
    acting_user_id: str | None = None
    error_message: str | None = None
