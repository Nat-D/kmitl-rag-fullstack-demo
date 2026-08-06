# Multi-stage: (1) build the Svelte SPA with Node, (2) run FastAPI with Python
# and serve the built SPA as static files. Result: one image, one URL (:8000).

# ---- stage 1: build the frontend ----
FROM node:22-bookworm-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build          # -> /fe/build (adapter-static SPA)

# ---- stage 2: python runtime ----
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

# Install deps first (cached unless pyproject changes).
COPY backend/pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# App code + migrations.
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

# Built SPA from stage 1 (served by app.main when STATIC_DIR exists).
COPY --from=frontend /fe/build ./frontend_build
ENV STATIC_DIR=/app/frontend_build

EXPOSE 8000
# entrypoint waits for the DB, runs migrations, then starts uvicorn.
CMD ["./entrypoint.sh"]
