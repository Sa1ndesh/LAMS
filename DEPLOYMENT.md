# National Land Acquisition & Management System (LAMS) - Production Deployment Guide

This guide provides comprehensive instructions for deploying LAMS in a secure, containerized production environment using Docker, PostgreSQL/PostGIS, FastAPI, and Nginx.

---

## 1. Prerequisites & System Requirements

- **Operating System:** Linux (Ubuntu 22.04 LTS / RHEL 9 recommended) or Windows Server with WSL2
- **Hardware Minimum:** 4 vCPUs, 8 GB RAM, 50 GB SSD storage
- **Software Dependencies:**
  - Docker Engine `v24.0+`
  - Docker Compose `v2.20+`
  - Git `v2.40+`

---

## 2. Environment Configuration & Secret Setup

1. **Clone Repository & Navigate to Workspace:**
   ```bash
   git clone https://github.com/Sa1ndesh/quickcart.git lams-system
   cd lams-system
   ```

2. **Generate Cryptographic Secrets:**
   Generate a strong random 32-byte JWT secret key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Create Production `.env` File:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and populate production parameters:
   ```env
   APPLICATION_ENV=production
   DEBUG=false
   LOG_LEVEL=INFO

   POSTGRES_DB=lams
   POSTGRES_USER=lams_admin
   POSTGRES_PASSWORD=<YOUR_STRONG_DB_PASSWORD>
   POSTGRES_HOST=database
   POSTGRES_PORT=5432

   JWT_SECRET_KEY=<YOUR_GENERATED_JWT_SECRET>
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60

   CORS_ORIGINS=https://lams.gov.in,http://localhost:80

   LAMS_STORAGE_PATH=/app/storage
   VITE_API_BASE_URL=https://lams.gov.in
   ```

---

## 3. Docker Compose Build & Startup Procedure

1. **Validate Docker Compose File Syntax:**
   ```bash
   docker compose config
   ```

2. **Build Production Container Images:**
   ```bash
   docker compose build --no-cache
   ```

3. **Start Container Cluster in Detached Mode:**
   ```bash
   docker compose up -d
   ```

4. **Verify Container Health & Readiness:**
   ```bash
   docker compose ps
   ```
   *Expected output:*
   - `lams_database`: `healthy` (Port 5432)
   - `lams_backend`: `healthy` (Port 8000)
   - `lams_frontend`: `running` / `healthy` (Port 80)

---

## 4. Database Migrations & Seed Execution

1. **Run Database Schema Migrations (Alembic):**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. **Verify Migration Status:**
   ```bash
   docker compose exec backend alembic current
   ```
   *Expected output:* `004_document_management (head)`

3. **Verify PostGIS Extension & Spatial Indexes:**
   ```bash
   docker compose exec database psql -U lams_admin -d lams -c "SELECT PostGIS_Version();"
   docker compose exec database psql -U lams_admin -d lams -c "\d land_parcels"
   ```

4. **Demo Seeding (Development Environments Only):**
   > [!CAUTION]
   > **DO NOT** run demo seed scripts against production database instances containing live acquisition records.
   ```bash
   # Development demo seeding only:
   docker compose exec backend python scripts/seed_data.py
   ```

---

## 5. Reverse Proxy & HTTPS Setup (Nginx + Certbot)

For Internet-facing production deployments, place an Nginx / HAProxy reverse proxy in front of Docker containers to handle HTTPS (TLS 1.3) termination:

```nginx
# Example /etc/nginx/sites-available/lams.conf
server {
    listen 80;
    server_name lams.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lams.gov.in;

    ssl_certificate /etc/letsencrypt/live/lams.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lams.gov.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Route Frontend Static SPA
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Route Backend REST API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 6. Database Backup & Disaster Recovery Procedures

1. **Automated Daily Logical Database Backup:**
   ```bash
   docker compose exec -T database pg_dump -U lams_admin -F c -b -v -f /tmp/lams_backup_$(date +%Y%m%d).dump lams
   docker cp lams_database:/tmp/lams_backup_$(date +%Y%m%d).dump ./backups/
   ```

2. **Restore Database from Backup Dump:**
   ```bash
   docker cp ./backups/lams_backup_20260823.dump lams_database:/tmp/restore.dump
   docker compose exec -T database pg_restore -U lams_admin -d lams -v --clean --if-exists /tmp/restore.dump
   ```

3. **Persistent Volume Backup (Document Storage):**
   ```bash
   tar -cvzf ./backups/lams_documents_$(date +%Y%m%d).tar.gz -C ./backend storage/
   ```

---

## 7. Container Lifecycle Management & Troubleshooting

- **View Live Logs:**
  ```bash
  docker compose logs -f --tail=100 backend
  docker compose logs -f --tail=100 database
  ```

- **Restart Specific Service:**
  ```bash
  docker compose restart backend
  ```

- **Graceful Shutdown (Preserves Volumes):**
  ```bash
  docker compose down
  ```

- **Container Health Endpoint Checks:**
  - Health: `curl http://localhost:8000/api/health`
  - Readiness: `curl http://localhost:8000/api/ready`

