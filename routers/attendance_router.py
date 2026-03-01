from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional

import models
import schemas
from database import get_db
from auth import get_current_user, require_admin

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def get_client_ip(request: Request) -> str:
    """Extract real client IP, considering proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def validate_ip(ip: str, db: Session) -> bool:
    """Check if IP matches allowed company IPs."""
    settings = db.query(models.CompanySettings).first()
    if not settings or not settings.enforce_ip:
        return True  # IP check disabled
    if not settings.allowed_ips:
        return True
    allowed = [i.strip() for i in settings.allowed_ips.split(",")]
    return ip in allowed


# ─── Employee: Check In ───────────────────────────────────────────────────────
@router.post("/check-in", response_model=schemas.AttendanceResponse)
def check_in(
    payload: schemas.CheckInRequest,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    ip = get_client_ip(request)

    # IP validation
    if not validate_ip(ip, db):
        raise HTTPException(
            status_code=403,
            detail="Check-in is only allowed from the company network",
        )

    # Check if already checked in today
    existing = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.user_id == current_user.id,
            models.Attendance.date == today,
        )
        .first()
    )
    if existing and existing.check_in_time:
        raise HTTPException(status_code=400, detail="Already checked in today")

    now = datetime.utcnow()
    settings = db.query(models.CompanySettings).first()
    status_label = "present"

    # Determine if late
    if settings:
        from datetime import time
        late_cutoff = datetime.strptime(settings.check_in_end, "%H:%M").time()
        if now.time() > late_cutoff:
            status_label = "late"

    if existing:
        existing.check_in_time = now
        existing.ip_address = ip
        existing.status = status_label
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    record = models.Attendance(
        user_id=current_user.id,
        date=today,
        check_in_time=now,
        ip_address=ip,
        status=status_label,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ─── Employee: Check Out ──────────────────────────────────────────────────────
@router.post("/check-out", response_model=schemas.AttendanceResponse)
def check_out(
    payload: schemas.CheckOutRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    record = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.user_id == current_user.id,
            models.Attendance.date == today,
        )
        .first()
    )
    if not record or not record.check_in_time:
        raise HTTPException(status_code=400, detail="You have not checked in today")
    if record.check_out_time:
        raise HTTPException(status_code=400, detail="Already checked out today")

    record.check_out_time = datetime.utcnow()
    if payload.notes:
        record.notes = payload.notes
    db.commit()
    db.refresh(record)
    return record


# ─── Employee: My Attendance ──────────────────────────────────────────────────
@router.get("/me", response_model=List[schemas.AttendanceResponse])
def my_attendance(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Attendance).filter(
        models.Attendance.user_id == current_user.id
    )
    if month and year:
        from sqlalchemy import extract
        query = query.filter(
            extract("month", models.Attendance.date) == month,
            extract("year", models.Attendance.date) == year,
        )
    return query.order_by(models.Attendance.date.desc()).all()


@router.get("/today", response_model=Optional[schemas.AttendanceResponse])
def today_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.user_id == current_user.id,
            models.Attendance.date == date.today(),
        )
        .first()
    )
    return record


@router.get("/my-stats", response_model=schemas.MyStats)
def my_stats(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import extract
    now = datetime.utcnow()
    m = month or now.month
    y = year or now.year

    records = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.user_id == current_user.id,
            extract("month", models.Attendance.date) == m,
            extract("year", models.Attendance.date) == y,
        )
        .all()
    )
    present = sum(1 for r in records if r.status in ("present", "late"))
    absent = sum(1 for r in records if r.status == "absent")

    pending_leaves = (
        db.query(models.LeaveRequest)
        .filter(
            models.LeaveRequest.user_id == current_user.id,
            models.LeaveRequest.status == models.LeaveStatus.pending,
        )
        .count()
    )
    approved_leaves = (
        db.query(models.LeaveRequest)
        .filter(
            models.LeaveRequest.user_id == current_user.id,
            models.LeaveRequest.status == models.LeaveStatus.approved,
            extract("month", models.LeaveRequest.from_date) == m,
            extract("year", models.LeaveRequest.from_date) == y,
        )
        .count()
    )
    return schemas.MyStats(
        total_present=present,
        total_absent=absent,
        total_leaves_taken=approved_leaves,
        pending_leaves=pending_leaves,
    )


# ─── Admin: All Attendance ────────────────────────────────────────────────────
@router.get("/all", response_model=List[schemas.AttendanceWithUser])
def all_attendance(
    target_date: Optional[date] = None,
    user_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import extract
    query = db.query(models.Attendance)
    if target_date:
        query = query.filter(models.Attendance.date == target_date)
    if user_id:
        query = query.filter(models.Attendance.user_id == user_id)
    if month and year:
        query = query.filter(
            extract("month", models.Attendance.date) == month,
            extract("year", models.Attendance.date) == year,
        )
    return query.order_by(models.Attendance.date.desc()).all()


@router.get("/dashboard-stats", response_model=schemas.DashboardStats)
def dashboard_stats(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    today = date.today()
    total_employees = db.query(models.User).filter(
        models.User.role == models.UserRole.employee,
        models.User.is_active == True,
    ).count()

    present_today = db.query(models.Attendance).filter(
        models.Attendance.date == today,
        models.Attendance.check_in_time.isnot(None),
    ).count()

    pending_leaves = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.status == models.LeaveStatus.pending
    ).count()

    # Employees on approved leave today
    on_leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.status == models.LeaveStatus.approved,
        models.LeaveRequest.from_date <= today,
        models.LeaveRequest.to_date >= today,
    ).count()

    absent_today = total_employees - present_today - on_leave

    return schemas.DashboardStats(
        total_employees=total_employees,
        present_today=present_today,
        absent_today=max(absent_today, 0),
        pending_leaves=pending_leaves,
        on_leave_today=on_leave,
    )


@router.get("/export/csv")
def export_csv(
    month: int,
    year: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export attendance as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    from sqlalchemy import extract

    records = (
        db.query(models.Attendance)
        .filter(
            extract("month", models.Attendance.date) == month,
            extract("year", models.Attendance.date) == year,
        )
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Employee ID", "Name", "Check-In", "Check-Out", "Status", "IP Address"])

    for r in records:
        writer.writerow([
            r.date,
            r.user.employee_id or "-",
            r.user.name,
            r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "-",
            r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "-",
            r.status,
            r.ip_address or "-",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{year}_{month:02d}.csv"},
    )
