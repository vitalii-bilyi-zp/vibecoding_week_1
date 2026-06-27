import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from app import db
from app.models import BoardData

STATIC_DIR = Path(__file__).parent / "static"


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "hello world"}


@api.get("/board")
def get_board(conn=Depends(get_conn)) -> BoardData:
    board_id = db.get_board_id_for_user(conn)
    return db.read_board(conn, board_id)


@api.put("/board")
def put_board(board: BoardData, conn=Depends(get_conn)) -> BoardData:
    board_id = db.get_board_id_for_user(conn)
    db.save_board(conn, board_id, board)
    return db.read_board(conn, board_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Project Management API", lifespan=lifespan)
app.include_router(api)

# Serve the static site at /. API routes are registered first, so they take
# precedence over this catch-all mount. In the Docker image this directory holds
# the exported Next.js build.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
