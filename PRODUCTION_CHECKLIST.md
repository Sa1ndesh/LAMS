# National Land Acquisition & Management System (LAMS) - Production Readiness Checklist

This document tracks all required security, database, application, and operational verification items prior to launching LAMS into production.

---

## 1. Security Checklist

- [x] **Production JWT Secret Configured:** `JWT_SECRET_KEY` set via environment variable using cryptographically secure 32+ byte random string.
- [x] **Database Passwords Secured:** Default passwords replaced with strong random credentials in `.env`.
- [x] **Secret Exclusion:** `.env` and `.env.*` listed in root `.gitignore`. Zero hardcoded secrets committed to source control.
- [x] **CORS Origin Scoping:** `CORS_ORIGINS` configured with specific domain allowlist rather than wildcard `*`.
- [x] **Security Headers Active:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` enforced.
- [x] **Database Isolation:** PostgreSQL port binding isolated to internal Docker network or firewall-restricted interface.
- [x] **RBAC Enforcement:** All 8 roles verified. `VIEWER` mutation endpoints return `403 Forbidden`.
- [x] **IDOR / BOLA Boundary Checks:** Regional authority state/district spatial scoping verified via `check_project_access_scope`.
- [x] **HTTPS Termination:** Reverse proxy HTTPS deployment pattern documented with TLS 1.3 requirement.

---

## 2. Database & PostGIS Checklist

- [x] **PostgreSQL Version:** PostgreSQL 16/18 container image configured.
- [x] **PostGIS Extension:** PostGIS 3.4/3.6 extension active and verified.
- [x] **Spatial Indexing:** GIST index `idx_land_parcels_geometry` created on `land_parcels.geometry`.
- [x] **Alembic Migrations:** Alembic current == heads (`004_document_management`).
- [x] **Persistent Database Volume:** `postgres_data` volume configured in `docker-compose.yml`.
- [x] **Backup Strategy:** `pg_dump` logical backup and restore procedures validated and documented.

---

## 3. Application & Service Checklist

- [x] **Backend Dockerfile:** Python 3.11 slim image built with non-root application user (`lamsuser`).
- [x] **Production ASGI Server:** Uvicorn configured with multi-worker process mode without `--reload`.
- [x] **Frontend Dockerfile:** Multi-stage build (Node 20 builder → Nginx alpine runner).
- [x] **Frontend Code Splitting:** `React.lazy()` and `Suspense` route-level dynamic imports implemented.
- [x] **Dynamic API Configuration:** Frontend API client uses `VITE_API_BASE_URL` environment variable.
- [x] **Health & Readiness Endpoints:** `/api/health` and `/api/ready` endpoints operational.
- [x] **Document Storage Persistence:** Document directory mounted to persistent volume (`lams_storage`).

---

## 4. Operations & Monitoring Checklist

- [x] **Docker Compose Configuration:** `docker-compose.yml` validated via `docker compose config`.
- [x] **Service Dependencies:** `depends_on` with `service_healthy` conditions configured.
- [x] **Container Health Checks:** Healthcheck directives specified for `database`, `backend`, and `frontend`.
- [x] **Restart Policies:** `restart: unless-stopped` specified across all production services.
- [x] **Automated Test Suite:** 69 backend pytest suite tests passing 100%.
- [x] **TypeScript Build:** `npm run build` succeeds with 0 compilation errors.

