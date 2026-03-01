# AttendX — Attendance Management System

A full-stack attendance tracking system with role-based access control, built with **FastAPI + PostgreSQL + Docker**.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Port 80 and 8000 available

### 1. Clone / set up the project
```bash
cd attendance-system
```

### 2. Start all services
```bash
docker-compose up --build
```

### 3. Access the app
| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| API Docs (Swagger) | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |

### 4. Default Login
| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@company.com | Admin@123 |

> Create employee accounts from the Admin dashboard.

---

## 📁 Project Structure

```
attendance-system/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── database.py           # DB connection and session
│   ├── auth.py               # JWT authentication, password hashing
│   ├── routers/
│   │   ├── auth_router.py    # /auth — login, me, change-password
│   │   ├── attendance_router.py  # /attendance — check-in/out, reports
│   │   ├── leave_router.py   # /leaves — apply, review
│   │   └── admin_router.py   # /admin — user management, settings
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html            # Login page
│   ├── employee.html         # Employee dashboard
│   └── admin.html            # Admin dashboard
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## 👥 Roles & Permissions

### 🔴 Super Admin
- All admin permissions +
- Configure company settings (allowed IPs, check-in times)
- Create/manage admin accounts
- Access settings panel

### 🟠 Admin
- Create employee accounts
- View all attendance records
- Export CSV reports
- Approve/reject leave requests
- Reset employee passwords

### 🔵 Employee
- Check in / Check out
- View personal attendance history
- Apply for leave
- Cancel pending leave requests

---

## 🌐 API Endpoints

### Authentication
```
POST   /auth/login              Login, returns JWT token
GET    /auth/me                 Get current user info
POST   /auth/change-password    Change own password
```

### Attendance
```
POST   /attendance/check-in     Employee check-in
POST   /attendance/check-out    Employee check-out
GET    /attendance/today        Today's attendance record
GET    /attendance/me           My attendance history
GET    /attendance/my-stats     Monthly stats summary
GET    /attendance/all          All attendance (admin)
GET    /attendance/dashboard-stats  Dashboard summary (admin)
GET    /attendance/export/csv   Export CSV report (admin)
```

### Leave Management
```
POST   /leaves/apply            Submit leave request
GET    /leaves/me               My leave requests
DELETE /leaves/{id}             Cancel pending request
GET    /leaves/all              All requests (admin)
PATCH  /leaves/{id}/review      Approve/reject (admin)
```

### Admin
```
GET    /admin/users             List all users
POST   /admin/users             Create user
GET    /admin/users/{id}        Get user
PATCH  /admin/users/{id}        Update user
DELETE /admin/users/{id}        Deactivate user
POST   /admin/users/{id}/reset-password
GET    /admin/settings          Company settings (super admin)
PATCH  /admin/settings          Update settings (super admin)
```

---

## 🏢 WiFi/IP-Based Attendance

### Enable IP Restriction:
1. Login as Super Admin → Settings
2. Add company public IP(s) in "Allowed IPs" field (comma-separated)
3. Toggle "Enforce IP Restriction" ON
4. Save

Employees can now only check in from whitelisted IP addresses.

### Get your public IP:
```bash
curl https://api.ipify.org
```

---

## 🗄️ Database Schema

```
users              → id, name, email, password_hash, role, department, employee_id, is_active
attendance         → id, user_id, date, check_in_time, check_out_time, ip_address, status
leave_requests     → id, user_id, from_date, to_date, leave_type, reason, status, reviewed_by
company_settings   → company_name, allowed_ips, check_in times, enforce_ip
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://... | PostgreSQL connection string |
| SECRET_KEY | change_this | JWT signing key |
| ADMIN_EMAIL | admin@company.com | Initial super admin email |
| ADMIN_PASSWORD | Admin@123 | Initial super admin password |
| COMPANY_NAME | My Company | Company display name |
| TOKEN_EXPIRE_MINUTES | 480 | JWT token validity (8 hours) |

---

## 🛠️ Local Development (without Docker)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL="postgresql://user:pass@localhost:5432/attendance_db"

# Run
uvicorn main:app --reload --port 8000
```

---

## 🔮 Future Enhancements

- [ ] Face recognition check-in
- [ ] QR code attendance
- [ ] GPS/geofence attendance
- [ ] Monthly PDF report generation  
- [ ] Email notifications
- [ ] Slack integration
- [ ] Multi-branch support
- [ ] Biometric device integration
- [ ] Mobile app (React Native)

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Auth | JWT (python-jose) |
| Frontend | HTML + CSS + Vanilla JS |
| Containerization | Docker + Docker Compose |
| Web Server | Nginx |
