#!/bin/sh
# Bring the schema up to date, then serve. `alembic upgrade head` is idempotent,
# so it's safe to run on every start. The DB is already healthy because
# docker-compose waits on its healthcheck (depends_on: condition: service_healthy).
set -e

echo "[entrypoint] running migrations…"
alembic upgrade head

echo "[entrypoint] starting uvicorn on :8000…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
