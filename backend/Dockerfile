# =====================================================================
# LAMS Backend Production Dockerfile
# Base: Python 3.11 Slim Production Base
# =====================================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files & enable unbuffered logging
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

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code & migrations
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts

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

# Production ASGI server launch (No --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

