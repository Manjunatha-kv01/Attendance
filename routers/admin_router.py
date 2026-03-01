from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from auth import require_admin, require_super_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── User Management ──────────────────────────────────────────────────────────
@router.post("/users", response_model=schemas.UserResponse)
def create_user(
    payload: schemas.UserCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Only super admin can create other admins
    if payload.role in (models.UserRole.admin, models.UserRole.super_admin):
        if admin.role != models.UserRole.super_admin:
            raise HTTPException(status_code=403, detail="Only Super Admin can create admin accounts")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department=payload.department,
        employee_id=payload.employee_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=List[schemas.UserResponse])
def list_users(
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: int,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": f"User {user.name} deactivated"}


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    new_password: str,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "Password reset successfully"}


# ─── Company Settings ─────────────────────────────────────────────────────────
@router.get("/settings", response_model=schemas.CompanySettingsResponse)
def get_settings(
    _: models.User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    settings = db.query(models.CompanySettings).first()
    if not settings:
        settings = models.CompanySettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.patch("/settings", response_model=schemas.CompanySettingsResponse)
def update_settings(
    payload: schemas.CompanySettingsUpdate,
    _: models.User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    settings = db.query(models.CompanySettings).first()
    if not settings:
        settings = models.CompanySettings()
        db.add(settings)

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings
