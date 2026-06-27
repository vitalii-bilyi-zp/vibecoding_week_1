# Backend

FastAPI app served by uvicorn, dependencies managed by `uv`. Packaged into a Docker
container that also serves the statically-exported Next.js frontend at `/`.

## Layout

```
backend/
  app/
    __init__.py
    main.py          FastAPI app: API routes + static mount + lifespan (init_db)
    db.py            sqlite3 access: schema, connection, seed, read/save board
    models.py        Pydantic Card/Column/BoardData (mirrors the frontend shape)
    ai.py            OpenRouter client (openai SDK): get_model / ask(prompt)
    static/
      index.html     Placeholder page for local dev; in the Docker image this dir is
                     replaced by the Next.js export (so / serves the Kanban board)
  tests/
    test_health.py   pytest: /api/health, /api/hello, and / serve correctly
    test_board.py    pytest: board seed, db auto-create, read/write, move, rename,
                     persistence across restart, invalid PUT rejection
    test_ai.py       pytest: /api/ai/check (mocked), error handling, and a live
                     OpenRouter test gated behind RUN_LIVE_AI
  pyproject.toml     Project + dependencies (managed by uv)
  uv.lock            Locked dependency versions
  Dockerfile         Multi-stage: Node builds the frontend export, Python runtime serves it
```

The Dockerfile's build context is the repo root (`docker-compose.yml` sets
`context: .`, `dockerfile: backend/Dockerfile`) so it can build `frontend/` and copy the
export into `app/static`. The repo-root `.dockerignore` trims the build context.

## API

- `GET /api/health` -> `{"status": "ok"}`
- `GET /api/hello` -> `{"message": "hello world"}`
- `GET /api/board` -> the user's board as `BoardData` (seeds 5 empty columns if none exists)
- `PUT /api/board` -> full-replace the board from a `BoardData` body; returns the saved board
- `GET /api/ai/check` -> connectivity probe; asks the model "2+2" and returns `{model, answer}`
- `GET /` -> static `index.html`

API routes are registered before the `/` static mount, so they take precedence over the
catch-all static handler.

## Database

SQLite via stdlib `sqlite3` (no ORM). Schema and access live in `app/db.py`; see
`docs/DATABASE.md` for the design. The file path comes from `DATABASE_PATH` (default
`./data/kanban.db`, relative to the working directory) and is created on demand; tables are
created in the app lifespan via `init_db()`. A fresh connection is opened per request
(`get_conn` dependency) with `PRAGMA foreign_keys = ON`. The MVP uses a single hardcoded user
(`user`); writes are full-replace inside a transaction. Tests point `DATABASE_PATH` at a temp
file per test.

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

## AI (OpenRouter)

`app/ai.py` talks to OpenRouter via the `openai` SDK (OpenRouter is OpenAI-compatible),
using `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` (default `openai/gpt-oss-120b:free`) from
the environment. `ask(prompt)` sends a single message and returns the text reply; a missing
key raises a clear `RuntimeError` (surfaced as HTTP 500 by `/api/ai/check`). Tests mock
`ai.ask`; the live test runs only when `RUN_LIVE_AI` is set.

## Conventions

- Config/secrets come from the repo-root `.env` (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`,
  `DATABASE_PATH`). Never hardcode secrets.
- Keep it simple; no over-engineering.
