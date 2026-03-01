from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    employee = "employee"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.employee, nullable=False)
    department = Column(String(100), nullable=True)
    employee_id = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    attendance_records = relationship("Attendance", back_populates="user")
    leave_requests = relationship("LeaveRequest", back_populates="user")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(String(20), default="present")  # present, absent, late, half-day
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="attendance_records")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    leave_type = Column(String(50), default="casual")  # casual, sick, annual
    reason = Column(Text, nullable=True)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.pending)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="leave_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class CompanySettings(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), default="My Company")
    allowed_ips = Column(Text, nullable=True)   # comma-separated IPs
    check_in_start = Column(String(5), default="08:00")   # HH:MM
    check_in_end = Column(String(5), default="10:00")
    check_out_start = Column(String(5), default="17:00")
    check_out_end = Column(String(5), default="20:00")
    enforce_ip = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
