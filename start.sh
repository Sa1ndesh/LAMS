#!/usr/bin/env bash
set -e

echo "Starting National Land Acquisition & Management System (LAMS)..."
cd backend
python3 -m alembic upgrade head || true
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
