"""Session State Models matching SDD Section 3.5.1."""

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class WorkLocationType(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "OnSite"


class UserContext(BaseModel):
    name: str
    email: str
    department: str
    role: str
    work_location_type: WorkLocationType = WorkLocationType.REMOTE
    manager_id: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    address: str | None = None


class ConversationTurn(BaseModel):
    turn_id: int
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    tool_calls: list[dict] | None = None


class ActiveTransaction(BaseModel):
    transaction_id: str
    target_system: Literal["WorkWeek", "ServiceImmediately", "CrossSystem"]
    status: Literal["INITIATED", "VALIDATED", "SUBMITTED", "FAILED", "ROLLED_BACK"]
    payload: dict | None = None
    details: str | None = None


class SessionStateSchema(BaseModel):
    session_id: str
    user_id: str = Field(pattern=r"^E[0-9]{4,8}$")
    user_context: UserContext
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    active_transaction: ActiveTransaction | None = None
