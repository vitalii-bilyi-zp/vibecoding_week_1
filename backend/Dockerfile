# Backend image: FastAPI served by uvicorn, dependencies managed by uv.
# Part 3 will add a frontend build stage; for now this serves the placeholder
# static page plus the example API.
FROM python:3.12-slim

# uv binary
COPY --from=ghcr.io/astral-sh/uv:0.10.3 /uv /uvx /bin/

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first (cached unless lockfile changes).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
