from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

import models
import schemas
from database import get_db
from auth import get_current_user, require_admin

router = APIRouter(prefix="/leaves", tags=["Leave Management"])


@router.post("/apply", response_model=schemas.LeaveResponse)
def apply_leave(
    payload: schemas.LeaveCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check for overlapping leaves
    overlap = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.user_id == current_user.id,
        models.LeaveRequest.status != models.LeaveStatus.rejected,
        models.LeaveRequest.from_date <= payload.to_date,
        models.LeaveRequest.to_date >= payload.from_date,
    ).first()
    if overlap:
        raise HTTPException(status_code=400, detail="You already have a leave request for overlapping dates")

    leave = models.LeaveRequest(
        user_id=current_user.id,
        from_date=payload.from_date,
        to_date=payload.to_date,
        leave_type=payload.leave_type,
        reason=payload.reason,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/me", response_model=List[schemas.LeaveResponse])
def my_leaves(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.LeaveRequest)
        .filter(models.LeaveRequest.user_id == current_user.id)
        .order_by(models.LeaveRequest.created_at.desc())
        .all()
    )


@router.delete("/{leave_id}")
def cancel_leave(
    leave_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.id == leave_id,
        models.LeaveRequest.user_id == current_user.id,
    ).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != models.LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    db.delete(leave)
    db.commit()
    return {"message": "Leave request cancelled"}


# ─── Admin ────────────────────────────────────────────────────────────────────
@router.get("/all", response_model=List[schemas.LeaveWithUser])
def all_leaves(
    status: Optional[str] = None,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.LeaveRequest)
    if status:
        query = query.filter(models.LeaveRequest.status == status)
    return query.order_by(models.LeaveRequest.created_at.desc()).all()


@router.patch("/{leave_id}/review", response_model=schemas.LeaveResponse)
def review_leave(
    leave_id: int,
    payload: schemas.LeaveReview,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    leave = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != models.LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="Leave already reviewed")

    leave.status = payload.status
    leave.reviewed_by = admin.id
    leave.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(leave)
    return leave
