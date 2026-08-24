# National Land Acquisition & Management System (LAMS)

![LAMS Architecture](https://img.shields.io/badge/Stack-React_18_%7C_FastAPI_%7C_PostgreSQL_18_%7C_PostGIS_3.6-blue)
![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![Tests](https://img.shields.io/badge/Tests-69_Passed-success)
![Security Audit](https://img.shields.io/badge/Security_Audit-Passed-blue)

The **National Land Acquisition & Management System (LAMS)** is a digital platform designed for monitoring, managing, and streamlining land acquisition lifecycles across national infrastructure corridors in India.

---

## 🚀 Key System Features

- **9-Stage Sequential Lifecycle Engine:** `Proposal` → `Verification` → `Survey` → `Notification` → `Award` → `Compensation` → `Possession` → `Rehabilitation & Resettlement` → `Completed`.
- **GIS & Spatial Mapping:** PostGIS 3.6 spatial polygon storage (`geometry(Polygon, 4326)`), GIST spatial index (`idx_land_parcels_geometry`), interactive Leaflet map, coordinate inspector drawer.
- **8-Role RBAC Matrix:** Enforces administrative role access control across `SUPER_ADMIN`, `CENTRAL_MINISTRY`, `STATE_AUTHORITY`, `DISTRICT_ADMIN`, `LAND_ACQUISITION_OFFICER`, `FIELD_OFFICER`, `PROJECT_IMPLEMENTING_AGENCY`, and `VIEWER`.
- **Secure Document Management:** Category-based project document upload/storage (`PROPOSAL`, `LAND_RECORDS`, `SURVEY`, `NOTIFICATIONS`, `AWARD`, `COMPENSATION`, `RR`), path-traversal validation, UUID storage filenames, audit logging.
- **Production SQL Analytics:** Aggregated metrics for state distributions, land acquisition progress, financial treasury disbursement, R&R family status, project timelines, and delay bottleneck tracking.
- **AI Decision Support Engine:** Deterministic, explainable 0–100 risk scoring algorithm across 6 project factor components (`stage_duration`, `land_gap`, `disbursement_gap`, `unresolved_disputes`, `pending_approvals`, `overdue_milestones`).
- **Defensive Application Security:** BOLA/IDOR regional spatial boundary isolation, global HTTP security headers, JWT token validation, `bcrypt` password hashing, parameterized SQL injection prevention.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Leaflet.js, Recharts, Lucide Icons |
| **Backend** | FastAPI, Python 3.11, Async SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 18.6 with PostGIS 3.6 Extension |
| **Migrations** | Alembic (`004_document_management`) |
| **Authentication** | JWT Bearer Tokens, Bcrypt Hashing, 8-Role RBAC Dependencies |
| **Deployment** | Docker, Docker Compose, Nginx, Multi-Stage Container Builds |

---

## 📂 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI REST Endpoints (Projects, GIS, Analytics, AI, etc.)
│   │   ├── core/             # Configuration, Database Engine, Security, Dependencies
│   │   ├── models/           # SQLAlchemy 2.0 ORM Schema Definitions
│   │   ├── schemas/          # Pydantic Input/Output Validation Schemas
│   │   └── services/         # Storage, AI Engine, Workflow Logic
│   ├── alembic/              # Database Migration Scripts
│   ├── tests/                # Automated Pytest Suite (69 Tests)
│   └── Dockerfile            # Production Backend Container Spec
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI Controls, Modals, Navigation
│   │   ├── pages/            # Dashboard, GIS Map, Analytics, AI, Projects
│   │   ├── routes/           # React Router AppRoutes with Lazy Code Splitting
│   │   └── services/         # Centralized API Services & Auth Context
│   ├── nginx.conf            # Production Nginx Web Server Configuration
│   └── Dockerfile            # Multi-stage Frontend Container Spec
├── docker-compose.yml        # Orchestration Manifest (Database, Backend, Frontend)
├── DEPLOYMENT.md             # Production Deployment Instructions & Backup Guide
├── PRODUCTION_CHECKLIST.md   # Deployment Verification Checklist
├── PHASE_14_SECURITY_AUDIT.md# Comprehensive Security Audit Report
├── PHASE_15_PRODUCTION_REPORT.md # Production Readiness Report
└── PROJECT_STATUS.md         # Phase-by-Phase Development Tracker
```

---

## ⚡ Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate    # On Linux/macOS

pip install -r requirements.txt
python -m alembic upgrade head
python -m pytest              # Run backend test suite (69 passed)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run build                 # Run TypeScript check & Vite production build
npm run dev                   # Start Vite development server (http://localhost:5173)
```

---

## 🐳 Containerized Production Deployment (Docker Compose)

Refer to [`DEPLOYMENT.md`](file:///c:/Users/Sande/Desktop/project/DEPLOYMENT.md) for full production deployment guidance:

```bash
# 1. Environment Setup
cp .env.example .env

# 2. Build & Launch Container Cluster
docker compose up -d --build

# 3. Apply Schema Migrations
docker compose exec backend alembic upgrade head
```

---

## 📜 Documentation Links

- **[Government Executive Proposal & Technical Whitepaper (`NATIONAL_LAMS_MASTER_PROPOSAL.md`)](file:///c:/Users/Sande/Desktop/project/NATIONAL_LAMS_MASTER_PROPOSAL.md)**
- [Production Deployment Guide (`DEPLOYMENT.md`)](file:///c:/Users/Sande/Desktop/project/DEPLOYMENT.md)
- [Production Readiness Checklist (`PRODUCTION_CHECKLIST.md`)](file:///c:/Users/Sande/Desktop/project/PRODUCTION_CHECKLIST.md)
- [Security Audit Report (`PHASE_14_SECURITY_AUDIT.md`)](file:///c:/Users/Sande/Desktop/project/PHASE_14_SECURITY_AUDIT.md)
- [Production Preparation Report (`PHASE_15_PRODUCTION_REPORT.md`)](file:///c:/Users/Sande/Desktop/project/PHASE_15_PRODUCTION_REPORT.md)
- [Project Status Tracker (`PROJECT_STATUS.md`)](file:///c:/Users/Sande/Desktop/project/PROJECT_STATUS.md)

