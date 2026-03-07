#!/bin/sh
set -e

echo "[entrypoint] Running Alembic migrations..."
alembic -c backend/alembic.ini upgrade head
echo "[entrypoint] Migrations complete."

echo "[entrypoint] Starting application..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
