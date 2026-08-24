# National Land Acquisition & Management System (LAMS) - Technical Architecture

## 1. System Overview
The National Land Acquisition & Management System (LAMS) is a centralized, digital, role-based, GIS-enabled enterprise platform designed for monitoring and managing the end-to-end land acquisition lifecycle for national infrastructure projects across India.

### Core Objectives:
- **Lifecycle Tracking:** 9-stage workflow management from initial proposal to final completion.
- **GIS Integration:** Real-time spatial tracking of projects and land parcel boundary polygons.
- **Role-Based Access Control (RBAC):** Strict security across 8 government user roles.
- **Transparency & Audit:** Immutable audit logging for all lifecycle and financial operations.
- **Decision Support:** Predictive AI risk scoring for project delay and compensation bottlenecks.

---

## 2. Technology Stack

### Frontend Architecture
- **Framework:** React 18+ (TypeScript) built with **Vite**
- **Styling & UI Design:** **Tailwind CSS** following the Stitch Design System (#002046 Primary, #1261A3 Secondary, #F8F9FF Background, #FFFFFF Surface)
- **Routing:** React Router v6
- **Icons:** Lucide React
- **Data Visualization:** Recharts
- **GIS Mapping:** Leaflet.js / React-Leaflet with GeoJSON layers

### Backend Architecture
- **Language & Engine:** Python 3.11+
- **API Framework:** FastAPI with async handlers and Pydantic v2 data validation
- **ASGI Server:** Uvicorn
- **ORM & Database Client:** SQLAlchemy 2.0 (Async Engine)
- **Database Migrations:** Alembic
- **Document Processing:** ReportLab (PDF), python-docx (DOCX)

### Database Architecture
- **Relational Database:** PostgreSQL 15+
- **Spatial Extension:** PostGIS for spatial geometries (Polygons, MultiPolygons, Points, Centroids)

### Authentication & Authorization
- **Token Format:** JWT (JSON Web Tokens) with RSA/HS256 encryption
- **Password Security:** bcrypt hashing (cost factor 12)
- **Authorization:** Fine-grained Role-Based Access Control (RBAC) middleware

---

## 3. System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|                                                                                   |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Executive Dashboard|   | Project Directory   |   | GIS Parcel Explorer      |  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Compensation Portal|   | R&R Family Tracker  |   | Document Repository      |  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|                                                                                   |
|                     React 18 + TypeScript + Tailwind CSS (Vite)                   |
+------------------------------------------+----------------------------------------+
                                           |
                                           | HTTPS / REST APIs (JWT)
                                           v
+-----------------------------------------------------------------------------------+
|                                BACKEND SERVICES                                   |
|                                                                                   |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Auth & Security    |   | Project Lifecycle   |   | GIS & Spatial Engine     |  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Financial/Comp API |   | R&R Tracking Engine |   | Document & Audit Engine  |  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  |                      AI Predictive Analytics Engine                         |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|                              FastAPI + Python 3.11+                               |
+------------------------------------------+----------------------------------------+
                                           |
                                           | SQLAlchemy 2.0 (Async PostGIS)
                                           v
+-----------------------------------------------------------------------------------+
|                                DATA STORAGE LAYER                                 |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                      PostgreSQL 15+ with PostGIS                            |  |
|  |  - Spatial Polygons (Land Parcels)       - Financial Compensation Logs        |  |
|  |  - Project Lifecycle Audit Trails       - Affected Family & R&R Records        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 4. Security & Compliance
1. **Zero Secret Hardcoding:** All database credentials, JWT secrets, and environment configurations loaded from `.env`.
2. **RBAC Guarding:** Every API endpoint validates the token payload against permissible user roles.
3. **Data Anonymization:** Development and demo datasets strictly use fictional Indian names, survey numbers, and coordinates.
4. **Audit Logging:** Every state change, approval, document upload, and status progression creates an immutable entry in `audit_logs`.

