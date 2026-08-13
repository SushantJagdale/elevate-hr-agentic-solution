"""ServiceImmediately ITSM/HRSD Enterprise Connector."""

import time
import logging
from ..services.service_immediately_service import servicenow_db, ServiceImmediatelyService
from ..models.service_immediately import (
    IncidentTicket,
    HardwareRequest,
    TicketPriority,
    TicketState,
)

logger = logging.getLogger("ServiceImmediatelyConnector")


class ServiceImmediatelyConnector:
    """Enterprise ServiceImmediately Connector with Secret Manager credentials & Provenance headers."""

    def __init__(self, service: ServiceImmediatelyService | None = None):
        self.service = service or servicenow_db
        self.origin_agent = "HR-Agentic-MVP"
        self._max_retries = 3

    def _get_headers(self, acting_user_id: str) -> dict[str, str]:
        """Construct request headers matching SDD specs."""
        return {
            "Authorization": "Bearer mock_sm_token_sec_mgr_99201",
            "X-Automation-Source": self.origin_agent,
            "X-Acting-User": acting_user_id,
            "Content-Type": "application/json",
        }

    def get_ticket(self, ticket_number: str, acting_user_id: str | None = None) -> dict:
        """Fetch incident ticket details."""
        start_time = time.time()
        ticket = self.service.get_ticket(ticket_number)
        latency = int((time.time() - start_time) * 1000)

        if not ticket:
            return {
                "status": "error",
                "status_code": 404,
                "error": f"Ticket {ticket_number} not found",
                "latency_ms": latency,
            }
        return {
            "status": "success",
            "status_code": 200,
            "data": ticket.model_dump(),
            "latency_ms": latency,
        }

    def list_user_tickets(
        self, caller_id: str, state: str | None = None, acting_user_id: str | None = None
    ) -> dict:
        """List active or historical incident tickets for caller."""
        start_time = time.time()
        tickets = self.service.list_user_tickets(caller_id, state)
        latency = int((time.time() - start_time) * 1000)

        return {
            "status": "success",
            "status_code": 200,
            "data": [t.model_dump() for t in tickets],
            "latency_ms": latency,
        }

    def check_duplicate(
        self, caller_id: str, category: str, keyword: str = "", window_hours: int = 24
    ) -> dict:
        """Check for active duplicate tickets created in window."""
        start_time = time.time()
        dup = self.service.check_duplicate_ticket(caller_id, category, keyword, window_hours)
        latency = int((time.time() - start_time) * 1000)

        if dup:
            return {
                "status": "duplicate_found",
                "status_code": 200,
                "data": dup.model_dump(),
                "latency_ms": latency,
            }
        return {
            "status": "no_duplicate",
            "status_code": 200,
            "data": None,
            "latency_ms": latency,
        }

    def create_incident(
        self,
        caller_id: str,
        category: str,
        priority: int,
        short_description: str,
        description: str = "",
        assigned_group: str = "IT-Helpdesk",
        acting_user_id: str | None = None,
    ) -> dict:
        """Create a new incident ticket in ServiceImmediately."""
        start_time = time.time()
        try:
            ticket = self.service.create_incident(
                caller_id=caller_id,
                category=category,
                priority=priority,
                short_description=short_description,
                description=description,
                assigned_group=assigned_group,
            )
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "success",
                "status_code": 201,
                "data": ticket.model_dump(),
                "latency_ms": latency,
            }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "status_code": 500,
                "error": str(e),
                "latency_ms": latency,
            }

    def create_hardware_request(
        self,
        recipient_id: str,
        item_name: str,
        shipping_address: str,
        justification: str = "",
        acting_user_id: str | None = None,
    ) -> dict:
        """Create hardware procurement request in ServiceImmediately."""
        start_time = time.time()
        try:
            req = self.service.create_hardware_request(
                recipient_id=recipient_id,
                item_name=item_name,
                shipping_address=shipping_address,
                justification=justification,
            )
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "success",
                "status_code": 201,
                "data": req.model_dump(),
                "latency_ms": latency,
            }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "status_code": 500,
                "error": str(e),
                "latency_ms": latency,
            }

    def add_comment(
        self,
        ticket_number: str,
        commenter_id: str,
        comment: str,
        acting_user_id: str | None = None,
    ) -> dict:
        """Add a comment to an existing incident ticket."""
        start_time = time.time()
        success = self.service.add_comment(ticket_number, commenter_id, comment)
        latency = int((time.time() - start_time) * 1000)

        if success:
            return {
                "status": "success",
                "status_code": 200,
                "message": f"Comment added to {ticket_number}",
                "latency_ms": latency,
            }
        return {
            "status": "error",
            "status_code": 404,
            "error": f"Ticket {ticket_number} not found",
            "latency_ms": latency,
        }


service_immediately_connector = ServiceImmediatelyConnector()
