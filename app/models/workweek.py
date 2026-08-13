"""WorkWeek HCM Data Models."""

from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field


class LeaveType(str, Enum):
    VACATION = "Vacation"
    SICK = "Sick"
    BEREAVEMENT = "Bereavement"
    CARERS = "Carers"
    MATERNITY = "Maternity"
    TOIL = "TOIL"
    UNPAID = "Unpaid"


class LeaveStatus(str, Enum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    PENDING_APPROVAL = "Pending_Approval"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class LeaveBalance(BaseModel):
    employee_id: str
    vacation_accrued: float = 16.0  # in days or hours
    vacation_used: float = 0.0
    vacation_remaining: float = 16.0
    sick_accrued: float = 14.0
    sick_used: float = 0.0
    sick_remaining: float = 14.0
    bereavement_eligible_days: int = 5
    carers_eligible_days: int = 5
    toil_balance_days: float = 2.0


class LeaveRequest(BaseModel):
    request_id: str
    employee_id: str
    leave_type: LeaveType
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    requested_days: float
    notes: str = ""
    status: LeaveStatus = LeaveStatus.SUBMITTED
    submitted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ContactUpdate(BaseModel):
    employee_id: str
    phone: str | None = None
    address: str | None = None
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class EmployeeProfile(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    role: str
    work_location_type: str = "Remote"  # Remote, Hybrid, OnSite
    office_location: str = "Singapore"
    manager_id: str = "E1001"
    manager_name: str = "Jane Doe"
    hire_date: str = "2023-01-15"
    phone: str = "+65 9123 4567"
    address: str = "123 Tech Way, Austin TX"
    balances: LeaveBalance | None = None
