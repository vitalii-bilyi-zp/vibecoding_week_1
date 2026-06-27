from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"

api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "hello world"}


app = FastAPI(title="Project Management API")
app.include_router(api)

# Serve the static site at /. API routes are registered first, so they take
# precedence over this catch-all mount. In Part 3 this directory is replaced by
# the exported Next.js build.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
