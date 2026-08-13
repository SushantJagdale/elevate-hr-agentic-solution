"""WorkWeek HCM Enterprise Connector."""

import time
import logging
from ..services.workweek_service import workweek_db, WorkWeekService
from ..models.workweek import EmployeeProfile, LeaveBalance, LeaveRequest, ContactUpdate, LeaveType

logger = logging.getLogger("WorkWeekConnector")


class WorkWeekConnector:
    """Enterprise WorkWeek Connector with Secret Manager credentials & Provenance headers."""

    def __init__(self, service: WorkWeekService | None = None):
        self.service = service or workweek_db
        self.origin_agent = "HR-Agentic-MVP"
        self._max_retries = 3

    def _get_headers(self, acting_user_id: str) -> dict[str, str]:
        """Construct secure request headers matching SDD specs."""
        return {
            "Authorization": "Bearer mock_ww_token_sec_mgr_88391",
            "X-Origin-Agent": self.origin_agent,
            "X-Acting-User": acting_user_id,
            "Content-Type": "application/json",
        }

    def get_employee_profile(self, employee_id: str, acting_user_id: str | None = None) -> dict:
        """Fetch employee profile over simulated Private Service Connect (PSC)."""
        acting_user = acting_user_id or employee_id
        start_time = time.time()
        
        # Exponential backoff retry logic
        for attempt in range(self._max_retries):
            try:
                profile = self.service.get_profile(employee_id)
                latency = int((time.time() - start_time) * 1000)
                if not profile:
                    return {
                        "status": "error",
                        "status_code": 404,
                        "error": f"Employee {employee_id} not found",
                        "latency_ms": latency,
                    }
                return {
                    "status": "success",
                    "status_code": 200,
                    "data": profile.model_dump(),
                    "latency_ms": latency,
                }
            except Exception as e:
                if attempt == self._max_retries - 1:
                    return {
                        "status": "error",
                        "status_code": 500,
                        "error": str(e),
                        "latency_ms": int((time.time() - start_time) * 1000),
                    }
                time.sleep(0.05 * (2**attempt))
        return {"status": "error", "status_code": 500, "error": "Unknown error"}

    def get_leave_balances(self, employee_id: str, acting_user_id: str | None = None) -> dict:
        """Fetch accrued, used, and remaining leave balances."""
        acting_user = acting_user_id or employee_id
        start_time = time.time()
        balances = self.service.get_leave_balances(employee_id)
        latency = int((time.time() - start_time) * 1000)
        
        if not balances:
            return {
                "status": "error",
                "status_code": 404,
                "error": f"No balances found for employee {employee_id}",
                "latency_ms": latency,
            }
        return {
            "status": "success",
            "status_code": 200,
            "data": balances.model_dump(),
            "latency_ms": latency,
        }

    def submit_leave_request(
        self,
        employee_id: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        requested_days: float,
        notes: str = "",
        acting_user_id: str | None = None,
    ) -> dict:
        """Submit a formal leave request to WorkWeek HCM."""
        acting_user = acting_user_id or employee_id
        start_time = time.time()
        try:
            req = self.service.submit_leave_request(
                employee_id=employee_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                requested_days=requested_days,
                notes=notes,
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
                "status_code": 400,
                "error": str(e),
                "latency_ms": latency,
            }

    def update_contact_info(
        self,
        employee_id: str,
        phone: str | None = None,
        address: str | None = None,
        acting_user_id: str | None = None,
    ) -> dict:
        """Update employee contact details."""
        acting_user = acting_user_id or employee_id
        start_time = time.time()
        try:
            update_res = self.service.update_contact_info(
                employee_id=employee_id, phone=phone, address=address
            )
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "success",
                "status_code": 200,
                "data": update_res.model_dump(),
                "latency_ms": latency,
            }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "status_code": 400,
                "error": str(e),
                "latency_ms": latency,
            }


workweek_connector = WorkWeekConnector()
