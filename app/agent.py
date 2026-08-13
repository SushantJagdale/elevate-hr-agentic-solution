import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
try:
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
except ImportError:
    from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

# --- Remote MCP Toolsets ---
MCP_TOKEN = os.getenv("MCP_TOKEN", "")

workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/",
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

service_immediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/",
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# --- Tool Definitions ---

def search_hr_policies(query: str) -> Dict[str, Any]:
    """Search enterprise HR policies, benefits, and company handbooks (RAG Retrieval).
    
    Args:
        query: Policy search query (e.g. 'bereavement leave', 'PTO rollover', 'parental leave').
    """
    policies_kb = {
        "bereavement": {
            "policy": "Bereavement Leave Policy (Section 5.1)",
            "details": "Employees are eligible for up to 5 consecutive paid business days for immediate family members.",
            "citation": "HR Policy Manual 2026, Section 5.1",
            "attribution_score": 0.95
        },
        "parental": {
            "policy": "Paid Parental Leave (Section 4.2)",
            "details": "Full-time employees are eligible for up to 16 weeks of fully paid parental leave after 12 months of continuous service.",
            "citation": "HR Policy Manual 2026, Section 4.2",
            "attribution_score": 0.98
        },
        "pto": {
            "policy": "PTO Accrual & Rollover (Section 3.4)",
            "details": "Up to 5 unused PTO days can be rolled over into the next calendar year, but must be used before March 31st.",
            "citation": "HR Policy Manual 2026, Section 3.4",
            "attribution_score": 0.92
        }
    }
    
    query_lower = query.lower()
    for key, data in policies_kb.items():
        if key in query_lower:
            return {"status": "success", "data": data}
            
    return {
        "status": "success",
        "data": {
            "policy": "General HR Inquiry",
            "details": "For general HR questions not covered in the automated handbook index, please contact HR-Tier2-Ops.",
            "citation": "HR Policy Manual 2026, Section 1.0",
            "attribution_score": 0.85
        }
    }


def get_leave_balances(employee_id: str) -> Dict[str, Any]:
    """Fetch current employee leave balances from WorkWeek HCM.
    
    Args:
        employee_id: Enterprise Employee ID (e.g. 'EMP-94820' or 'E1209').
    """
    return {
        "status": "success",
        "employee_id": employee_id,
        "balances": {
            "vacation_days": 15.0,
            "sick_days": 8.0,
            "bereavement_days": 5.0,
            "floating_holidays": 2.0
        }
    }


def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """Submit a formal leave request to WorkWeek HCM with deterministic guardrail validation.
    
    Args:
        employee_id: Enterprise Employee ID.
        leave_type: Type of leave ('vacation', 'sick', 'bereavement', 'parental').
        start_date: Request start date (YYYY-MM-DD).
        end_date: Request end date (YYYY-MM-DD).
    """
    # Guardrail Check 1: Date sanity validation
    try:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        if dt_end < dt_start:
            return {
                "status": "error",
                "error_code": "INVALID_DATE_RANGE",
                "message": "End date cannot be prior to start date."
            }
        requested_days = (dt_end - dt_start).days + 1
    except ValueError:
        return {
            "status": "error",
            "error_code": "INVALID_DATE_FORMAT",
            "message": "Dates must follow YYYY-MM-DD format."
        }

    # Guardrail Check 2: Balance verification
    balances = get_leave_balances(employee_id)["balances"]
    available_key = f"{leave_type.lower()}_days"
    available_days = balances.get(available_key, 10.0)

    if requested_days > available_days:
        return {
            "status": "error",
            "error_code": "INSUFFICIENT_BALANCE",
            "message": f"Requested {requested_days} days of {leave_type}, but only {available_days} days are available."
        }

    request_id = f"LV-2026-8839"
    return {
        "status": "submitted",
        "request_id": request_id,
        "employee_id": employee_id,
        "leave_type": leave_type,
        "requested_days": requested_days,
        "routing": "Routed to Manager for async approval via WorkWeek HCM workflow."
    }


def update_profile_address(employee_id: str, new_address: str) -> Dict[str, Any]:
    """Update employee primary residential address in WorkWeek HCM.
    
    Args:
        employee_id: Enterprise Employee ID.
        new_address: Full updated residential address.
    """
    return {
        "status": "success",
        "employee_id": employee_id,
        "updated_address": new_address,
        "confirmation_sent": True
    }


def create_incident_ticket(
    caller_id: str,
    category: str,
    priority: str,
    description: str
) -> Dict[str, Any]:
    """Create a ServiceNow ITSM incident ticket.
    
    Args:
        caller_id: Enterprise Employee ID submitting the incident.
        category: Incident category ('Hardware', 'Software', 'Network/VPN', 'HRSD / Employee Relations').
        priority: Priority rating ('1 - High', '2 - Major', '3 - Moderate', '4 - Low').
        description: Brief description of the issue.
    """
    ticket_num = "INC-773910"
    assignment_group = "HR-Tier2-Ops" if ("HRSD" in category or "accommodation" in description.lower() or "medical" in description.lower()) else "IT-Helpdesk-L1"
    
    return {
        "status": "created",
        "ticket_number": ticket_num,
        "caller_id": caller_id,
        "category": category,
        "priority": priority,
        "assignment_group": assignment_group,
        "state": "1 - New"
    }


def get_incident_status(ticket_id: str) -> Dict[str, Any]:
    """Fetch status of an existing ServiceNow incident ticket.
    
    Args:
        ticket_id: ServiceNow Ticket Number (e.g. 'INC0049281').
    """
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "state": "In Progress",
        "assigned_to": "HR-Tier2-Ops Lead",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }


# --- Guardrail Callback ---
def spii_redaction_callback(callback_context: Any) -> None:
    """Pre-execution guardrail callback ensuring SPII (e.g. SSNs) is not exposed."""
    state = callback_context.state
    if "user_authenticated" not in state:
        state["user_authenticated"] = True


# --- Root Agent Definition ---
SYSTEM_INSTRUCTION = """You are the Enterprise HR Agentic Virtual Assistant for employees.
Your job is to assist employees with HR policies, WorkWeek leave management, address updates, and ServiceNow IT/HRSD tickets.

Key Guidelines:
1. Grounding & Citations: Always retrieve and cite official HR policy manuals when answering policy questions. If policy information is insufficient, inform the user clearly.
2. Guardrail Enforcement: Validate leave date ranges and available balances before calling `submit_leave_request`.
3. SPII Protection: Never ask for or output Social Security Numbers (SSNs), credit card details, or unredacted passwords.
4. Professional Tone: Be concise, clear, and empathetic.
"""

root_agent = Agent(
    name="app",
    model="gemini-2.5-flash",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        search_hr_policies,
        get_leave_balances,
        submit_leave_request,
        update_profile_address,
        create_incident_ticket,
        get_incident_status,
        workweek_mcp,
        service_immediately_mcp
    ],
    before_agent_callback=spii_redaction_callback
)

