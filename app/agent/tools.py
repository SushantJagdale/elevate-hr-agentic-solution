"""ADK Tool Definitions with Integrated Guardrail Validation."""

from ..services.policy_knowledge_service import policy_service
from ..connectors.workweek_connector import workweek_connector
from ..connectors.service_immediately_connector import service_immediately_connector
from ..guardrails.workweek_guard import workweek_guard
from ..guardrails.service_immediately_guard import service_immediately_guard
from ..guardrails.rag_guard import rag_guard


def search_policy_handbook(query: str) -> dict:
    """Search official Altostrat Singapore Employee Policy Handbook and Guidelines.

    Args:
        query: Natural language query regarding leave, benefits, expenses, conduct, equipment, or HR policies.

    Returns:
        Dictionary containing matched policy sections, citations, attribution score, and grounding status.
    """
    res = policy_service.search(query, top_k=4)
    is_valid, reason = rag_guard.evaluate_grounding(res)

    chunks_data = [
        {
            "document_name": c.document_name,
            "section_title": c.section_title,
            "chunk_text": c.chunk_text,
            "deep_link_url": c.deep_link_url,
        }
        for c in res.chunks
    ]

    return {
        "query": query,
        "attribution_score": res.attribution_score,
        "is_grounded": is_valid,
        "policy_chunks": chunks_data,
        "citations": res.source_citations,
        "guardrail_status": "APPROVED" if is_valid else "REFUSAL_REQUIRED",
    }


def get_leave_balances(employee_id: str) -> dict:
    """Fetch current accrued, used, and remaining leave balances from WorkWeek HCM.

    Args:
        employee_id: Employee identifier (e.g., 'E1209').

    Returns:
        Dictionary with vacation, sick leave, bereavement, carers, and TOIL balances.
    """
    return workweek_connector.get_leave_balances(employee_id)


def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    requested_days: float,
    notes: str = "",
) -> dict:
    """Submit a formal leave request to WorkWeek HCM after verifying balance and dates.

    Args:
        employee_id: Employee identifier (e.g., 'E1209').
        leave_type: Type of leave ('Vacation', 'Sick', 'Bereavement', 'Carers', 'TOIL', 'Unpaid').
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        requested_days: Total working days requested (e.g., 2.0).
        notes: Optional comments for the manager.

    Returns:
        Confirmation details with Request ID and submission status, or validation error.
    """
    # 1. Validate date chronology
    valid_dates, date_msg = workweek_guard.validate_date_chronology(start_date, end_date)
    if not valid_dates:
        return {"status": "validation_error", "error": date_msg}

    # 2. Validate leave balance
    bal_res = workweek_connector.get_leave_balances(employee_id)
    if bal_res.get("status") == "success" and bal_res.get("data"):
        valid_bal, bal_msg = workweek_guard.validate_leave_balance(
            leave_type, requested_days, bal_res["data"]
        )
        if not valid_bal:
            return {"status": "validation_error", "error": bal_msg}

    # 3. Submit request
    return workweek_connector.submit_leave_request(
        employee_id=employee_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        requested_days=requested_days,
        notes=notes,
    )


def get_employee_profile(employee_id: str) -> dict:
    """Fetch employee profile details including work location type, department, and contact info.

    Args:
        employee_id: Employee identifier (e.g., 'E1209').

    Returns:
        Employee profile dictionary.
    """
    return workweek_connector.get_employee_profile(employee_id)


def update_employee_contact(
    employee_id: str, phone: str = "", address: str = ""
) -> dict:
    """Update employee phone number or residential address in WorkWeek HCM.

    Args:
        employee_id: Employee identifier (e.g., 'E1209').
        phone: Optional updated phone number.
        address: Optional updated address.

    Returns:
        Updated profile details.
    """
    return workweek_connector.update_contact_info(
        employee_id=employee_id,
        phone=phone if phone else None,
        address=address if address else None,
    )


def get_support_ticket(ticket_number: str) -> dict:
    """Fetch status and details of a ServiceImmediately support ticket.

    Args:
        ticket_number: Ticket identifier (e.g., 'INC0048100').

    Returns:
        Ticket details including state, priority, description, and comments.
    """
    return service_immediately_connector.get_ticket(ticket_number)


