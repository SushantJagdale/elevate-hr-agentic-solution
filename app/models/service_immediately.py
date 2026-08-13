"""ServiceImmediately ITSM/HRSD Data Models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TicketPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MODERATE = 3
    LOW = 4


class TicketState(str, Enum):
    NEW = "1 - New"
    IN_PROGRESS = "2 - In Progress"
    ON_HOLD = "3 - On Hold"
    RESOLVED = "6 - Resolved"
    CLOSED = "7 - Closed"
    CANCELLED = "8 - Cancelled"


class IncidentTicket(BaseModel):
    sys_id: str
    number: str  # e.g., INC0049281
    caller_id: str  # e.g., E1209
    category: str   # e.g., "Network/VPN", "Software", "Hardware", "HRSD / Employee Relations"
    priority: TicketPriority = TicketPriority.MODERATE
    state: TicketState = TicketState.NEW
    short_description: str
    description: str = ""
    assigned_group: str = "IT-Helpdesk"
    assignee: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    comments: list[str] = Field(default_factory=list)


class HardwareRequest(BaseModel):
    request_id: str  # e.g., REQ0094120
    recipient_id: str  # e.g., E1209
    item_name: str     # e.g., "27-inch 4K Monitor"
    shipping_address: str
    justification: str = ""
    status: str = "In-Fulfillment"  # Submitted, Approved, In-Fulfillment, Shipped, Delivered
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class TicketComment(BaseModel):
    ticket_id: str
    commenter_id: str
    comment: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
