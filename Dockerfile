# =====================================================================
# LAMS Monorepo Production Root Dockerfile (Railway / Cloud Deployment)
# Base: Python 3.11 Slim Production Base
# =====================================================================

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LAMS_STORAGE_PATH=/app/storage

WORKDIR /app

# Install system runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, migrations, and scripts
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .
COPY backend/scripts ./scripts

# Create storage directory for project documents & set permissions
RUN mkdir -p /app/storage && chmod -R 755 /app/storage

# Create non-root application user for container security
RUN adduser --disabled-password --gecos "" lamsuser && \
    chown -R lamsuser:lamsuser /app
USER lamsuser

# Expose FastAPI application port
EXPOSE 8000

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production ASGI server launch
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
