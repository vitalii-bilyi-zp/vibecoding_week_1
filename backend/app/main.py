import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import ai, db
from app.models import BoardData, ChatRequest, ChatResult, ai_to_board

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


@api.get("/ai/check")
def ai_check() -> dict[str, str]:
    """Connectivity probe: ask the model a trivial question (2+2)."""
    try:
        answer = ai.ask("What is 2+2? Reply with just the number.")
    except RuntimeError as error:  # missing/invalid configuration
        raise HTTPException(status_code=500, detail=str(error))
    except Exception as error:  # upstream/network failure
        raise HTTPException(status_code=502, detail=f"AI request failed: {error}")
    return {"model": ai.get_model(), "answer": answer}


@api.post("/chat")
def chat(request: ChatRequest, conn=Depends(get_conn)) -> ChatResult:
    """Send the board + history + message to the AI. If it returns a board
    update, validate and persist it; otherwise leave the board unchanged."""
    board_id = db.get_board_id_for_user(conn)
    board = BoardData.model_validate(db.read_board(conn, board_id))

    try:
        response = ai.chat_with_board(request.message, request.history, board)
    except RuntimeError as error:  # missing/invalid configuration
        raise HTTPException(status_code=500, detail=str(error))
    except Exception as error:  # upstream failure or malformed response
        raise HTTPException(status_code=502, detail=f"AI request failed: {error}")

    board_changed = False
    if response.board_update is not None:
        db.save_board(conn, board_id, ai_to_board(response.board_update))
        board_changed = True

    return ChatResult(reply=response.reply, board_changed=board_changed)


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
