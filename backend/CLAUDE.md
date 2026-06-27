# Backend

FastAPI app served by uvicorn, dependencies managed by `uv`. Packaged into a Docker
container that also serves the static frontend at `/` (the frontend is added in Part 3).

## Layout

```
backend/
  app/
    __init__.py
    main.py          FastAPI app: API routes + static mount
    static/
      index.html     Placeholder page served at / (replaced by the Next.js export in Part 3)
  tests/
    test_health.py   pytest: /api/health, /api/hello, and / serve correctly
  pyproject.toml     Project + dependencies (managed by uv)
  uv.lock            Locked dependency versions
  Dockerfile         Single-stage Python image using uv
  .dockerignore
```

## API

- `GET /api/health` -> `{"status": "ok"}`
- `GET /api/hello` -> `{"message": "hello world"}`
- `GET /` -> static `index.html`

API routes are registered before the `/` static mount, so they take precedence over the
catch-all static handler.

## Develop locally

```bash
cd backend
uv sync              # create .venv and install deps
uv run pytest        # run tests
uv run uvicorn app.main:app --reload   # dev server on :8000
```

## Run in Docker

From the repo root use the scripts (preferred):

```bash
scripts/start.sh     # or scripts\start.ps1 on Windows
scripts/stop.sh      # or scripts\stop.ps1
```

These wrap `docker compose` defined in the repo-root `docker-compose.yml`, which builds this
image, maps port 8000, loads `.env`, and bind-mounts `./data` for the SQLite database (used
from Part 6).

## Conventions

- Config/secrets come from the repo-root `.env` (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`,
  `DATABASE_PATH`). Never hardcode secrets.
- Keep it simple; no over-engineering.
