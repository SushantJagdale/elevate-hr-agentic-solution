"""WorkWeek HCM Domain Guardrails Engine."""

from datetime import datetime, date
from typing import Tuple
from ..models.workweek import LeaveBalance, LeaveType


class WorkWeekGuardrail:
    """Deterministic validation firewall for WorkWeek actions."""

    @staticmethod
    def validate_user_authorization(session_user_id: str, target_user_id: str) -> Tuple[bool, str]:
        """Assert session user has permission to view/modify target record."""
        if not session_user_id or not target_user_id:
            return False, "Missing session or target user ID."
        
        # In MVP 1, users can operate only on their own account (unless manager override)
        if session_user_id != target_user_id and session_user_id not in ["E1001", "E1002", "E0900"]:
            return False, f"Unauthorized: User {session_user_id} cannot access or mutate records for {target_user_id}."
        return True, "User authorized."

    @staticmethod
    def validate_date_chronology(start_date_str: str, end_date_str: str) -> Tuple[bool, str]:
        """Validate date chronology (start_date <= end_date) and ISO formatting."""
        try:
            start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, f"Invalid start_date format '{start_date_str}'. Must be YYYY-MM-DD."

        try:
            end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, f"Invalid end_date format '{end_date_str}'. Must be YYYY-MM-DD."

        if start_d > end_d:
            return False, f"Chronological error: start_date ({start_date_str}) must be on or before end_date ({end_date_str})."

        return True, "Date chronology verified."

    @staticmethod
    def validate_leave_balance(
        leave_type_str: str, requested_days: float, balances: LeaveBalance | dict
    ) -> Tuple[bool, str]:
        """Validate requested days against accrued and remaining leave balances."""
        if requested_days <= 0:
            return False, f"Requested leave days must be greater than 0 (received {requested_days})."

        if isinstance(balances, dict):
            vac_rem = balances.get("vacation_remaining", 0.0)
            sick_rem = balances.get("sick_remaining", 0.0)
            bereave_rem = balances.get("bereavement_eligible_days", 5)
            carers_rem = balances.get("carers_eligible_days", 5)
            toil_rem = balances.get("toil_balance_days", 0.0)
        else:
            vac_rem = balances.vacation_remaining
            sick_rem = balances.sick_remaining
            bereave_rem = balances.bereavement_eligible_days
            carers_rem = balances.carers_eligible_days
            toil_rem = balances.toil_balance_days

        l_type = leave_type_str.lower()
        if "vacation" in l_type or "annual" in l_type:
            if requested_days > vac_rem:
                return (
                    False,
                    f"Insufficient Vacation Balance: Requested {requested_days} days, but only {vac_rem} days remaining.",
                )
        elif "sick" in l_type:
            if requested_days > sick_rem:
                return (
                    False,
                    f"Insufficient Sick Leave: Requested {requested_days} days, but only {sick_rem} days remaining.",
                )
        elif "bereavement" in l_type:
            if requested_days > bereave_rem:
                return (
                    False,
                    f"Bereavement policy allows up to {bereave_rem} days per qualifying event (requested {requested_days} days).",
                )
        elif "carer" in l_type:
            if requested_days > carers_rem:
                return (
                    False,
                    f"Carer's leave policy allows up to {carers_rem} days per calendar year (requested {requested_days} days).",
                )
        elif "toil" in l_type:
            if requested_days > toil_rem:
                return (
                    False,
                    f"Insufficient TOIL Balance: Requested {requested_days} days, but only {toil_rem} days accrued.",
                )

        return True, "Leave balance verified."


workweek_guard = WorkWeekGuardrail()
