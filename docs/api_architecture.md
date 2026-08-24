# National Land Acquisition & Management System (LAMS) - API Architecture

## 1. Overview
The LAMS Backend API is a RESTful service built with **FastAPI** (Python 3.11+). All endpoints validate payloads using Pydantic schemas, enforce JWT authentication, and check Role-Based Access Control (RBAC).

---

## 2. API Endpoints Specification

### 2.1 Authentication (`/api/auth`)
- `POST /api/auth/login`: Authenticates user credentials, returns JWT Bearer token and user profile.
- `POST /api/auth/register`: Registers a new administrative user (SUPER_ADMIN or DISTRICT_ADMIN required).
- `POST /api/auth/refresh`: Refreshes expired access tokens.
- `GET /api/auth/me`: Retrieves current authenticated user profile and permissions.

### 2.2 Projects (`/api/projects`)
- `GET /api/projects`: List projects with search, filter (state, district, stage, status, type), and pagination.
- `POST /api/projects`: Create a new project proposal (Roles: CENTRAL_MINISTRY, STATE_AUTHORITY, DISTRICT_ADMIN, SUPER_ADMIN).
- `GET /api/projects/{id}`: Detailed overview of a specific project including current lifecycle stage.
- `PUT /api/projects/{id}`: Update project metadata, budget, or dates.
- `PUT /api/projects/{id}/stage`: Transition project to next lifecycle stage (logged in audit trail).
- `DELETE /api/projects/{id}`: Soft delete or archive project (SUPER_ADMIN only).

### 2.3 Land Parcels (`/api/parcels`)
- `GET /api/projects/{id}/parcels`: Retrieve list of all land parcels for a project.
- `POST /api/projects/{id}/parcels`: Register a new land parcel with survey details and GeoJSON boundary.
- `GET /api/parcels/{id}`: View detailed parcel record, landowner list, and acquisition status.
- `PUT /api/parcels/{id}`: Update parcel land type, area, or spatial coordinates.
- `PUT /api/parcels/{id}/status`: Advance acquisition/possession status.
- `DELETE /api/parcels/{id}`: Remove parcel record.

### 2.4 Compensation (`/api/compensation`)
- `GET /api/projects/{id}/compensation`: Summarize compensation status across all parcels in a project.
- `POST /api/compensation`: Create an assessment or disbursement record for a parcel.
- `PUT /api/compensation/{id}`: Update compensation status (Assessed -> Approved -> Disbursed).

### 2.5 Affected Families & R&R (`/api/families`)
- `GET /api/projects/{id}/families`: List all registered affected families and R&R status.
- `POST /api/families`: Register an affected/displaced family.
- `PUT /api/families/{id}`: Update family details or R&R eligibility status.
- `PUT /api/families/{id}/package`: Update housing, employment, or cash grant package.

### 2.6 Document Management (`/api/documents`)
- `GET /api/projects/{id}/documents`: List documents linked to a project (with category filters).
- `POST /api/documents`: Upload file (PDF/Word/Images) with metadata tagging.
- `GET /api/documents/{id}/download`: Download document file stream.
- `DELETE /api/documents/{id}`: Remove document (Role check enforced).

### 2.7 Executive Dashboard (`/api/dashboard`)
- `GET /api/dashboard/summary`: High-level metrics (Total Projects, Proposed/Acquired Land, Compensation, Families).
- `GET /api/dashboard/state-progress`: State-wise land acquisition comparison breakdown.
- `GET /api/dashboard/project-status`: Distribution of projects by lifecycle stage and delay status.
- `GET /api/dashboard/compensation`: National compensation disbursement progress.

### 2.8 GIS Spatial Data (`/api/gis`)
- `GET /api/gis/projects`: FeatureCollection GeoJSON of all project center points.
- `GET /api/gis/projects/{id}`: FeatureCollection GeoJSON of project boundary & parcel polygons.
- `GET /api/gis/parcels/{id}`: GeoJSON polygon and metadata for a specific land parcel.

### 2.9 Notifications & Audit (`/api/notifications`, `/api/audit-logs`)
- `GET /api/notifications`: Retrieve user-specific alerts and system notifications.
- `PUT /api/notifications/{id}/read`: Mark notification as read.
- `GET /api/audit-logs`: View system-wide audit logs with filters (SUPER_ADMIN / CENTRAL_MINISTRY).

### 2.10 AI Decision Support (`/api/ai`)
- `GET /api/ai/projects/{id}/delay-risk`: Calculate delay risk score, identifying bottleneck drivers.
- `GET /api/ai/projects/{id}/compensation-bottlenecks`: Predict compensation disbursement friction.

---

## 3. Standard API Response Structure

```json
{
  "success": true,
  "message": "Project retrieved successfully",
  "data": { ... },
  "error": null,
  "timestamp": "2026-08-23T12:18:17Z"
}
```