def list_my_tickets(employee_id: str, state: str = "") -> dict:
    """List recent IT or HR support tickets created by the employee.

    Args:
        employee_id: Employee identifier (e.g., 'E1209').
        state: Optional filter for state (e.g., 'New', 'In Progress', 'Resolved').

    Returns:
        List of incident tickets.
    """
    return service_immediately_connector.list_user_tickets(
        caller_id=employee_id, state=state if state else None
    )


def create_support_ticket(
    category: str,
    priority: int,
    short_description: str,
    description: str = "",
    employee_id: str = "E1209",
) -> dict:
    """Create a new IT or HRSD incident ticket in ServiceImmediately after deduplication check.

    Args:
        category: Incident category ('Network/VPN', 'Hardware', 'Software', 'Security/Access', 'Facilities', 'HRSD / Employee Relations').
        priority: Priority level: 1 (Critical), 2 (High), 3 (Moderate), 4 (Low).
        short_description: Concise summary of the issue.
        description: Optional detailed explanation.
        employee_id: Employee ID filing the ticket.

    Returns:
        Created ticket details (e.g. INC0049281) or duplicate warning.
    """
    # 1. Guardrail validation
    valid_params, p_msg = service_immediately_guard.validate_ticket_parameters(
        category=category, priority=priority, short_description=short_description
    )
    if not valid_params:
        return {"status": "validation_error", "error": p_msg}

    # 2. Check for duplicate ticket within 24h
    has_dup, dup_ticket, dup_msg = service_immediately_guard.check_deduplication(
        caller_id=employee_id, category=category, short_description=short_description
    )
    if has_dup and dup_ticket:
        return {
            "status": "duplicate_prevented",
            "message": (
                f"A similar active ticket ({dup_ticket['number']}: '{dup_ticket['short_description']}') "
                f"is already in state '{dup_ticket['state']}'. To avoid duplicate queues, please add a comment to that ticket."
            ),
            "existing_ticket": dup_ticket,
        }

    # 3. Create ticket
    return service_immediately_connector.create_incident(
        caller_id=employee_id,
        category=category,
        priority=priority,
        short_description=short_description,
        description=description,
    )


def add_ticket_comment(ticket_number: str, comment: str, employee_id: str = "E1209") -> dict:
    """Add a note or update comment to an existing support ticket.

    Args:
        ticket_number: Ticket identifier (e.g., 'INC0048100').
        comment: Note text to append.
        employee_id: Employee ID adding the comment.

    Returns:
        Status confirmation.
    """
    return service_immediately_connector.add_comment(
        ticket_number=ticket_number, commenter_id=employee_id, comment=comment
    )


# --- Cross-System Orchestration Tools (UC-2.1, UC-2.2, UC-2.3) ---


def order_hardware_equipment(
    item_name: str, employee_id: str = "E1209", justification: str = ""
) -> dict:
    """Cross-System Workflow (UC-2.1): Verify remote work eligibility and order equipment.

    Args:
        item_name: Hardware requested (e.g., '27-inch 4K Monitor', 'Ergonomic Chair').
        employee_id: Employee identifier.
        justification: Business reason for the procurement.

    Returns:
        Combined workflow result with eligibility check and hardware request ID.
    """
    # Step 1: Check WorkWeek profile for Remote/Hybrid status
    prof_res = workweek_connector.get_employee_profile(employee_id)
    if prof_res.get("status") != "success" or not prof_res.get("data"):
        return {"status": "error", "error": f"Could not verify profile for {employee_id}"}

    profile = prof_res["data"]
    loc_type = profile.get("work_location_type", "OnSite")
    shipping_addr = profile.get("address", "")

    if loc_type not in ["Remote", "Hybrid"]:
        return {
            "status": "ineligible",
            "message": f"Employee {employee_id} has work location type '{loc_type}'. Home office equipment is reserved for Remote or Hybrid staff.",
        }

    # Step 2: Create hardware procurement ticket
    req_res = service_immediately_connector.create_hardware_request(
        recipient_id=employee_id,
        item_name=item_name,
        shipping_address=shipping_addr,
        justification=justification or f"Remote Work Setup for {profile.get('name')}",
    )

    return {
        "status": "success",
        "work_location_type": loc_type,
        "shipping_address": shipping_addr,
        "hardware_request": req_res.get("data"),
        "message": f"Equipment request for '{item_name}' successfully created! Reference: {req_res.get('data', {}).get('request_id')}.",
    }


