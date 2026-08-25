#!/usr/bin/env bash
set -e

echo "Starting National Land Acquisition & Management System (LAMS)..."
pip install -r backend/requirements.txt
cd backend
python -m alembic upgrade head || true
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
