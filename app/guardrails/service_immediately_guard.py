"""ServiceImmediately ITSM/HRSD Domain Guardrails."""

from typing import Tuple
from ..connectors.service_immediately_connector import (
    ServiceImmediatelyConnector,
    service_immediately_connector,
)


class ServiceImmediatelyGuardrail:
    """Deterministic validation firewall for ServiceImmediately actions."""

    VALID_CATEGORIES = [
        "Network/VPN",
        "Hardware",
        "Software",
        "Security/Access",
        "Facilities",
        "HRSD / Employee Relations",
        "General IT",
    ]

    def __init__(self, connector: ServiceImmediatelyConnector | None = None):
        self.connector = connector or service_immediately_connector

    def check_deduplication(
        self, caller_id: str, category: str, short_description: str, window_hours: int = 24
    ) -> Tuple[bool, dict | None, str]:
        """Check if an open ticket for the same issue was created in the last 24 hours."""
        res = self.connector.check_duplicate(
            caller_id=caller_id,
            category=category,
            keyword=short_description,
            window_hours=window_hours,
        )
        if res.get("status") == "duplicate_found" and res.get("data"):
            dup_ticket = res["data"]
            return (
                True,
                dup_ticket,
                f"Duplicate ticket detected ({dup_ticket['number']}: {dup_ticket['short_description']} - State: {dup_ticket['state']}).",
            )
        return False, None, "No duplicate tickets found."

    def validate_ticket_parameters(
        self, category: str, priority: int, short_description: str
    ) -> Tuple[bool, str]:
        """Validate category, priority (1-4), and description length."""
        if not short_description or len(short_description.strip()) < 5:
            return False, "Short description must be at least 5 characters long."

        if priority not in [1, 2, 3, 4]:
            return False, f"Invalid priority '{priority}'. Must be 1 (Critical), 2 (High), 3 (Moderate), or 4 (Low)."

        return True, "Ticket parameters validated."


service_immediately_guard = ServiceImmediatelyGuardrail()
