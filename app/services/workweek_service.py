"""WorkWeek HCM Mock Sandbox Service & In-Memory Database."""

import uuid
from datetime import datetime
from ..models.workweek import (
    EmployeeProfile,
    LeaveBalance,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    ContactUpdate,
)


class WorkWeekService:
    """Simulates WorkWeek HCM REST API with stateful operations."""

    def __init__(self):
        self._employees: dict[str, EmployeeProfile] = {}
        self._leave_requests: list[LeaveRequest] = []
        self._seed_default_data()

    def _seed_default_data(self):
        """Seed realistic enterprise employee records."""
        # Main test persona: E1209 (Remote Knowledge Worker)
        e1209 = EmployeeProfile(
            employee_id="E1209",
            name="Alex Chen",
            email="alex.chen@altostrat.com",
            department="Engineering",
            role="Senior Software Engineer",
            work_location_type="Remote",
            office_location="Singapore",
            manager_id="E1001",
            manager_name="Sarah Jenkins",
            hire_date="2022-03-15",
            phone="+65 9123 4567",
            address="123 Tech Way, Austin TX",
            balances=LeaveBalance(
                employee_id="E1209",
                vacation_accrued=16.0,
                vacation_used=0.0,
                vacation_remaining=16.0,
                sick_accrued=14.0,
                sick_used=0.0,
                sick_remaining=14.0,
                bereavement_eligible_days=5,
                carers_eligible_days=5,
                toil_balance_days=2.0,
            ),
        )

        # Persona 2: E1042 (Frontline Hourly / OnSite Employee)
        e1042 = EmployeeProfile(
            employee_id="E1042",
            name="David Kumar",
            email="david.kumar@altostrat.com",
            department="Logistics",
            role="Warehouse Operations Associate",
            work_location_type="OnSite",
            office_location="Singapore",
            manager_id="E1002",
            manager_name="Robert Tan",
            hire_date="2023-06-01",
            phone="+65 8234 5678",
            address="45 Jurong Port Rd, Singapore",
            balances=LeaveBalance(
                employee_id="E1042",
                vacation_accrued=14.0,
                vacation_used=6.0,
                vacation_remaining=8.0,
                sick_accrued=14.0,
                sick_used=2.0,
                sick_remaining=12.0,
                bereavement_eligible_days=5,
                carers_eligible_days=5,
                toil_balance_days=0.0,
            ),
        )

        # Persona 3: E1001 (Manager)
        e1001 = EmployeeProfile(
            employee_id="E1001",
            name="Sarah Jenkins",
            email="sarah.jenkins@altostrat.com",
            department="Engineering",
            role="Engineering Director",
            work_location_type="Hybrid",
            office_location="Singapore",
            manager_id="E0900",
            manager_name="Michael Scott",
            hire_date="2020-01-10",
            phone="+65 9988 7766",
            address="88 Orchard Road, Singapore",
            balances=LeaveBalance(
                employee_id="E1001",
                vacation_accrued=21.0,
                vacation_used=5.0,
                vacation_remaining=16.0,
                sick_accrued=14.0,
                sick_used=1.0,
                sick_remaining=13.0,
                bereavement_eligible_days=5,
                carers_eligible_days=5,
                toil_balance_days=4.0,
            ),
        )

        self._employees["E1209"] = e1209
        self._employees["E1042"] = e1042
        self._employees["E1001"] = e1001

    def get_profile(self, employee_id: str) -> EmployeeProfile | None:
        """Fetch employee profile."""
        return self._employees.get(employee_id)

    def get_leave_balances(self, employee_id: str) -> LeaveBalance | None:
        """Fetch leave balances for employee."""
        emp = self._employees.get(employee_id)
        if emp:
            return emp.balances
        return None

    def submit_leave_request(
        self,
        employee_id: str,
        leave_type: LeaveType | str,
        start_date: str,
        end_date: str,
        requested_days: float,
        notes: str = "",
    ) -> LeaveRequest:
        """Submit a leave request and deduct temporary pending balance."""
        emp = self._employees.get(employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found in WorkWeek database.")

        if isinstance(leave_type, str):
            try:
                leave_type = LeaveType(leave_type.capitalize())
            except ValueError:
                leave_type = LeaveType.VACATION

        # Deduct balance if approved/submitted
        if emp.balances:
            if leave_type == LeaveType.VACATION:
                emp.balances.vacation_remaining = max(
                    0.0, emp.balances.vacation_remaining - requested_days
                )
                emp.balances.vacation_used += requested_days
            elif leave_type == LeaveType.SICK:
                emp.balances.sick_remaining = max(
                    0.0, emp.balances.sick_remaining - requested_days
                )
                emp.balances.sick_used += requested_days

        req_id = f"LV-{uuid.uuid4().hex[:6].upper()}"
        leave_req = LeaveRequest(
            request_id=req_id,
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            requested_days=requested_days,
            notes=notes,
            status=LeaveStatus.SUBMITTED,
            submitted_at=datetime.utcnow().isoformat() + "Z",
        )
        self._leave_requests.append(leave_req)
        return leave_req

    def update_contact_info(
        self, employee_id: str, phone: str | None = None, address: str | None = None
    ) -> ContactUpdate:
        """Update contact phone or address in HCM profile."""
        emp = self._employees.get(employee_id)
        if not emp:
            raise ValueError(f"Employee {employee_id} not found in WorkWeek database.")

        if phone:
            emp.phone = phone
        if address:
            emp.address = address

        return ContactUpdate(
            employee_id=employee_id,
            phone=emp.phone,
            address=emp.address,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )

    def list_employee_leave_requests(self, employee_id: str) -> list[LeaveRequest]:
        """List all leave requests filed by an employee."""
        return [r for r in self._leave_requests if r.employee_id == employee_id]


workweek_db = WorkWeekService()
