# Multi-stage build. Stage 1 builds the Next.js static export; stage 2 is the
# Python runtime that serves that export at / alongside the API.
# Build context is the repo root (see docker-compose.yml), so paths below are
# relative to the repo root.

# Stage 1: build the static frontend
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime (uv-managed FastAPI)
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.3 /uv /uvx /bin/

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first (cached unless lockfile changes).
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/app ./app

# Replace the placeholder static page with the built frontend export.
COPY --from=frontend /frontend/out ./app/static

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
