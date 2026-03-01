from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database import engine, SessionLocal
import models
from auth import hash_password
from routers import auth_router, attendance_router, leave_router, admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed super admin on startup."""
    models.Base.metadata.create_all(bind=engine)
    seed_super_admin()
    yield


def seed_super_admin():
    """Create default super admin if no users exist."""
    db = SessionLocal()
    try:
        exists = db.query(models.User).first()
        if not exists:
            admin = models.User(
                name="Super Admin",
                email=os.getenv("ADMIN_EMAIL", "admin@company.com"),
                password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "Admin@123")),
                role=models.UserRole.super_admin,
                department="IT",
                employee_id="EMP-001",
            )
            # Default company settings
            settings = models.CompanySettings(
                company_name=os.getenv("COMPANY_NAME", "My Company"),
                check_in_start="08:00",
                check_in_end="10:00",
                check_out_start="17:00",
                check_out_end="20:00",
                enforce_ip=False,
            )
            db.add(admin)
            db.add(settings)
            db.commit()
            print("✅ Super Admin created:", os.getenv("ADMIN_EMAIL", "admin@company.com"))
    finally:
        db.close()


app = FastAPI(
    title="Attendance Management System",
    description="Employee attendance tracking with role-based access control",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(attendance_router.router)
app.include_router(leave_router.router)
app.include_router(admin_router.router)


@app.get("/health")
def health():
    return {"status": "ok", "message": "Attendance System is running"}


@app.get("/")
def root():
    return {
        "message": "Welcome to Attendance Management System API",
        "docs": "/docs",
        "redoc": "/redoc",
    }