def file_medical_leave_with_it_routing(
    employee_id: str,
    start_date: str,
    end_date: str,
    requested_days: float,
    notes: str = "",
) -> dict:
    """Cross-System Workflow (UC-2.2): Submit medical leave in WorkWeek and open IT routing ticket.

    Args:
        employee_id: Employee identifier.
        start_date: Medical leave start date (YYYY-MM-DD).
        end_date: Medical leave end date (YYYY-MM-DD).
        requested_days: Total sick days requested.
        notes: Doctor's note or medical details.

    Returns:
        Combined confirmation with WorkWeek leave ID and ServiceImmediately HRSD ticket ID.
    """
    # Step 1: Submit sick leave in WorkWeek
    ww_res = submit_leave_request(
        employee_id=employee_id,
        leave_type="Sick",
        start_date=start_date,
        end_date=end_date,
        requested_days=requested_days,
        notes=notes or "Medical Leave",
    )
    if ww_res.get("status") != "success":
        return {"status": "error", "step": "WorkWeek_Submission", "error": ww_res.get("error")}

    leave_id = ww_res.get("data", {}).get("request_id")

    # Step 2: Create IT routing & HRSD ticket in ServiceImmediately
    sm_res = service_immediately_connector.create_incident(
        caller_id=employee_id,
        category="HRSD / Employee Relations",
        priority=3,
        short_description=f"Medical Leave Notification & Out-of-Office Routing ({leave_id})",
        description=f"Automated HRSD notification: Employee {employee_id} on medical leave from {start_date} to {end_date} ({requested_days} days). WorkWeek Ref: {leave_id}.",
        assigned_group="HR-Tier2-Ops",
    )

    return {
        "status": "success",
        "workweek_leave_id": leave_id,
        "hrsd_ticket": sm_res.get("data"),
        "message": f"Medical leave ({requested_days} days) logged in WorkWeek ({leave_id}) and HRSD coverage ticket ({sm_res.get('data', {}).get('number')}) opened.",
    }


def process_relocation_request(
    employee_id: str, new_address: str, new_phone: str = ""
) -> dict:
    """Cross-System Workflow (UC-2.3): Update address in WorkWeek and create Facilities badge ticket.

    Args:
        employee_id: Employee identifier.
        new_address: New residential address.
        new_phone: Optional new contact number.

    Returns:
        Combined result with updated profile and Facilities ticket ID.
    """
    # Step 1: Update contact in WorkWeek
    ww_res = workweek_connector.update_contact_info(
        employee_id=employee_id, address=new_address, phone=new_phone or None
    )
    if ww_res.get("status") != "success":
        return {"status": "error", "step": "WorkWeek_Update", "error": ww_res.get("error")}

    # Step 2: Create Facilities badge & relocation support ticket
    sm_res = service_immediately_connector.create_incident(
        caller_id=employee_id,
        category="Facilities",
        priority=3,
        short_description=f"Relocation & Badge Update for {employee_id}",
        description=f"Employee relocated to new address: {new_address}. Please update local site badge access and regional tax profile.",
        assigned_group="Facilities-Ops",
    )

    return {
        "status": "success",
        "updated_profile": ww_res.get("data"),
        "facilities_ticket": sm_res.get("data"),
        "message": f"Address updated in WorkWeek and Facilities badge request ({sm_res.get('data', {}).get('number')}) created.",
    }


ALL_TOOLS = [
    search_policy_handbook,
    get_leave_balances,
    submit_leave_request,
    get_employee_profile,
    update_employee_contact,
    get_support_ticket,
    list_my_tickets,
    create_support_ticket,
    add_ticket_comment,
    order_hardware_equipment,
    file_medical_leave_with_it_routing,
    process_relocation_request,
]
