from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from models import UserRole, LeaveStatus


# ─────────────── Auth ───────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str


# ─────────────── User ───────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.employee
    department: Optional[str] = None
    employee_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: Optional[str]
    employee_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────── Attendance ───────────────
class CheckInRequest(BaseModel):
    notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    date: date
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    ip_address: Optional[str]
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class AttendanceWithUser(AttendanceResponse):
    user: UserResponse

    class Config:
        from_attributes = True


# ─────────────── Leave ───────────────
class LeaveCreate(BaseModel):
    from_date: date
    to_date: date
    leave_type: str = "casual"
    reason: Optional[str] = None

    @validator("to_date")
    def end_after_start(cls, v, values):
        if "from_date" in values and v < values["from_date"]:
            raise ValueError("to_date must be after from_date")
        return v


class LeaveReview(BaseModel):
    status: LeaveStatus
    

class LeaveResponse(BaseModel):
    id: int
    user_id: int
    from_date: date
    to_date: date
    leave_type: str
    reason: Optional[str]
    status: LeaveStatus
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveWithUser(LeaveResponse):
    user: UserResponse

    class Config:
        from_attributes = True


# ─────────────── Company Settings ───────────────
class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    allowed_ips: Optional[str] = None
    check_in_start: Optional[str] = None
    check_in_end: Optional[str] = None
    check_out_start: Optional[str] = None
    check_out_end: Optional[str] = None
    enforce_ip: Optional[bool] = None


class CompanySettingsResponse(BaseModel):
    id: int
    company_name: str
    allowed_ips: Optional[str]
    check_in_start: str
    check_in_end: str
    check_out_start: str
    check_out_end: str
    enforce_ip: bool

    class Config:
        from_attributes = True


# ─────────────── Dashboard Stats ───────────────
class DashboardStats(BaseModel):
    total_employees: int
    present_today: int
    absent_today: int
    pending_leaves: int
    on_leave_today: int


class MyStats(BaseModel):
    total_present: int
    total_absent: int
    total_leaves_taken: int
    pending_leaves: int
