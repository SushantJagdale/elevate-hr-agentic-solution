"""ServiceImmediately ITSM/HRSD Mock Sandbox Service."""

import uuid
from datetime import datetime, timedelta
from ..models.service_immediately import (
    IncidentTicket,
    HardwareRequest,
    TicketComment,
    TicketPriority,
    TicketState,
)


class ServiceImmediatelyService:
    """Simulates ServiceImmediately ITSM/HRSD REST API with stateful operations."""

    def __init__(self):
        self._incidents: dict[str, IncidentTicket] = {}
        self._hardware_requests: dict[str, HardwareRequest] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        """Seed sample IT and HRSD incidents."""
        # Initial ticket for E1209
        now = datetime.utcnow()
        inc1 = IncidentTicket(
            sys_id="inc_001_seed",
            number="INC0048100",
            caller_id="E1209",
            category="Software",
            priority=TicketPriority.MODERATE,
            state=TicketState.RESOLVED,
            short_description="IntelliJ License renewal",
            description="Employee requested renewal for IDE enterprise license.",
            assigned_group="IT-App-Support",
            assignee="Mike IT",
            created_at=(now - timedelta(days=5)).isoformat() + "Z",
            updated_at=(now - timedelta(days=4)).isoformat() + "Z",
            comments=["License renewed successfully via Okta."],
        )
        self._incidents[inc1.number] = inc1

    def get_ticket(self, ticket_number: str) -> IncidentTicket | None:
        """Fetch incident ticket by number (e.g. INC0048100)."""
        return self._incidents.get(ticket_number)

    def list_user_tickets(
        self, caller_id: str, state: str | None = None
    ) -> list[IncidentTicket]:
        """List tickets created by a specific user."""
        results = [t for t in self._incidents.values() if t.caller_id == caller_id]
        if state:
            results = [t for t in results if state.lower() in t.state.lower()]
        # Sort descending by creation date
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def check_duplicate_ticket(
        self, caller_id: str, category: str, keyword: str = "", window_hours: int = 24
    ) -> IncidentTicket | None:
        """Scan for duplicate tickets created within the window_hours."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=window_hours)

        for ticket in self._incidents.values():
            if ticket.caller_id != caller_id:
                continue
            # Ignore resolved/closed/cancelled tickets
            if ticket.state in [TicketState.RESOLVED, TicketState.CLOSED, TicketState.CANCELLED]:
                continue
            
            created_dt = datetime.fromisoformat(ticket.created_at.replace("Z", "+00:00")).replace(tzinfo=None)
            if created_dt >= cutoff:
                # Check category or keyword overlap
                if category.lower() in ticket.category.lower() or (
                    keyword and keyword.lower() in ticket.short_description.lower()
                ):
                    return ticket
        return None

    def create_incident(
        self,
        caller_id: str,
        category: str,
        priority: int | TicketPriority,
        short_description: str,
        description: str = "",
        assigned_group: str = "IT-Helpdesk",
    ) -> IncidentTicket:
        """Create a new incident ticket."""
        if isinstance(priority, int):
            try:
                priority = TicketPriority(priority)
            except ValueError:
                priority = TicketPriority.MODERATE

        ticket_count = len(self._incidents) + 49200
        number = f"INC00{ticket_count}"
        sys_id = f"sys_{uuid.uuid4().hex[:8]}"

        ticket = IncidentTicket(
            sys_id=sys_id,
            number=number,
            caller_id=caller_id,
            category=category,
            priority=priority,
            state=TicketState.NEW,
            short_description=short_description,
            description=description,
            assigned_group=assigned_group,
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z",
        )
        self._incidents[number] = ticket
        return ticket

    def create_hardware_request(
        self,
        recipient_id: str,
        item_name: str,
        shipping_address: str,
        justification: str = "",
    ) -> HardwareRequest:
        """Create an enterprise hardware procurement request."""
        req_count = len(self._hardware_requests) + 94100
        req_id = f"REQ00{req_count}"

        req = HardwareRequest(
            request_id=req_id,
            recipient_id=recipient_id,
            item_name=item_name,
            shipping_address=shipping_address,
            justification=justification,
            status="In-Fulfillment",
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        self._hardware_requests[req_id] = req
        return req

    def add_comment(self, ticket_number: str, commenter_id: str, comment: str) -> bool:
        """Add a comment to an existing ticket."""
        ticket = self._incidents.get(ticket_number)
        if not ticket:
            return False
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ticket.comments.append(f"[{timestamp}] ({commenter_id}): {comment}")
        ticket.updated_at = datetime.utcnow().isoformat() + "Z"
        return True


servicenow_db = ServiceImmediatelyService()
